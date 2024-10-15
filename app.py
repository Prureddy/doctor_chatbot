from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import pandas as pd
import openai

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Initialize the OpenAI API
openai.api_key = ''  # Replace with your OpenAI API key

# Define admin credentials
ADMIN_USERS = {
    'admin1': 'password1',
    'admin2': 'password2',
    'admin3': 'password3',
    'admin4': 'password4'
}


# Assign 25 rows to each admin
ADMIN_DATA = {
    'admin1': list(range(0, 25)),
    'admin2': list(range(25, 50)),
    'admin3': list(range(50, 75)),
    'admin4': list(range(75, 100))
}



# Load CSV data
def load_user_data():
    df = pd.read_csv('output.csv')
    return df

def validate_user(username, password):
    # Check if the user is an admin
    if username in ADMIN_USERS and ADMIN_USERS[username] == password:
        return {'user_id': username, 'role': 'admin'}
    
    # Otherwise, check the CSV file for regular users
    df = load_user_data()
    user_row = df[(df['user_id'] == username) & (df['password'] == password)]
    if not user_row.empty:
        return user_row.iloc[0].to_dict()
    
    return None

# Format user details to JSON format
def format_user_details(user_details):
    keys = [
        "Name", "Age", "Gender", "Blood_Type", "Medical_Condition", "Date_of_Admission",
        "Doctor", "Hospital", "Insurance_Provider", "Billing_Amount", "Room_Number",
        "Admission_Type", "Discharge_Date", "Medication", "Test_Results", "Alcohol_Level",
        "Heart_Rate", "Blood_Oxygen_Level", "Body_Temperature", "Weight", "MRI_Delay",
        "Prescription", "Dosage_in_mg", "Education_Level", "Dominant_Hand", "Family_History",
        "Smoking_Status", "Physical_Activity", "Depression_Status", "Cognitive_Test_Scores",
        "Medication_History", "Nutrition_Diet", "Sleep_Quality", "Chronic_Health_Conditions",
        "trestbps", "cholestral", "thalach"
    ]
    formatted_details = {key: user_details[key] for key in keys if key in user_details}
    return formatted_details

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_details = validate_user(username, password)
        
        if user_details:
            session['username'] = username
            session['user_details'] = format_user_details(user_details)
            
            # Debugging: Print the role of the user
            print(f"User {username} logged in with role: {user_details.get('role')}")
            
            if user_details.get('role') == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            return "Invalid credentials. Please try again."
    
    return render_template('login.html')

@app.route('/user_dashboard')
def user_dashboard():
    if 'username' in session and session['username'] != 'admin':
        user_details = session['user_details']
        user_name = user_details.get('Name')

        # Fetch any messages sent to this user by the admin
        chat_history = session.get('chat_history', {}).get(user_name, [])

        return render_template('user_dashboard.html', user_details=user_details, chat_history=chat_history)
    return redirect(url_for('login'))

# Assign rows to each admin dynamically
def assign_rows_to_admins(df):
    total_rows = len(df)
    rows_per_admin = 25
    ADMIN_DATA = {}

    for i, admin in enumerate(ADMIN_USERS):
        start_index = i * rows_per_admin
        end_index = start_index + rows_per_admin
        
        # Ensure we don't exceed the dataframe's length
        if start_index < total_rows:
            ADMIN_DATA[admin] = list(range(start_index, min(end_index, total_rows)))
        else:
            ADMIN_DATA[admin] = []  # No rows to assign if out-of-bounds

    return ADMIN_DATA

@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'username' in session and session['username'] in ADMIN_USERS:
        df = load_user_data()
        ADMIN_DATA = assign_rows_to_admins(df)
        admin_rows = ADMIN_DATA.get(session['username'], [])
        if admin_rows:
            admin_data = df.iloc[admin_rows]
            names = admin_data['Name'].tolist()
        else:
            names = []

        if request.method == 'POST':
            selected_user_name = request.form.get('user_name')
            if selected_user_name:
                # Fetch the user details
                user_row = df[df['Name'] == selected_user_name].iloc[0]
                
                # Store the message in the user's session or a database
                user_details = user_row.to_dict()
                message = f"Hi {selected_user_name}, it's been a long time you didn't give any update."
                
                # Save this message in the user's session for demonstration purposes
                if 'chat_history' not in session:
                    session['chat_history'] = {}
                session['chat_history'][selected_user_name] = session['chat_history'].get(selected_user_name, []) + [message]
                
                # Redirect to the admin dashboard after processing
                return redirect(url_for('admin_dashboard'))
        
        return render_template('admin_dashboard.html', names=names)
    else:
        return redirect(url_for('login'))


@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('user_input')
    user_details = session.get('user_details')
    conversation_history = request.json.get('conversation_history', [])
    
    if not user_details or not user_input:
        return jsonify({'error': 'Missing user details or input'}), 400

    # Create a prompt including user details and conversation history
    prompt = (
        "The following is a data of a patient "
        "You need to analyze it and give short answers and medications to the patient's queries:\n\n"
        f"Admission Type: {user_details.get('Admission_Type')}, "
        f"Age: {user_details.get('Age')}, "
        f"Alcohol Level: {user_details.get('Alcohol_Level')}, "
        f"Billing Amount: {user_details.get('Billing_Amount')}, "
        f"Blood Oxygen Level: {user_details.get('Blood_Oxygen_Level')}, "
        f"Blood Type: {user_details.get('Blood_Type')}, "
        f"Body Temperature: {user_details.get('Body_Temperature')}, "
        f"Chronic Health Conditions: {user_details.get('Chronic_Health_Conditions')}, "
        f"Cognitive Test Scores: {user_details.get('Cognitive_Test_Scores')}, "
        f"Date of Admission: {user_details.get('Date_of_Admission')}, "
        f"Depression Status: {user_details.get('Depression_Status')}, "
        f"Discharge Date: {user_details.get('Discharge_Date')}, "
        f"Doctor: {user_details.get('Doctor')}, "
        f"Dominant Hand: {user_details.get('Dominant_Hand')}, "
        f"Dosage in mg: {user_details.get('Dosage_in_mg')}, "
        f"Education Level: {user_details.get('Education_Level')}, "
        f"Family History: {user_details.get('Family_History')}, "
        f"Gender: {user_details.get('Gender')}, "
        f"Heart Rate: {user_details.get('Heart_Rate')}, "
        f"Hospital: {user_details.get('Hospital')}, "
        f"Insurance Provider: {user_details.get('Insurance_Provider')}, "
        f"MRI Delay: {user_details.get('MRI_Delay')}, "
        f"Medical Condition: {user_details.get('Medical_Condition')}, "
        f"Medication: {user_details.get('Medication')}, "
        f"Medication History: {user_details.get('Medication_History')}, "
        f"Name: {user_details.get('Name')}, "
        f"Nutrition Diet: {user_details.get('Nutrition_Diet')}, "
        f"Physical Activity: {user_details.get('Physical_Activity')}, "
        f"Prescription: {user_details.get('Prescription')}, "
        f"Room Number: {user_details.get('Room_Number')}, "
        f"Sleep Quality: {user_details.get('Sleep_Quality')}, "
        f"Smoking Status: {user_details.get('Smoking_Status')}, "
        f"Test Results: {user_details.get('Test_Results')}, "
        f"Weight: {user_details.get('Weight')}, "
        f"Cholesterol: {user_details.get('cholestral')}, "
        f"Thalach: {user_details.get('thalach')}, "
        f"Trestbps: {user_details.get('trestbps')}\n\n"
        f"Conversation History:\n" + "\n".join(conversation_history) + "\nChatbot:"
    )
    
    # Call the OpenAI API
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",  # or use "gpt-4" if you have access
        messages=[{"role": "user", "content": prompt}]
    )
    
    # Get the chatbot's response
    chatbot_response = response['choices'][0]['message']['content']
    
    return jsonify({'response': chatbot_response})

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_details', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)

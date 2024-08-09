$(document).ready(function() {
    let conversationHistory = [];

    $('#sendBtn').click(function() {
        let userInput = $('#chatInput').val();
        if (userInput.trim() === '') return;

        $('#chatlog').append(`<div><strong>You:</strong> ${userInput}</div>`);
        conversationHistory.push(`You: ${userInput}`);
        $('#chatInput').val('');

        $.ajax({
            url: '/chat',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                user_input: userInput,
                conversation_history: conversationHistory
            }),
            success: function(response) {
                $('#chatlog').append(`<div><strong>Chatbot:</strong> ${response.response}</div>`);
                conversationHistory.push(`Chatbot: ${response.response}`);
            },
            error: function() {
                $('#chatlog').append('<div><strong>Chatbot:</strong> There was an error processing your request.</div>');
            }
        });
    });
});

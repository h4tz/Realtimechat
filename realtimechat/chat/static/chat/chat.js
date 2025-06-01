const roomName = document.getElementById('room-name').value;
const chatSocket = new WebSocket('ws://127.0.0.1:8001/ws/chat/'+ roomName + '/');

// refrence to elements
const chatLog = document.getElementById('chat-log');
const messageInput = document.getElementById('chat-message-input');
const sendButton = document.getElementById('chat-message-submit');
const typingIndicator = document.getElementById('typing-indicator');




chatSocket.onopen = function(e){
    console.log('websocket connection established');
    chatSocket.send(JSON.stringify({'message': 'hellowww!!'}));
};



chatSocket.onmessage = function(e){
    const data = JSON.parse(e.data);
    const chatLog = document.getElementById('chat-log');
    if (data.message) {
        const p = document.createElement('p');
        p.innerHTML = `<strong>${data.user}:</strong> ${data.message}`;
        chatLog.appendChild(p);
    }
    if (data.typing) {
        typingIndicator.innerText = `${data.user} is typing ... `;
        setTimeout(() => {
           typingIndicator.innerText = '';
        }, 3000);
    }
    console.log('Recieved:', data.message);
};



let typingTimeout;


function sendMessage(){
    const message = messageInput.value;
    if (message.trim()){
        if(chatSocket.readyState === WebSocket.OPEN){
            chatSocket.send(JSON.stringify({ 'type': 'chat.message', 'message': message}));
        } else {
            console.error('websocket not open , cannot send message')
        } 
        messageInput.value = '';
    }
    if (typingTimeout) {
        clearTimeout(typingTimeout);
        typingTimeout = null;
    }
    if (chatSocket.readyState === WebSocket.OPEN){
        chatSocket.send(JSON.stringify({'is_typing': false ,
            'type': 'typing.indicator',
            'user' : username

        }));
    }
    
}

// attach sendMessage to buttons click event 
sendButton.onclick = sendMessage;


//typing indicator logic
messageInput.oninput = function(e) {
    if (chatSocket.readyState === WebSocket.OPEN){
        chatSocket.send(JSON.stringify({'typing': true}));
        if (typingTimeout) {
            clearTimeout(typingTimeout);
        }
        typingTimeout = setTimeout(() => {
            if (chatSocket.readyState === WebSocket.OPEN){
                chatSocket.send(JSON.stringify({'typing': false}));
            }
        }, 1000 );
    }
}

// allow enter key to send
messageInput.onkeyup = function(e){
    if (e.key === 'Enter'){
        sendMessage();
    }
}

//error handling

chatSocket.onclose = function(e) {
    console.log('Websocket closed unexpectedly', e);
    alert('Websocket connection lost ,please refresh');
}

chatSocket.onerror = function(e) {
    console.error(' WebSocket Error ', e);
}
(function () {
    if (window.hasOwnProperty('sourceSelectWidget')) return;
  
    // Load external CSS
    const styleLink = document.createElement("link");
    styleLink.rel = "stylesheet";
    styleLink.href = "/static/chat-widget.css";
    document.head.appendChild(styleLink);
  
    // Create the chat button
    const chatButton = document.createElement('div');
    chatButton.id = 'chat-button';
    chatButton.innerHTML = '💬';
    document.body.appendChild(chatButton);
  
    // Create the chat container
    const chatDiv = document.createElement('div');
    chatDiv.id = 'chat';
    document.body.appendChild(chatDiv);
  
    // Inject the chat UI
    chatDiv.innerHTML = `
      <div id="chat-window">
        <div class="msg bot">
          <div class="bot-msg-wrapper">
            <img src="https://backend.chatbase.co/storage/v1/object/public/chatbots-profile-pictures/f295df57-57e4-4b10-824d-e5659916d586/i91yeOUDGtHiX4ImHr8tA.jpg?width=24&height=24&quality=50" alt="Bot Avatar">
            <span>Bobot:</span>
          </div>
          <div class="user-msg-wrapper">Hi! Good Day, What can I help you with?</div>
        </div>
      </div>
      <input id="msg" placeholder="Ask me something..." />
      <button id="sendBtn">Send</button>
    `;
  
    const chatWindow = chatDiv.querySelector('#chat-window');
    let userInfoCaptured = false;
    let hasSentFirstMessage = false;
  
    function appendMessage(sender, text) {
      const msg = document.createElement('div');
      msg.className = 'msg ' + sender;
  
      if (sender === 'bot') {
        msg.innerHTML = `
          <div class="bot-msg-wrapper">
            <img src="https://backend.chatbase.co/storage/v1/object/public/chatbots-profile-pictures/f295df57-57e4-4b10-824d-e5659916d586/i91yeOUDGtHiX4ImHr8tA.jpg?width=24&height=24&quality=50" alt="Bot Avatar">
            <span>Bobot:</span>
          </div>
          <div class="user-msg-wrapper">${text}</div>
        `;
      } else {
        msg.innerHTML = `
          <div class="user-msg-wrapper">${text}</div>
        `;
      }
  
      chatWindow.appendChild(msg);
      chatWindow.scrollTop = chatWindow.scrollHeight;
    }
  
    function showTypingIndicator() {
      const typing = document.createElement('div');
      typing.className = 'bot-typing';
      typing.innerHTML = `
        <div class="typing-indicator">
          <span></span><span></span><span></span>
        </div>
      `;
      chatWindow.appendChild(typing);
      chatWindow.scrollTop = chatWindow.scrollHeight;
    }
  
    function removeTypingIndicator() {
      const typing = chatWindow.querySelector('.bot-typing');
      if (typing) typing.remove();
    }
  
    function showInlineFormMessage() {
      const msg = document.createElement('div');
      msg.className = 'msg bot';
      msg.innerHTML = `
        <div class="bot-msg-wrapper">
          <img src="https://backend.chatbase.co/storage/v1/object/public/chatbots-profile-pictures/f295df57-57e4-4b10-824d-e5659916d586/i91yeOUDGtHiX4ImHr8tA.jpg?width=24&height=24&quality=50" alt="Bot Avatar">
          <span>Bobot:</span>
        </div>
        <div class="user-msg-wrapper">
          Hello! It's great to hear from you. Before we dive into your questions or requests, could you please provide your name, email, and phone number? This will help us assist you better. Thank you!
        </div>
        <form id="inline-user-info-form" style="margin-top: 10px;">
          <input type="text" id="user-name" placeholder="Your Name" required />
          <input type="email" id="user-email" placeholder="Your Email" required />
          <input type="text" id="user-phone" placeholder="Your Phone" required />
          <button type="submit">Submit</button>
        </form>
      `;
      chatWindow.appendChild(msg);
      chatWindow.scrollTop = chatWindow.scrollHeight;
  
      msg.querySelector('#inline-user-info-form').addEventListener('submit', function (e) {
        e.preventDefault();
        const name = msg.querySelector('#user-name').value;
        const email = msg.querySelector('#user-email').value;
        const phone = msg.querySelector('#user-phone').value;
  
        sessionStorage.setItem("chat_user_name", name);
        sessionStorage.setItem("chat_user_email", email);
        sessionStorage.setItem("chat_user_phone", phone);
        userInfoCaptured = true;
        msg.querySelector('#inline-user-info-form').style.display = 'none';
        // Show confirmation
        appendMessage("bot", `Thanks ${name}, how can I assist you further?`);
      });
    }
  
    function sendMessage() {
      const input = chatDiv.querySelector('#msg');
      const message = input.value.trim();
      if (!message) return;
  
      appendMessage("user", message);
      input.value = '';
  
      if (!hasSentFirstMessage) {
        hasSentFirstMessage = true;
        showInlineFormMessage();
        return;
      }
  
      if (!userInfoCaptured) return;
  
      showTypingIndicator();
  
      fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          name: sessionStorage.getItem("chat_user_name"),
          email: sessionStorage.getItem("chat_user_email"),
          phone: sessionStorage.getItem("chat_user_phone")
        })
      })
        .then(resp => resp.json())
        .then(data => {
          removeTypingIndicator();
          appendMessage("bot", data.response);
        })
        .catch(() => {
          removeTypingIndicator();
          appendMessage("bot", "Oops! Something went wrong.");
        });
    }
  
    // Button listeners
    chatDiv.querySelector('#sendBtn').addEventListener('click', sendMessage);
    chatDiv.querySelector('#msg').addEventListener('keydown', function (e) {
      if (e.key === 'Enter') sendMessage();
    });
  
    chatButton.addEventListener('click', function () {
      const isOpen = chatDiv.style.display === 'block';
      chatDiv.style.display = isOpen ? 'none' : 'block';
    });
  
    window.sourceSelectWidget = true;
  })();
  
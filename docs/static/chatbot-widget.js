/* Libya B2B Chatbot Widget - Floating */
(function() {
    const widget = document.createElement('div');
    widget.id = 'chatbot-widget';
    widget.innerHTML = `
        <style>
            #chatbot-widget { position: fixed; bottom: 20px; right: 20px; z-index: 9999; font-family: 'Segoe UI', sans-serif; }
            #chatbot-toggle { width: 60px; height: 60px; border-radius: 50%; background: #00d2ff; color: white; border: none; font-size: 1.5rem; cursor: pointer; box-shadow: 0 4px 15px rgba(0,210,255,0.4); transition: transform 0.3s; }
            #chatbot-toggle:hover { transform: scale(1.1); }
            #chatbot-box { display: none; position: absolute; bottom: 70px; right: 0; width: 350px; height: 450px; background: white; border-radius: 15px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); overflow: hidden; flex-direction: column; }
            #chatbot-box.open { display: flex; }
            #chatbot-header { background: #1a1a2e; color: #00d2ff; padding: 15px; font-weight: bold; display: flex; justify-content: space-between; align-items: center; }
            #chatbot-close { background: none; border: none; color: #8892b0; font-size: 1.2rem; cursor: pointer; }
            #chatbot-messages { flex: 1; overflow-y: auto; padding: 15px; display: flex; flex-direction: column; gap: 10px; }
            .chat-msg { max-width: 80%; padding: 10px 15px; border-radius: 12px; font-size: 0.9rem; line-height: 1.4; }
            .chat-msg.user { align-self: flex-end; background: #00d2ff; color: white; border-bottom-right-radius: 4px; }
            .chat-msg.bot { align-self: flex-start; background: #f0f0f0; color: #333; border-bottom-left-radius: 4px; }
            #chatbot-input { display: flex; padding: 10px; gap: 8px; border-top: 1px solid #eee; }
            #chatbot-input input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 20px; outline: none; }
            #chatbot-input button { padding: 10px 18px; background: #00d2ff; color: white; border: none; border-radius: 20px; cursor: pointer; font-weight: bold; }
            [dir="rtl"] #chatbot-widget { right: auto; left: 20px; }
            [dir="rtl"] #chatbot-box { right: auto; left: 0; }
        </style>
        <button id="chatbot-toggle" onclick="document.getElementById('chatbot-box').classList.toggle('open')">💬</button>
        <div id="chatbot-box">
            <div id="chatbot-header">
                <span>AI Assistant</span>
                <button id="chatbot-close" onclick="document.getElementById('chatbot-box').classList.remove('open')">✕</button>
            </div>
            <div id="chatbot-messages">
                <div class="chat-msg bot">Welcome! How can I help you?</div>
            </div>
            <div id="chatbot-input">
                <input type="text" id="chatbot-text" placeholder="Type a message..." onkeypress="if(event.key==='Enter')sendChat()">
                <button onclick="sendChat()">Send</button>
            </div>
        </div>
    `;
    document.body.appendChild(widget);

    const sessionId = 'web-' + Date.now();
    const isAR = document.documentElement.dir === 'rtl';

    window.sendChat = async function() {
        const input = document.getElementById('chatbot-text');
        const msg = input.value.trim();
        if (!msg) return;
        input.value = '';

        const messages = document.getElementById('chatbot-messages');
        messages.innerHTML += `<div class="chat-msg user">${msg}</div>`;
        messages.scrollTop = messages.scrollHeight;

        try {
            const res = await fetch(`${window.API_BASE}/api/chat`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ session_id: sessionId, message: msg, is_arabic: isAR })
            });
            const data = await res.json();
            messages.innerHTML += `<div class="chat-msg bot">${data.response}</div>`;
            messages.scrollTop = messages.scrollHeight;
        } catch(e) {
            messages.innerHTML += `<div class="chat-msg bot">Error: ${e.message}</div>`;
        }
    };
})();

/**
 * Libya B2B — WebSocket Client for Realtime Messaging
 *
 * Usage:
 *   const ws = new MessageWS(conversationId, userId, userRole);
 *   ws.onMessage = (msg) => { ... };
 *   ws.onTyping = (sender) => { ... };
 *   ws.onRead = (reader) => { ... };
 *   ws.send('Hello!');
 *   ws.sendTyping();
 *   ws.sendRead();
 *   ws.disconnect();
 */
class MessageWS {
    constructor(conversationId, userId, userRole) {
        this.conversationId = conversationId;
        this.userId = userId;
        this.userRole = userRole || 'buyer';
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnect = 5;
        this.reconnectDelay = 1000;

        // Callbacks (override these)
        this.onMessage = null;   // (msg) => {}
        this.onTyping = null;    // (sender) => {}
        this.onRead = null;      // (reader) => {}
        this.onConnect = null;   // () => {}
        this.onDisconnect = null; // () => {}

        this._connect();
    }

    _connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        const url = `${protocol}//${host}/api/b2b/messages/ws/${this.conversationId}`;

        try {
            this.ws = new WebSocket(url);
        } catch (e) {
            console.error('WebSocket creation failed:', e);
            this._scheduleReconnect();
            return;
        }

        this.ws.onopen = () => {
            console.log(`[WS] Connected to conversation ${this.conversationId}`);
            this.reconnectAttempts = 0;
            if (this.onConnect) this.onConnect();
        };

        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this._handleMessage(data);
            } catch (e) {
                console.error('[WS] Parse error:', e);
            }
        };

        this.ws.onclose = (event) => {
            console.log(`[WS] Disconnected (code: ${event.code})`);
            if (this.onDisconnect) this.onDisconnect();
            this._scheduleReconnect();
        };

        this.ws.onerror = (error) => {
            console.error('[WS] Error:', error);
        };
    }

    _handleMessage(data) {
        switch (data.type) {
            case 'message':
                if (this.onMessage) this.onMessage(data);
                break;
            case 'typing':
                if (this.onTyping) this.onTyping(data.sender_type);
                break;
            case 'read':
                if (this.onRead) this.onRead(data.reader);
                break;
        }
    }

    _scheduleReconnect() {
        if (this.reconnectAttempts < this.maxReconnect) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
            console.log(`[WS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
            setTimeout(() => this._connect(), delay);
        } else {
            console.log('[WS] Max reconnect attempts reached');
        }
    }

    send(text) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'message',
                sender_type: this.userRole,
                sender_id: this.userId,
                text: text,
            }));
        }
    }

    sendTyping() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'typing',
                sender_type: this.userRole,
            }));
        }
    }

    sendRead() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'read',
                sender_type: this.userRole,
            }));
        }
    }

    disconnect() {
        this.maxReconnect = 0; // Prevent reconnect
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    get isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }
}

// Export for use in templates
window.MessageWS = MessageWS;

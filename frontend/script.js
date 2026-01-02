document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const appSelect = document.getElementById('app-select');
    const appTitle = document.getElementById('app-title');
    const chatToggle = document.getElementById('chat-toggle');
    const chatContainer = document.getElementById('chat-container');
    const closeChat = document.getElementById('close-chat');
    const chatAppBadge = document.getElementById('chat-app-badge');
    const welcomeMessage = document.getElementById('welcome-message');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const chatMessages = document.getElementById('chat-messages');
    const comparisonModeCheckbox = document.getElementById('comparison-mode');

    // API URL
    const API_URL = 'http://localhost:8000';

    // State
    let currentApp = '';

    // --- Initialization ---
    fetchApps();

    async function fetchApps() {
        try {
            const response = await fetch(`${API_URL}/apps`);
            const apps = await response.json();

            appSelect.innerHTML = '';
            apps.forEach(appName => {
                const option = document.createElement('option');
                option.value = appName;
                option.textContent = appName;
                appSelect.appendChild(option);
            });

            if (apps.length > 0) {
                currentApp = apps[0];
                updateAppContext();
            }
        } catch (err) {
            console.error('Failed to fetch apps:', err);
        }
    }

    // --- Event Listeners ---

    // App Switcher
    appSelect.addEventListener('change', (e) => {
        currentApp = e.target.value;
        updateAppContext();
    });

    // Chat Toggle
    chatToggle.addEventListener('click', () => {
        chatContainer.classList.add('active');
    });

    closeChat.addEventListener('click', () => {
        chatContainer.classList.remove('active');
    });

    // Send Message
    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    // --- Functions ---

    function updateAppContext() {
        appTitle.textContent = `${currentApp} Dashboard`;
        chatAppBadge.textContent = currentApp;
        if (welcomeMessage) {
            welcomeMessage.innerHTML = `Hello! I'm your assistant for <b>${currentApp}</b>. How can I help you today?`;
        }
    }

    async function sendMessage() {
        const text = userInput.value.trim();
        if (!text) return;

        userInput.value = '';
        addMessage(text, 'user');

        const isComparison = comparisonModeCheckbox.checked;
        const appContext = isComparison ? "comparison" : currentApp;

        const loadingId = addMessage('Thinking...', 'bot');

        try {
            const response = await fetch(`${API_URL}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: text,
                    app: appContext
                }),
            });

            if (!response.ok) throw new Error('Network response was not ok');

            const data = await response.json();

            const loadingMsg = document.getElementById(loadingId);
            if (loadingMsg) loadingMsg.remove();

            addMessage(data.response, 'bot');

        } catch (error) {
            console.error('Error:', error);
            const loadingMsg = document.getElementById(loadingId);
            if (loadingMsg) loadingMsg.textContent = "Sorry, I encountered an error connecting to the server.";
        }
    }

    function addMessage(text, sender) {
        const msgDiv = document.createElement('div');
        msgDiv.classList.add('message', sender);

        if (sender === 'bot') {
            msgDiv.innerHTML = text.replace(/\n/g, '<br>');
        } else {
            msgDiv.textContent = text;
        }

        const id = 'msg-' + Date.now();
        msgDiv.id = id;

        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return id;
    }
});

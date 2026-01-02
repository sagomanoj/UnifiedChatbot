document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const appSelect = document.getElementById('app-select');
    const appTitle = document.getElementById('app-title');
    const chatToggle = document.getElementById('chat-toggle');
    const chatContainer = document.getElementById('chat-container');
    const closeChat = document.getElementById('close-chat');
    const chatAppBadge = document.getElementById('chat-app-badge');
    const welcomeAppName = document.getElementById('welcome-app-name');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const chatMessages = document.getElementById('chat-messages');
    const manualUpload = document.getElementById('manual-upload');
    const uploadStatusText = document.getElementById('upload-status-text');
    const comparisonModeCheckbox = document.getElementById('comparison-mode');

    // API URL
    const API_URL = 'http://localhost:8000';

    // State
    let currentApp = appSelect.value;

    // --- Event Listeners ---

    // App Switcher
    appSelect.addEventListener('change', (e) => {
        currentApp = e.target.value;
        updateAppContext();
    });

    // Chat Toggle
    chatToggle.addEventListener('click', () => {
        chatContainer.classList.add('active');
        // chatToggle.style.transform = 'scale(0)';
    });

    closeChat.addEventListener('click', () => {
        chatContainer.classList.remove('active');
        // chatToggle.style.transform = 'scale(1)';
    });

    // Send Message
    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    // File Upload
    manualUpload.addEventListener('change', uploadManual);

    // --- Functions ---

    function updateAppContext() {
        appTitle.textContent = `${currentApp} Dashboard`;
        chatAppBadge.textContent = currentApp;
        welcomeAppName.textContent = currentApp;

        // Add a system message about context switch
        addMessage(`System: Switched context to ${currentApp}.`, 'bot');
    }

    async function sendMessage() {
        const text = userInput.value.trim();
        if (!text) return;

        // Clear input
        userInput.value = '';

        // Add user message
        addMessage(text, 'user');

        // Determine context (Comparison or Single App)
        const isComparison = comparisonModeCheckbox.checked;
        const appContext = isComparison ? "comparison" : currentApp;

        // Show loading state (optional)
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

            // Remove loading message
            const loadingMsg = document.getElementById(loadingId);
            if (loadingMsg) loadingMsg.remove();

            // Add bot response
            addMessage(data.response, 'bot');

        } catch (error) {
            console.error('Error:', error);
            const loadingMsg = document.getElementById(loadingId);
            if (loadingMsg) loadingMsg.textContent = "Sorry, I encountered an error connecting to the server.";
        }
    }

    async function uploadManual(e) {
        const file = e.target.files[0];
        if (!file) return;

        uploadStatusText.textContent = "Uploading...";

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(`${API_URL}/upload/${encodeURIComponent(currentApp)}`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) throw new Error('Upload failed');

            const data = await response.json();
            uploadStatusText.textContent = "Upload Complete";
            addMessage(`Successfully uploaded manual for ${currentApp}.`, 'bot');

            setTimeout(() => {
                uploadStatusText.textContent = "Upload Manual";
            }, 3000);

        } catch (error) {
            console.error('Error:', error);
            uploadStatusText.textContent = "Upload Failed";
            addMessage(`Failed to upload document: ${error.message}`, 'bot');
        }
    }

    function addMessage(text, sender) {
        const msgDiv = document.createElement('div');
        msgDiv.classList.add('message', sender);

        // Handle simple markdown-like formatting if needed, or just text
        // For now, just preserving newlines
        msgDiv.textContent = text;
        msgDiv.style.whiteSpace = 'pre-wrap';

        const id = 'msg-' + Date.now();
        msgDiv.id = id;

        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return id;
    }
});

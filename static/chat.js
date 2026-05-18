document.addEventListener('DOMContentLoaded', function () {
    const chatToggle = document.getElementById('chatToggle');
    const chatPanel = document.getElementById('chatPanel');
    const chatClose = document.getElementById('chatClose');
    const chatForm = document.getElementById('chatForm');
    const chatInput = document.getElementById('chatInput');
    const chatBody = document.getElementById('chatBody');

    if (!chatToggle || !chatPanel || !chatForm || !chatInput || !chatBody) {
        return;
    }

    function toggleChat(open) {
        const isVisible = chatPanel.classList.contains('visible');
        const shouldOpen = open === undefined ? !isVisible : open;

        if (!shouldOpen) {
            const activeElement = document.activeElement;
            if (chatPanel.contains(activeElement)) {
                chatToggle.focus();
            }
        }

        chatPanel.classList.toggle('visible', shouldOpen);
        if (shouldOpen) {
            chatPanel.removeAttribute('aria-hidden');
            chatPanel.removeAttribute('inert');
            setTimeout(() => chatInput.focus(), 200);
            scrollChatToBottom();
        } else {
            chatPanel.setAttribute('aria-hidden', 'true');
            chatPanel.setAttribute('inert', '');
        }
    }

    async function loadChatHistory() {
        try {
            const response = await fetch('/api/chat/history');
            if (!response.ok) {
                throw new Error('No autorizado');
            }

            const data = await response.json();
            chatBody.innerHTML = '';

            if (data.messages && data.messages.length) {
                data.messages.forEach(msg => {
                    appendMessage(msg.mensaje, msg.remitente === 'bot' ? 'bot' : 'user');
                });
            } else {
                appendMessage('Hola, soy tu asistente. Pregunta lo que necesites.', 'bot');
            }

            scrollChatToBottom();
        } catch (error) {
            console.error('Error cargando el historial de chat:', error);
            appendMessage('No se pudo cargar el historial de chat.', 'bot');
        }
    }

    function appendMessage(text, sender) {
        const messageEl = document.createElement('div');
        messageEl.className = `message ${sender}`;
        messageEl.textContent = text;
        chatBody.appendChild(messageEl);
        scrollChatToBottom();
    }

    function scrollChatToBottom() {
        chatBody.scrollTop = chatBody.scrollHeight;
    }

    async function sendMessage(message) {
        if (!message || !message.trim()) {
            return;
        }

        appendMessage(message, 'user');
        chatInput.value = '';

        try {
            const response = await fetch('/api/chat/send', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message })
            });

            if (!response.ok) {
                throw new Error('Error al enviar el mensaje');
            }

            const data = await response.json();
            if (data.reply) {
                appendMessage(data.reply, 'bot');
            } else {
                appendMessage('No recibimos respuesta del servicio.', 'bot');
            }
        } catch (error) {
            console.error('Error enviando mensaje de chat:', error);
            appendMessage('Ocurrió un error al enviar tu mensaje.', 'bot');
        }
    }

    chatToggle.addEventListener('click', () => toggleChat());
    chatClose.addEventListener('click', () => toggleChat(false));

    chatForm.addEventListener('submit', function (event) {
        event.preventDefault();
        const message = chatInput.value;
        sendMessage(message);
    });

    loadChatHistory();
});

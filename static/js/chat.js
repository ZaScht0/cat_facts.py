// JavaScript для работы чат-бота
document.addEventListener('DOMContentLoaded', function() {
    // Получаем элементы DOM
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const chatMessages = document.getElementById('chat-messages');
    const clearButton = document.getElementById('clear-button');
    const typingIndicator = document.getElementById('typing-indicator');

    // Генерируем уникальный ID сессии
    const sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

    // Функция для добавления сообщения в чат
    function addMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        messageDiv.classList.add(role === 'user' ? 'user-message' : 'bot-message');

        const messageHeader = document.createElement('div');
        messageHeader.classList.add('message-header');
        messageHeader.textContent = role === 'user' ? 'Вы' : 'Qwen AI';

        const messageContent = document.createElement('div');
        messageContent.classList.add('message-content');
        messageContent.textContent = content;

        messageDiv.appendChild(messageHeader);
        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);

        // Прокручиваем к новому сообщению
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Функция для отправки сообщения
    async function sendMessage() {
        const message = messageInput.value.trim();
        if (!message) return;

        // Добавляем сообщение пользователя в чат
        addMessage('user', message);

        // Очищаем поле ввода
        messageInput.value = '';

        // Показываем индикатор набора текста
        typingIndicator.style.display = 'block';
        chatMessages.scrollTop = chatMessages.scrollHeight;

        // Блокируем кнопку отправки
        sendButton.disabled = true;

        try {
            // Отправляем запрос к серверу
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `message=${encodeURIComponent(message)}&session_id=${sessionId}`
            });

            const data = await response.json();

            // Скрываем индикатор набора текста
            typingIndicator.style.display = 'none';

            // Добавляем ответ бота в чат
            addMessage('assistant', data.bot_response);
        } catch (error) {
            // Скрываем индикатор набора текста
            typingIndicator.style.display = 'none';

            // Показываем сообщение об ошибке
            addMessage('assistant', 'Произошла ошибка при отправке сообщения. Попробуйте еще раз.');
            console.error('Ошибка:', error);
        } finally {
            // Разблокируем кнопку отправки
            sendButton.disabled = false;
            messageInput.focus();
        }
    }

    // Функция для очистки истории чата
    async function clearHistory() {
        if (confirm('Вы уверены, что хотите очистить историю чата?')) {
            try {
                await fetch(`/clear/${sessionId}`, {
                    method: 'POST'
                });

                // Очищаем чат на клиенте
                chatMessages.innerHTML = '';
                typingIndicator.style.display = 'none';

                // Добавляем приветственное сообщение
                addMessage('assistant', 'Привет! Я Qwen AI. Как я могу вам помочь?');
            } catch (error) {
                console.error('Ошибка при очистке истории:', error);
                alert('Произошла ошибка при очистке истории');
            }
        }
    }

    // Загружаем историю чата при загрузке страницы
    async function loadChatHistory() {
        try {
            const response = await fetch(`/history/${sessionId}`);
            const data = await response.json();

            // Добавляем сообщения из истории
            data.history.forEach(msg => {
                addMessage(msg.role, msg.content);
            });

            // Если история пуста, добавляем приветственное сообщение
            if (data.history.length === 0) {
                addMessage('assistant', 'Привет! Я Qwen AI. Как я могу вам помочь?');
            }
        } catch (error) {
            console.error('Ошибка при загрузке истории:', error);
            addMessage('assistant', 'Привет! Я Qwen AI. Как я могу вам помочь?');
        }
    }

    // Обработчики событий
    sendButton.addEventListener('click', sendMessage);

    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    clearButton.addEventListener('click', clearHistory);

    // Загружаем историю чата
    loadChatHistory();

    // Устанавливаем фокус на поле ввода
    messageInput.focus();
});
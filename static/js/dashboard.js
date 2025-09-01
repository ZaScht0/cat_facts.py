// JavaScript для панели управления
document.addEventListener('DOMContentLoaded', function() {
    // Открытие модального окна создания чата
    window.openCreateChatModal = function(chatType = '') {
        document.getElementById('createChatModal').style.display = 'block';
        if (chatType) {
            document.getElementById('chatType').value = chatType;
        }
    };

    // Закрытие модального окна создания чата
    window.closeCreateChatModal = function() {
        document.getElementById('createChatModal').style.display = 'none';
    };

    // Открытие чата
    window.openChat = function(chatId) {
        window.location.href = `/chat/${chatId}`;
    };

    // Обработка отправки формы создания чата
    document.getElementById('createChatForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        
        try {
            const response = await fetch('/create_chat', {
                method: 'POST',
                body: new URLSearchParams(formData)
            });
            
            const data = await response.json();
            
            if (data.chat_id) {
                // Закрываем модальное окно
                closeCreateChatModal();
                
                // Очищаем форму
                this.reset();
                
                // Переходим к новому чату
                window.location.href = `/chat/${data.chat_id}`;
            } else {
                alert('Ошибка при создании чата');
            }
        } catch (error) {
            console.error('Ошибка:', error);
            alert('Произошла ошибка при создании чата');
        }
    });

    // Закрытие модального окна при клике вне его
    window.onclick = function(event) {
        const modal = document.getElementById('createChatModal');
        if (event.target == modal) {
            closeCreateChatModal();
        }
    };
});
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx
import os
from typing import List, Dict
import json

# Создаем экземпляр FastAPI приложения
app = FastAPI(
    title="Free Chat Bot",
    description="Веб-приложение с бесплатным чат-ботом",
    version="1.0.0"
)

# Подключаем статические файлы (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Подключаем шаблоны HTML
templates = Jinja2Templates(directory="templates")

# Здесь будет храниться история чатов
chat_history: Dict[str, List[Dict[str, str]]] = {}

# Настройки для Ollama
OLLAMA_API_URL = "http://localhost:11434/api/chat"

class FreeChatBot:
    """Класс для взаимодействия с локальными моделями через Ollama"""
    
    async def get_response(self, message: str, history: List[Dict[str, str]]) -> str:
        """
        Получает ответ от локальной модели
        
        Args:
            message: Сообщение пользователя
            history: История диалога
            
        Returns:
            Ответ от модели
        """
        # Формируем контекст диалога
        messages = []
        
        # Добавляем системное сообщение
        messages.append({
            "role": "system",
            "content": "Вы helpful assistant. Отвечайте кратко и по существу на русском языке."
        })
        
        # Добавляем историю диалога
        for msg in history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Добавляем новое сообщение пользователя
        messages.append({
            "role": "user",
            "content": message
        })
        
        # Параметры запроса к Ollama
        payload = {
            "model": "llama2",  # Вы можете изменить на другую модель
            "messages": messages,
            "stream": False
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    OLLAMA_API_URL,
                    json=payload,
                    timeout=60.0  # Увеличенный таймаут для локальных моделей
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["message"]["content"]
                else:
                    return f"Ошибка локальной модели: {response.status_code} - {response.text}"
                    
        except httpx.ConnectError:
            return "Ошибка: Не удалось подключиться к локальной модели. Убедитесь, что Ollama запущен."
        except Exception as e:
            return f"Ошибка при обращении к локальной модели: {str(e)}"

# Создаем экземпляр чат-бота
bot = FreeChatBot()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Главная страница приложения
    """
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "Free Chat Bot"
    })

@app.post("/chat")
async def chat(message: str = Form(...), session_id: str = Form(...)):
    """
    Обработчик сообщений чата
    """
    # Инициализируем историю для новой сессии
    if session_id not in chat_history:
        chat_history[session_id] = []
    
    # Добавляем сообщение пользователя в историю
    chat_history[session_id].append({
        "role": "user",
        "content": message
    })
    
    # Получаем ответ от локальной модели
    bot_response = await bot.get_response(message, chat_history[session_id])
    
    # Добавляем ответ бота в историю
    chat_history[session_id].append({
        "role": "assistant",
        "content": bot_response
    })
    
    return {
        "user_message": message,
        "bot_response": bot_response
    }

@app.get("/history/{session_id}")
async def get_history(session_id: str):
    """
    Получает историю чата для указанной сессии
    """
    return {"history": chat_history.get(session_id, [])}

@app.post("/clear/{session_id}")
async def clear_history(session_id: str):
    """
    Очищает историю чата для указанной сессии
    """
    if session_id in chat_history:
        chat_history[session_id] = []
    return {"message": "История очищена"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
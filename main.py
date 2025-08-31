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
    title="Qwen Chat Bot",
    description="Веб-приложение с чат-ботом Qwen AI",
    version="1.0.0"
)

# Подключаем статические файлы (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Подключаем шаблоны HTML
templates = Jinja2Templates(directory="templates")

# Здесь будет храниться история чатов (в реальном приложении используйте базу данных)
chat_history: Dict[str, List[Dict[str, str]]] = {}

# Замените на ваш API ключ Qwen (или установите как переменную окружения)
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "your-api-key-here")
QWEN_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"


class QwenChatBot:
    """Класс для взаимодействия с Qwen AI API"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    async def get_response(self, message: str, history: List[Dict[str, str]]) -> str:
        """
        Получает ответ от Qwen AI

        Args:
            message: Сообщение пользователя
            history: История диалога

        Returns:
            Ответ от Qwen AI
        """
        # Формируем контекст диалога
        messages = []
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

        # Параметры запроса к API
        payload = {
            "model": "qwen-turbo",  # Или "qwen-plus" для более мощной модели
            "input": {
                "messages": messages
            },
            "parameters": {
                "max_tokens": 1500,
                "temperature": 0.8,
                "top_p": 0.8
            }
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    QWEN_API_URL,
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )

                if response.status_code == 200:
                    data = response.json()
                    return data["output"]["text"]
                else:
                    return f"Ошибка API: {response.status_code} - {response.text}"

        except Exception as e:
            return f"Ошибка при обращении к API: {str(e)}"


# Создаем экземпляр чат-бота
bot = QwenChatBot(QWEN_API_KEY)


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Главная страница приложения
    """
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "Qwen Chat Bot"
    })


@app.post("/chat")
async def chat(message: str = Form(...), session_id: str = Form(...)):
    """
    Обработчик сообщений чата

    Args:
        message: Сообщение пользователя
        session_id: Идентификатор сессии пользователя

    Returns:
        JSON с ответом от бота
    """
    # Инициализируем историю для новой сессии
    if session_id not in chat_history:
        chat_history[session_id] = []

    # Добавляем сообщение пользователя в историю
    chat_history[session_id].append({
        "role": "user",
        "content": message
    })

    # Получаем ответ от Qwen AI
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

    Args:
        session_id: Идентификатор сессии

    Returns:
        История чата
    """
    return {"history": chat_history.get(session_id, [])}


@app.post("/clear/{session_id}")
async def clear_history(session_id: str):
    """
    Очищает историю чата для указанной сессии

    Args:
        session_id: Идентификатор сессии
    """
    if session_id in chat_history:
        chat_history[session_id] = []
    return {"message": "История очищена"}


# Запуск приложения
if __name__ == "__main__":
    import uvicorn

    # Используем localhost вместо 0.0.0.0 для локальной разработки
    uvicorn.run(app, host="127.0.0.1", port=8000)
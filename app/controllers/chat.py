from fastapi import Request, Form, Depends, HTTPException, APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse
import sqlite3

from app.config.core.config import templates
from app.config.core.depends import bot
from app.repositories.chat_repositories import get_user_chats, create_chat, add_message, get_chat_messages, \
    clear_chat_history
from app.repositories.user_repositories import get_current_user

router = APIRouter(prefix="/chat", tags=["chat"])


# Защищенные маршруты
@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request, current_user: dict = Depends(get_current_user)):
    return RedirectResponse(url="/dashboard")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, current_user: dict = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login")

    # Получаем список чатов пользователя
    chats = get_user_chats(current_user["id"])

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "title": "Панель управления",
        "user": current_user,
        "chats": chats
    })


@router.get("/chat/{chat_id}", response_class=HTMLResponse)
async def chat_page(request: Request, chat_id: int, current_user: dict = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login")

    chat = chat_belong_user(chat_id, current_user)

    if not chat:
        return RedirectResponse(url="/dashboard")

    return templates.TemplateResponse("chat.html", {
        "request": request,
        "title": chat[1],
        "chat_id": chat[0],
        "chat_name": chat[1],
        "chat_type": chat[2],
        "user": current_user
    })


@router.post("/create_chat")
async def create_chat_endpoint(
        request: Request,
        name: str = Form(...),
        chat_type: str = Form(...),
        current_user: dict = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Не авторизован")

    chat_id = create_chat(current_user["id"], name, chat_type)

    # Добавляем приветственное сообщение от бота
    welcome_messages = {
        "analysis": "Привет! Я ваш ИИ-ассистент по маркетинговому анализу. Расскажите, какие данные вы хотите проанализировать?",
        "strategy": "Привет! Я ваш ИИ-стратег по маркетингу. Какую маркетинговую стратегию вы хотите разработать?",
        "content": "Привет! Я ваш ИИ-копирайтер. Какой контент вы хотите создать?",
        "ads": "Привет! Я ваш ИИ-специалист по рекламе. Какую рекламную кампанию вы хотите запустить?",
        "seo": "Привет! Я ваш ИИ-SEO специалист. Что вы хотите оптимизировать?",
        "social": "Привет! Я ваш ИИ-специалист по социальным сетям. Какой контент для соцсетей вы хотите создать?"
    }

    welcome_message = welcome_messages.get(chat_type, "Привет! Я ваш маркетинговый ИИ-ассистент. Чем могу помочь?")
    add_message(chat_id, "assistant", welcome_message)

    return {"chat_id": chat_id}


@router.post("/chat/{chat_id}/message")
async def chat_message(
        chat_id: int,
        message: str = Form(...),
        current_user: dict = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Не авторизован")

    chat = chat_belong_user(chat_id, current_user)

    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден")

    # Добавляем сообщение пользователя
    add_message(chat_id, "user", message)

    # Получаем историю чата
    history = get_chat_messages(chat_id)

    # Получаем ответ от ИИ агента
    bot_response = await bot.get_response(message, history, chat[0])

    # Добавляем ответ бота
    add_message(chat_id, "assistant", bot_response)

    return {
        "user_message": message,
        "bot_response": bot_response
    }


@router.get("/chat/{chat_id}/history")
async def get_chat_history(chat_id: int, current_user: dict = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Не авторизован")

    if not chat_belong_user(chat_id, current_user):
        raise HTTPException(status_code=404, detail="Чат не найден")

    messages = get_chat_messages(chat_id)
    return {"history": messages}


@router.post("/chat/{chat_id}/clear")
async def clear_chat(chat_id: int, current_user: dict = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Не авторизован")

    if not chat_belong_user(chat_id, current_user):
        raise HTTPException(status_code=404, detail="Чат не найден")

    clear_chat_history(chat_id)
    return {"message": "История очищена"}


# Проверяем, что чат принадлежит пользователю
def chat_belong_user(chat_id: int, current_user: dict = Depends(get_current_user)):
    conn = sqlite3.connect('crm.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM chats WHERE id = ? AND user_id = ?", (chat_id, current_user["id"]))
    chat = cursor.fetchone()
    conn.close()
    return chat

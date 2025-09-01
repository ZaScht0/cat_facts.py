from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
import httpx
import os
from typing import List, Dict, Optional
import json
import uuid
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import sqlite3
from pydantic import BaseModel

# Создаем экземпляр FastAPI приложения
app = FastAPI(
    title="Marketing AI Agent CRM",
    description="Веб-приложение с ИИ агентом для маркетинга",
    version="1.0.0"
)

# Подключаем статические файлы (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Подключаем шаблоны HTML
templates = Jinja2Templates(directory="templates")

# Настройки безопасности
SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('crm.db')
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица чатов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            chat_type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Таблица сообщений
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chat_id) REFERENCES chats (id)
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

# Модели данных
class User(BaseModel):
    id: int
    username: str
    email: str

class Chat(BaseModel):
    id: int
    user_id: int
    name: str
    chat_type: str

class Message(BaseModel):
    id: int
    chat_id: int
    role: str
    content: str

# Вспомогательные функции для работы с БД
def get_user_by_username(username: str):
    conn = sqlite3.connect('crm.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, hashed_password FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {"id": user[0], "username": user[1], "email": user[2], "hashed_password": user[3]}
    return None

def get_user_by_id(user_id: int):
    conn = sqlite3.connect('crm.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {"id": user[0], "username": user[1], "email": user[2]}
    return None

def create_user(username: str, email: str, password: str):
    hashed_password = pwd_context.hash(password)
    conn = sqlite3.connect('crm.db')
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, email, hashed_password) VALUES (?, ?, ?)",
            (username, email, hashed_password)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return {"id": user_id, "username": username, "email": email}
    except sqlite3.IntegrityError:
        conn.close()
        return None

def create_chat(user_id: int, name: str, chat_type: str):
    conn = sqlite3.connect('crm.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chats (user_id, name, chat_type) VALUES (?, ?, ?)",
        (user_id, name, chat_type)
    )
    conn.commit()
    chat_id = cursor.lastrowid
    conn.close()
    return chat_id

def get_user_chats(user_id: int):
    conn = sqlite3.connect('crm.db')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, chat_type, created_at FROM chats WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    )
    chats = cursor.fetchall()
    conn.close()
    return [{"id": chat[0], "name": chat[1], "chat_type": chat[2], "created_at": chat[3]} for chat in chats]

def add_message(chat_id: int, role: str, content: str):
    conn = sqlite3.connect('crm.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)",
        (chat_id, role, content)
    )
    conn.commit()
    message_id = cursor.lastrowid
    conn.close()
    return message_id

def get_chat_messages(chat_id: int):
    conn = sqlite3.connect('crm.db')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role, content, timestamp FROM messages WHERE chat_id = ? ORDER BY timestamp ASC",
        (chat_id,)
    )
    messages = cursor.fetchall()
    conn.close()
    return [{"role": msg[0], "content": msg[1], "timestamp": msg[2]} for msg in messages]

def clear_chat_history(chat_id: int):
    conn = sqlite3.connect('crm.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()

# Функции безопасности
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(username: str, password: str):
    user = get_user_by_username(username)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        user = get_user_by_username(username)
        return user
    except JWTError:
        return None

# Настройки для Ollama
OLLAMA_API_URL = "http://localhost:11434/api/chat"

class MarketingAIBot:
    """Класс для взаимодействия с ИИ агентом для маркетинга через Ollama"""
    
    async def get_response(self, message: str, history: List[Dict[str, str]], chat_type: str) -> str:
        """
        Получает ответ от локальной модели с учетом типа чата
        
        Args:
            message: Сообщение пользователя
            history: История диалialogа
            chat_type: Тип чата (анализ, стратегия, контент, реклама и т.д.)
            
        Returns:
            Ответ от модели
        """
        # Формируем контекст диалога
        messages = []
        
        # Добавляем системное сообщение в зависимости от типа чата
        system_prompts = {
            "analysis": "Вы эксперт по маркетинговому анализу. Помогайте анализировать данные, метрики и показатели эффективности маркетинговых кампаний. Отвечайте профессионально и по существу на русском языке.",
            "strategy": "Вы стратег по маркетингу. Помогайте разрабатывать маркетинговые стратегии, планы и кампании. Предлагайте конкретные решения и шаги. Отвечайте профессионально и по существу на русском языке.",
            "content": "Вы копирайтер и контент-менеджер. Помогайте создавать качественный контент для различных каналов: социальные сети, блоги, email-рассылки. Отвечайте профессионально и по существу на русском языке.",
            "ads": "Вы специалист по рекламе. Помогайте создавать эффективные рекламные кампании, подбирать таргетинг, писать объявления и оптимизировать расходы. Отвечайте профессионально и по существу на русском языке.",
            "seo": "Вы SEO-специалист. Помогайте с оптимизацией контента, подбором ключевых слов, анализом позиций и улучшением видимости в поисковых системах. Отвечайте профессионально и по существу на русском языке.",
            "social": "Вы специалист по социальным сетям. Помогайте разрабатывать контент-планы, анализировать эффективность, работать с аудиторией и создавать вовлекающий контент. Отвечайте профессионально и по существу на русском языке."
        }
        
        system_message = system_prompts.get(chat_type, "Вы помощник по маркетингу. Отвечайте профессионально и по существу на русском языке.")
        
        messages.append({
            "role": "system",
            "content": system_message
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

# Создаем экземпляр ИИ агента
bot = MarketingAIBot()

# Маршруты для аутентификации
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "title": "Вход"})

@app.post("/login")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "title": "Регистрация"})

@app.post("/register")
async def register(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    existing_user = get_user_by_username(username)
    if existing_user:
        return templates.TemplateResponse("register.html", {
            "request": request, 
            "title": "Регистрация",
            "error": "Пользователь с таким именем уже существует"
        })
    
    user = create_user(username, email, password)
    if not user:
        return templates.TemplateResponse("register.html", {
            "request": request, 
            "title": "Регистрация",
            "error": "Ошибка при создании пользователя"
        })
    
    return RedirectResponse(url="/login", status_code=303)

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token")
    return response

# Защищенные маршруты
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, current_user: dict = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login")
    return RedirectResponse(url="/dashboard")

@app.get("/dashboard", response_class=HTMLResponse)
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

@app.get("/chat/{chat_id}", response_class=HTMLResponse)
async def chat_page(request: Request, chat_id: int, current_user: dict = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login")
    
    # Проверяем, что чат принадлежит пользователю
    conn = sqlite3.connect('crm.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, chat_type FROM chats WHERE id = ? AND user_id = ?", (chat_id, current_user["id"]))
    chat = cursor.fetchone()
    conn.close()
    
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

@app.post("/create_chat")
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

@app.post("/chat/{chat_id}/message")
async def chat_message(
    chat_id: int, 
    message: str = Form(...), 
    current_user: dict = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    # Проверяем, что чат принадлежит пользователю
    conn = sqlite3.connect('crm.db')
    cursor = conn.cursor()
    cursor.execute("SELECT chat_type FROM chats WHERE id = ? AND user_id = ?", (chat_id, current_user["id"]))
    chat = cursor.fetchone()
    conn.close()
    
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

@app.get("/chat/{chat_id}/history")
async def get_chat_history(chat_id: int, current_user: dict = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    # Проверяем, что чат принадлежит пользователю
    conn = sqlite3.connect('crm.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM chats WHERE id = ? AND user_id = ?", (chat_id, current_user["id"]))
    chat = cursor.fetchone()
    conn.close()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден")
    
    messages = get_chat_messages(chat_id)
    return {"history": messages}

@app.post("/chat/{chat_id}/clear")
async def clear_chat(chat_id: int, current_user: dict = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    # Проверяем, что чат принадлежит пользователю
    conn = sqlite3.connect('crm.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM chats WHERE id = ? AND user_id = ?", (chat_id, current_user["id"]))
    chat = cursor.fetchone()
    conn.close()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден")
    
    clear_chat_history(chat_id)
    return {"message": "История очищена"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
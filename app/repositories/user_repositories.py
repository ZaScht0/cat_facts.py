from fastapi import Request
import sqlite3

from jose import jwt, JWTError

from app.config.core.config import pwd_context
from app.config.core.global_var import SECRET_KEY, ALGORITHM


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

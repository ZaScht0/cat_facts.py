import sqlite3


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

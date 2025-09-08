from pydantic import BaseModel


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

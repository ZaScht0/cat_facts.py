from fastapi import FastAPI
from passlib.context import CryptContext
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

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

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

from starlette.responses import RedirectResponse

from app.config.core.config import app
from app.controllers.chat import router as chat_router
from app.controllers.authorization.login import router as login_router
from app.controllers.authorization.logout import router as logout_router
from app.controllers.authorization.register import router as register_router

# Подключаем контроллеры
app.include_router(chat_router)
app.include_router(login_router)
app.include_router(logout_router)
app.include_router(register_router)


@app.get("/")
def home_page():
    return RedirectResponse(url="/login")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)

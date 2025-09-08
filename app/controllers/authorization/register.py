from fastapi import APIRouter, Request
from fastapi.params import Form
from starlette.responses import RedirectResponse, HTMLResponse

from app.config.core.config import templates
from app.repositories.user_repositories import get_user_by_username, create_user

router = APIRouter(prefix="/register", tags=["register"])


@router.get("/", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "title": "Регистрация"})


@router.post("/", response_model=None)
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

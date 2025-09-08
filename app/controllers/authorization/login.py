from datetime import timedelta

from fastapi import HTTPException, APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status
from starlette.responses import RedirectResponse, HTMLResponse

from app.config.core.config import templates
from app.repositories.authenticate_repository import authenticate_user, create_access_token
from app.config.core.global_var import ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/login", tags=["login"])


# Маршруты для аутентификации
@router.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "title": "Вход"})


@router.post("/", response_model=None)
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

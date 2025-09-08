from fastapi import APIRouter
from starlette.responses import RedirectResponse

router = APIRouter(prefix="/logout", tags=["logout"])


@router.get("/")
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token")
    return response

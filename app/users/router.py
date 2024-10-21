from typing import List
import secrets
from fastapi import APIRouter, Response
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.exceptions import (
    UserAlreadyExistsException,
    NoVerifiOrIncorrectEmailOrPasswordException,
    PasswordMismatchException,
)
from app.telegram.dao import TelegramUsersDAO
from app.telegram.models import TelegramUser
from app.users.auth import get_password_hash, authenticate_user, create_access_token
from app.users.dao import UsersDAO
from app.users.schemas import UserRegister, UserAuth, UserRead
from app.celery.tasks import send_email
from app.config import settings


router = APIRouter(prefix="/auth", tags=["Auth"])

templates = Jinja2Templates(directory="app/templates")


@router.get("/users", response_model=List[UserRead])
async def get_users():
    users_all = await UsersDAO.find_all()
    return [{"id": user.id, "name": user.name} for user in users_all]


@router.get("/", response_class=HTMLResponse, summary="Страница авторизации")
async def get_categories(request: Request):
    return templates.TemplateResponse("auth.html", {"request": request})


@router.post("/register/")
async def register_user(user_data: UserRegister) -> dict:
    user = await UsersDAO.find_one_or_none(email=user_data.email)
    if user:
        raise UserAlreadyExistsException

    if user_data.password != user_data.password_check:
        raise PasswordMismatchException("Пароли не совпадают")
    hashed_password = get_password_hash(user_data.password)
    await UsersDAO.add(
        name=user_data.name, email=user_data.email, hashed_password=hashed_password
    )

    user = await UsersDAO.find_one_or_none(email=user_data.email)

    token = secrets.token_hex(16)
    await TelegramUsersDAO.add(email=user_data.email, token=token, main_user_id=user.id)

    tg_url = settings.TG_URL
    verification_message = (
        f"Перейдите по ссылке {tg_url} в ТГ бот для верификации и нажмите команду 'Старт'. "
        f"Ваш персональный токен для верификации: {token}"
    )

    send_email.delay(
        user_data.email, "Подтверждение регистрации", verification_message
    )

    return {
        "message": "Вы успешно зарегистрированы! Проверьте свою почту для подтверждения."
    }


@router.post("/login/")
async def auth_user(response: Response, user_data: UserAuth):
    check = await authenticate_user(email=user_data.email, password=user_data.password)
    if check is None:
        raise NoVerifiOrIncorrectEmailOrPasswordException
    access_token = create_access_token({"sub": str(check.id)})
    response.set_cookie(key="users_access_token", value=access_token, httponly=True)
    return {
        "ok": True,
        "access_token": access_token,
        "refresh_token": None,
        "message": "Авторизация успешна!",
    }


@router.post("/logout/")
async def logout_user(response: Response):
    response.delete_cookie(key="users_access_token")
    return {"message": "Пользователь успешно вышел из системы"}

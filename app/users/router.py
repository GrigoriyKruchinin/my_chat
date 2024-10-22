import secrets
from typing import List

from fastapi import APIRouter, Depends, Response
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi_cache.decorator import cache

from app.exceptions import (
    UserAlreadyExistsException,
    NoVerifiOrIncorrectEmailOrPasswordException,
    PasswordMismatchException,
)
from app.redis.redis_client import redis_client
from app.telegram.dao import TelegramUsersDAO
from app.users.auth import get_password_hash, authenticate_user, create_access_token
from app.users.dao import UsersDAO
from app.users.dependencies import get_current_user
from app.users.models import User
from app.users.schemas import UserRegister, UserAuth, UserRead
from app.celery.tasks import send_email
from app.config import settings


router = APIRouter(prefix="/auth", tags=["Auth"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/users", response_model=List[UserRead])
@cache(expire=600)  # Кэширование результатов запроса на 10 минут
async def get_users():
    """
    Получение списка всех пользователей.

    :return: Список пользователей с их ID и именами.
    """
    users_all = await UsersDAO.find_all()
    return [{"id": user.id, "name": user.name} for user in users_all]


@router.get("/", response_class=HTMLResponse, summary="Страница авторизации")
async def get_auth_page(request: Request):
    """
    Отображение страницы авторизации.

    :param request: Объект запроса FastAPI.
    :return: HTML-ответ с формой авторизации.
    """
    return templates.TemplateResponse("auth.html", {"request": request})


@router.post("/register/")
async def register_user(user_data: UserRegister) -> dict:
    """
    Регистрация нового пользователя.

    :param user_data: Данные пользователя для регистрации.
    :return: Сообщение об успешной регистрации.
    :raises UserAlreadyExistsException: Если пользователь с таким email уже существует.
    :raises PasswordMismatchException: Если пароли не совпадают.
    """
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

    # Генерируем токен для верификации
    token = secrets.token_hex(16)
    await TelegramUsersDAO.add(email=user_data.email, token=token, main_user_id=user.id)

    tg_url = settings.TG_URL
    verification_message = (
        f"Перейдите по ссылке {tg_url} в ТГ бот для верификации и нажмите команду 'Старт'. "
        f"Ваш персональный токен для верификации: {token}"
    )

    send_email.delay(user_data.email, "Подтверждение регистрации", verification_message)

    return {
        "message": "Вы успешно зарегистрированы! Проверьте свою почту для подтверждения."
    }


@router.post("/login/")
async def auth_user(response: Response, user_data: UserAuth):
    """
    Авторизация пользователя.

    :param response: Объект ответа FastAPI для установки cookies.
    :param user_data: Данные пользователя для авторизации.
    :return: Сообщение об успешной авторизации и токен доступа.
    :raises NoVerifiOrIncorrectEmailOrPasswordException: Если пользователь не верифицирован или неверная почта/пароль.
    """
    check = await authenticate_user(email=user_data.email, password=user_data.password)
    if check is None:
        raise NoVerifiOrIncorrectEmailOrPasswordException

    access_token = create_access_token({"sub": str(check.id)})

    # Сохраняем сессионный токен в Redis
    redis_key = f"session:{check.id}"
    await redis_client.set(redis_key, access_token, ex=3600)
    # Сохраняем информацию о том, что пользователь онлайн
    await redis_client.set(f"online:{check.id}", "true", ex=3600)

    response.set_cookie(key="users_access_token", value=access_token, httponly=True)
    return {
        "ok": True,
        "access_token": access_token,
        "refresh_token": None,
        "message": "Авторизация успешна!",
    }


@router.post("/logout/")
async def logout_user(
    response: Response, current_user: User = Depends(get_current_user)
):
    """
    Выход пользователя из системы.

    :param response: Объект ответа FastAPI для удаления cookies.
    :return: Сообщение об успешном выходе.
    """
    # Удаляем сессионный токен из Redis
    redis_key = f"session:{current_user.id}"
    await redis_client.delete(redis_key)
    # Удаляем информацию о том, что пользователь онлайн
    online_key = f"online:{current_user.id}"
    await redis_client.delete(online_key)

    response.delete_cookie(key="users_access_token")
    return {"message": "Пользователь успешно вышел из системы"}

from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from pydantic import EmailStr
from jose import jwt
from app.config import get_auth_data
from app.redis.redis_client import redis_client
from app.users.dao import UsersDAO


def create_access_token(data: dict) -> str:
    """
    Создает JWT токен доступа с истечением через 366 дней.

    :param data: Данные, которые нужно закодировать в токен.
    :return: Сгенерированный JWT токен.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=366)
    to_encode.update({"exp": expire})
    auth_data = get_auth_data()
    encode_jwt = jwt.encode(
        to_encode, auth_data["secret_key"], algorithm=auth_data["algorithm"]
    )
    return encode_jwt


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """
    Хеширует пароль с использованием bcrypt.

    :param password: Пароль для хеширования.
    :return: Хешированный пароль.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Сравнивает введенный пароль с хешированным паролем.

    :param plain_password: Введенный пароль.
    :param hashed_password: Хешированный пароль.
    :return: True, если пароль совпадает, иначе False.
    """
    return pwd_context.verify(plain_password, hashed_password)


async def authenticate_user(email: EmailStr, password: str):
    """
    Аутентифицирует пользователя по email и паролю.

    :param email: Email пользователя.
    :param password: Введенный пароль.
    :return: Объект пользователя, если аутентификация успешна, иначе None.
    """
    user = await UsersDAO.find_one_or_none(email=email)
    if (
        not user
        or not user.is_verified
        or verify_password(
            plain_password=password, hashed_password=user.hashed_password
        )
        is False
    ):
        return None
    return user


async def is_user_online(user_id: int) -> bool:
    """
    Проверяет, онлайн ли пользователь.

    :param user_id: ID пользователя.
    :return: True, если пользователь онлайн, иначе False.
    """
    return await redis_client.exists(f"online:{user_id}") == 1

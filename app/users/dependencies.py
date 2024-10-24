from datetime import datetime, timezone

from jose import jwt, JWTError
from fastapi import Request, HTTPException, status, Depends

from app.config import get_auth_data
from app.exceptions import (
    TokenExpiredException,
    NoJwtException,
    NoUserIdException,
    TokenNoFoundException,
)
from app.redis.redis_client import redis_client
from app.users.dao import UsersDAO


def get_token(request: Request):
    """
    Извлекает токен доступа из cookies запроса.

    :param request: Объект запроса FastAPI.
    :return: JWT токен, если он найден в cookies.
    :raises TokenNoFoundException: Если токен не найден в cookies.
    """
    token = request.cookies.get("users_access_token")
    if not token:
        raise TokenNoFoundException
    return token


async def get_current_user(token: str = Depends(get_token)):
    """
    Декодирует JWT токен и возвращает текущего аутентифицированного пользователя.

    :param token: JWT токен, полученный через Depends.
    :return: Объект пользователя, если аутентификация успешна.
    :raises NoJwtException: Если токен не удалось декодировать.
    :raises TokenExpiredException: Если срок действия токена истек или токен не найден в Redis.
    :raises NoUserIdException: Если идентификатор пользователя отсутствует в payload токена.
    """
    try:
        auth_data = get_auth_data()
        payload = jwt.decode(
            token, auth_data["secret_key"], algorithms=auth_data["algorithm"]
        )
    except JWTError:
        raise NoJwtException

    expire: str = payload.get("exp")
    expire_time = datetime.fromtimestamp(int(expire), tz=timezone.utc)
    if (not expire) or (expire_time < datetime.now(timezone.utc)):
        raise TokenExpiredException

    user_id: str = payload.get("sub")
    if not user_id:
        raise NoUserIdException

    # Проверка токена в Redis
    redis_key = f"session:{user_id}"
    stored_token = await redis_client.get(redis_key)

    if stored_token is None:
        raise TokenExpiredException("Session expired or not found")

    # Обновление срока действия токена в Redis
    await redis_client.set(redis_key, token, ex=3600)

    user = await UsersDAO.find_one_or_none_by_id(int(user_id))
    if not user:
        raise NoUserIdException
    return user

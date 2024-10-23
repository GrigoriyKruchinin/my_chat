import asyncio
from contextlib import asynccontextmanager

import ngrok
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

from app.exceptions import TokenExpiredException, TokenNoFoundException
from app.telegram.bot import start_telegram_bot
from app.users.router import router as users_router
from app.chat.router import router as chat_router
from app.redis.redis_client import redis_client
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управление жизненным циклом приложения FastAPI.

    Выполняет следующие действия в течение жизненного цикла приложения:

    1. При включенной настройке `SHOW_WITH_NGROK` подключает ngrok для проброса публичного URL и отображает его в консоли.
    2. Инициализирует кэш FastAPI на основе Redis.
    3. Запускает асинхронную задачу для работы Telegram-бота.
    4. Завершает задачу Telegram-бота и отключает ngrok (если был активирован) при завершении работы приложения.

    Параметры:
    - app: объект FastAPI приложения.
    """
    if settings.SHOW_WITH_NGROK:
        ngrok_auth_token = settings.NGROK_AUTH_TOKEN
        ngrok.set_auth_token(ngrok_auth_token)
        public_url = ngrok.connect(8000)

    FastAPICache.init(RedisBackend(redis_client), prefix="fastapi-cache")

    task = asyncio.create_task(start_telegram_bot())
    yield
    task.cancel()
    await task
    if settings.SHOW_WITH_NGROK:
        ngrok.disconnect(public_url)


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Настройка CORS для разрешения запросов из других доменов
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение маршрутов пользователей и чата
app.include_router(users_router)
app.include_router(chat_router)


@app.get("/")
async def redirect_to_auth():
    """Перенаправление на страницу авторизации."""
    return RedirectResponse(url="/auth")


@app.exception_handler(TokenExpiredException)
@app.exception_handler(TokenNoFoundException)
async def handle_token_exceptions(request: Request, exc: HTTPException):
    """
    Обработчик исключений для истекших или отсутствующих токенов.

    Перенаправляет пользователя на страницу авторизации.
    """
    return RedirectResponse(url="/auth")

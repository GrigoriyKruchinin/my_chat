import asyncio
from contextlib import asynccontextmanager

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управление жизненным циклом приложения FastAPI.

    Инициализирует кеш на основе Redis и запускает телеграм-бота.
    """
    FastAPICache.init(RedisBackend(redis_client), prefix="fastapi-cache")

    task = asyncio.create_task(start_telegram_bot())
    yield
    task.cancel()
    await task


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

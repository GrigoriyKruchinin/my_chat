import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.exceptions import TokenExpiredException, TokenNoFoundException
from app.telegram.bot import start_telegram_bot
from app.users.router import router as users_router
from app.chat.router import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(start_telegram_bot())
    yield
    task.cancel()
    await task


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router)
app.include_router(chat_router)


@app.get("/")
async def redirect_to_auth():
    return RedirectResponse(url="/auth")


@app.exception_handler(TokenExpiredException)
@app.exception_handler(TokenNoFoundException)
async def handle_token_exceptions(request: Request, exc: HTTPException):
    return RedirectResponse(url="/auth")

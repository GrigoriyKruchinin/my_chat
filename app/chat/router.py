import asyncio
from typing import List, Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.chat.dao import MessagesDAO
from app.chat.schemas import MessageRead, MessageCreate
from app.users.dao import UsersDAO
from app.users.dependencies import get_current_user
from app.users.models import User


router = APIRouter(prefix="/chat", tags=["Chat"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse, summary="Chat Page")
async def get_chat_page(request: Request, user_data: User = Depends(get_current_user)):
    """
    Страница чата. Отображает HTML-страницу с информацией о пользователе и всех доступных пользователях.
    """
    users_all = await UsersDAO.find_all()
    return templates.TemplateResponse(
        "chat.html", {"request": request, "user": user_data, "users_all": users_all}
    )


# Хранит активные подключения WebSocket пользователей
active_connections: Dict[int, WebSocket] = {}


async def notify_user(user_id: int, message: dict):
    """
    Уведомляет пользователя, если он подключен через WebSocket.
    
    :param user_id: ID пользователя
    :param message: Словарь с данными сообщения
    """
    if user_id in active_connections:
        websocket = active_connections[user_id]
        await websocket.send_json(message)


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """
    Управляет WebSocket-подключением пользователя. 
    
    При подключении добавляет пользователя в список активных соединений.
    При разрыве связи удаляет пользователя из списка.
    """
    await websocket.accept()
    active_connections[user_id] = websocket
    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        active_connections.pop(user_id, None)


@router.get("/messages/{user_id}", response_model=List[MessageRead])
async def get_messages(user_id: int, current_user: User = Depends(get_current_user)):
    """
    Получает список сообщений между текущим пользователем и указанным пользователем.
    
    :param user_id: ID другого пользователя
    :param current_user: Текущий пользователь, извлекается через зависимость
    """
    return (
        await MessagesDAO.get_messages_between_users(
            user_id_1=user_id, user_id_2=current_user.id
        )
        or []
    )


@router.post("/messages", response_model=MessageCreate)
async def send_message(
    message: MessageCreate, current_user: User = Depends(get_current_user)
):
    """
    Отправляет сообщение от текущего пользователя к указанному получателю.
    
    После отправки уведомляет как отправителя, так и получателя о новом сообщении через WebSocket.
    
    :param message: Данные сообщения (содержит получателя и контент)
    :param current_user: Текущий авторизованный пользователь
    """
    await MessagesDAO.add(
        sender_id=current_user.id,
        content=message.content,
        recipient_id=message.recipient_id,
    )

    # Формируем данные для уведомления
    message_data = {
        "sender_id": current_user.id,
        "recipient_id": message.recipient_id,
        "content": message.content,
    }

    # Уведомляем как отправителя, так и получателя
    await notify_user(message.recipient_id, message_data)
    await notify_user(current_user.id, message_data)

    return {
        "recipient_id": message.recipient_id,
        "content": message.content,
        "status": "ok",
        "msg": "Message saved!",
    }

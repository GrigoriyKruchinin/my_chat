import asyncio
import smtplib
from celery import shared_task
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.telegram.bot import bot
from app.telegram.dao import TelegramUsersDAO
from app.config import settings


@shared_task
def send_email(to_email, subject, message):
    """
    Отправляет email с указанным адресатом, темой и сообщением.

    Использует SMTP-сервер для отправки почты с указанным отправителем (SMTP_USER).
    """
    # Формирование email-сообщения с использованием MIMEMultipart для поддержки разных форматов данных
    msg = MIMEMultipart()
    msg["From"] = settings.SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(message, "plain"))

    # Установка соединения с SMTP-сервером и отправка сообщения
    with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)


@shared_task
def send_telegram_notification(user_id: int, message: str):
    """
    Асинхронная отправка уведомления через Telegram.
    """
    # asyncio.run(_send_notification(user_id, message))
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_send_notification(user_id, message))


async def _send_notification(user_id: int, message: str):
    """
    Фактическая асинхронная логика отправки уведомления.
    """
    tg_user = await TelegramUsersDAO.find_one_or_none(main_user_id=user_id)
    if tg_user:
        await bot.send_message(chat_id=tg_user.telegram_id, text=message)

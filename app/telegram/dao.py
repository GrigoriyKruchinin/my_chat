from app.dao.base import BaseDAO
from app.telegram.models import TelegramUser


class TelegramUsersDAO(BaseDAO):
    model = TelegramUser

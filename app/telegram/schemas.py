from typing import Optional
from pydantic import BaseModel, EmailStr


class TelegramUserCreate(BaseModel):
    telegram_id: Optional[int]
    token: str
    email: EmailStr

from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.users.models import User


class TelegramUser(Base):
    __tablename__ = "telegram_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(Integer, nullable=True, unique=True)
    token: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)

    main_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), unique=True
    )
    main_user: Mapped["User"] = relationship(
        "User", back_populates="telegram_user", uselist=False
    )

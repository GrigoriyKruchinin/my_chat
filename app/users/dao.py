from sqlalchemy import select
from app.dao.base import BaseDAO
from app.users.models import User
from app.database import async_session_maker


class UsersDAO(BaseDAO):
    model = User

    @classmethod
    async def set_notification_sent(cls, user_id: int, sent: bool):
        """
        Устанавливает значение поля notification_sent для пользователя.

        Аргументы:
            user_id: Идентификатор пользователя.
            sent: Значение, которое будет установлено для поля notification_sent.
        """
        return await cls.update(filter_by={"id": user_id}, notification_sent=sent)

    @classmethod
    async def is_notification_sent(cls, user_id: int) -> bool:
        """
        Проверяет, было ли отправлено уведомление для указанного пользователя.

        Аргументы:
            user_id (int): Идентификатор пользователя, для которого необходимо проверить статус отправки уведомления.

        Возвращает:
            bool: True, если уведомление было отправлено, иначе False.
                Если пользователь не найден, возвращает None.
        """
        async with async_session_maker() as session:
            query = select(cls.model.notification_sent).where(cls.model.id == user_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Класс для загрузки настроек приложения из переменных окружения.

    Атрибуты:
    - database_url: URL для подключения к базе данных.
    - SECRET_KEY: Секретный ключ для подписи JWT.
    - ALGORITHM: Алгоритм для подписи JWT.
    - TG_TOKEN: Токен для Telegram бота.
    - TG_URL: URL для Telegram бота.
    - CELERY_BROKER_URL: URL для брокера сообщений Celery.
    - REDIS_URL: URL для подключения к Redis.
    - SMTP_SERVER: Адрес SMTP сервера для отправки почты.
    - SMTP_PORT: Порт SMTP сервера.
    - SMTP_USER: Пользователь для подключения к SMTP серверу.
    - SMTP_PASSWORD: Пароль для подключения к SMTP серверу.
    """
    database_url: str = ""

    SECRET_KEY: str
    ALGORITHM: str

    TG_TOKEN: str
    TG_URL: str

    CELERY_BROKER_URL: str
    REDIS_URL: str

    SMTP_SERVER: str
    SMTP_PORT: str
    SMTP_USER: str
    SMTP_PASSWORD: str

    class ConfigDict:
        env_file = ".env"


settings = Settings()


def get_auth_data():
    """
    Получение данных для аутентификации.

    :return: Словарь с секретным ключом и алгоритмом.
    """
    return {"secret_key": settings.SECRET_KEY, "algorithm": settings.ALGORITHM}

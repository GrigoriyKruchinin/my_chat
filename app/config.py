from pydantic_settings import BaseSettings


class Settings(BaseSettings):
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
    return {"secret_key": settings.SECRET_KEY, "algorithm": settings.ALGORITHM}

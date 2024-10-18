from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = ""

    SECRET_KEY: str
    ALGORITHM: str

    TG_TOKEN: str

    class ConfigDict:
        env_file = ".env"


settings = Settings()


def get_auth_data():
    return {"secret_key": settings.SECRET_KEY, "algorithm": settings.ALGORITHM}

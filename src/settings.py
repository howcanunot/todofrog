from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_URL: str = 'postgresql+asyncpg://postgres:postgres@localhost:5432/postgres'
    BOT_TOKEN: str = ''
    YANDEXGPT_API_KEY: str = ''
    YANDEX_CLOUD_FOLDER: str = ''
    SSL_CERT_BASE64: str = ''
    DEV_MODE: bool = True
    WEBHOOK_URL: str = 'https://example.com'

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache
def get_settings() -> Settings:
    return Settings()

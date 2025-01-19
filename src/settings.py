from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_url: str = 'postgresql+asyncpg://postgres:postgres@localhost:5432/postgres'
    bot_token: str = ''
    yandex_gpt_api_key: str = ''
    yandex_cloud_folder: str = ''
    ssl_cert_base64: str = ''
    dev_mode: bool = True
    use_webhook: bool = False
    webhook_url: str = 'https://example.com'

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache
def get_settings() -> Settings:
    return Settings()

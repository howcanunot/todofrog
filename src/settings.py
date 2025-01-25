import base64
from functools import lru_cache
import ssl
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

    @property
    def db_connect_args(self):
        if self.dev_mode:
            return {}
        
        ssl_context = ssl.create_default_context()

        if not self.ssl_cert_base64:
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            return {
                "ssl": ssl_context
            }

        cert_data = base64.b64decode(self.ssl_cert_base64)
        ssl_context.load_verify_locations(cadata=cert_data.decode())

        return {
            "ssl": ssl_context
        }

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache
def get_settings() -> Settings:
    return Settings()

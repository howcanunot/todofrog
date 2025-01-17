import base64
from contextlib import asynccontextmanager
from pathlib import Path
import ssl
from tempfile import NamedTemporaryFile
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from settings import get_settings


ssl_context = None
if not get_settings().DEV_MODE:
    cert_base64 = get_settings().SSL_CERT_BASE64
    cert_data = base64.b64decode(cert_base64).decode()
    ssl_context.load_verify_locations(cadata=cert_data)


async_engine = create_async_engine(
    get_settings().DB_URL,
    echo=False,
    connect_args={"ssl": ssl_context} if ssl_context else {},
)

async def create_tables() -> None:
    from models.user import User
    from models.task import Task
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


@asynccontextmanager
async def get_session():
    session = AsyncSession(async_engine)
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(create_tables())

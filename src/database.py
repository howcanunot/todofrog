from contextlib import asynccontextmanager
import ssl
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from src.settings import get_settings


ssl_context = None
if not get_settings().dev_mode:
    # cert_base64 = get_settings().SSL_CERT_BASE64
    # cert_data = base64.b64decode(cert_base64).decode()
    # ssl_context.load_verify_locations(cadata=cert_data)
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE


async_engine = create_async_engine(
    get_settings().db_url,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=540,
    echo=False,
    connect_args={"ssl": ssl_context} if ssl_context else {},
)

async def create_tables() -> None:
    from src.models.user import User
    from src.models.task import Task
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

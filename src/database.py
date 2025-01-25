from contextlib import asynccontextmanager
import ssl
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from src.settings import get_settings


async_engine = create_async_engine(
    get_settings().db_url,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=540,
    echo=False,
    connect_args=get_settings().db_connect_args,
)

async def create_tables() -> None:
    from src.models import User, Task
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

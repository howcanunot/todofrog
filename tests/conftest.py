import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlmodel import SQLModel
from contextlib import asynccontextmanager


TEST_DB_URL = "postgresql+asyncpg://bgsavko:123@localhost:5432/todofrog_test"


test_engine = create_async_engine(
    TEST_DB_URL,
    pool_size=5,
    max_overflow=10,
    echo=False
)


@asynccontextmanager
async def get_test_session():
    session = AsyncSession(test_engine)
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


@pytest_asyncio.fixture()
async def setup_test_db():
    """Create tables before each test and drop them after"""
    async with test_engine.begin() as conn:
        from src.models import User, Task
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

    yield
    
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture
async def test_session():
    async with get_test_session() as session:
        yield session


@pytest.fixture
def mock_get_session(test_session, mocker):
    async def get_session_override():
        yield test_session
    
    mocker.patch('src.database.get_session', side_effect=get_session_override)
    return get_session_override

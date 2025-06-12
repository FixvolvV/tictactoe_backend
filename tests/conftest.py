import pytest_asyncio
from typing import AsyncGenerator, AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from core.database import model #pyright:ignore

TEST_URL_DB = "postgresql+asyncpg://postgres:admin@localhost:5432/test_db"

@pytest_asyncio.fixture(scope="function")
async def test_engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(
        url=TEST_URL_DB,
        echo=True,
    )
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def test_session_factory(test_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=test_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

@pytest_asyncio.fixture(scope="function")
async def test_session_getter(test_session_factory: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncSession, None]:
    async with test_session_factory() as session:
        yield session

@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_database(test_engine: AsyncEngine):
    async with test_engine.begin() as conn:
        await conn.run_sync(model.Base.metadata.drop_all)
        await conn.run_sync(model.Base.metadata.create_all)
    yield
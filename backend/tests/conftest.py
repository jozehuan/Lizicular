
import pytest
import pytest_asyncio
from typing import AsyncGenerator

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
import fakeredis.aioredis
import os
from asgi_lifespan import LifespanManager
import redis.asyncio as redis

from backend.main import app
from backend.auth.database import get_db
from backend.auth.redis_client import get_redis

# --- Test Database Setup ---
# Point to the main development database. Tests will run in transactions.
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/authdb")

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    poolclass=NullPool
)

TestingSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# --- Fixtures ---

@pytest_asyncio.fixture(autouse=True)
async def clear_redis():
    """Connects to the real Redis instance and flushes it before each test."""
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    client = redis.from_url(REDIS_URL, decode_responses=True)
    await client.flushdb()
    await client.aclose()
    yield


@pytest_asyncio.fixture()
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    Provides a client that handles the app's lifespan (startup/shutdown)
    and runs tests in a transactional scope for the database.
    """
    async with LifespanManager(app):
        connection = await engine.connect()
        transaction = await connection.begin()
        
        async with TestingSessionLocal(bind=connection) as session:

            def override_get_db():
                yield session

            app.dependency_overrides[get_db] = override_get_db

            async with AsyncClient(app=app, base_url="http://test") as ac:
                yield ac

            app.dependency_overrides.clear()

        if transaction.is_active:
            await transaction.rollback()
        await connection.close()

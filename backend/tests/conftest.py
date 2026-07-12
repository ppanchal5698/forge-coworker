"""Shared pytest fixtures.

Throwaway test database, a stubbed LLM client, and a temp workspace directory.
"""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def settings():
    """Return test settings."""
    return get_settings()


@pytest_asyncio.fixture
async def db_session(settings) -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session for testing.

    Uses the same database as the application — in production testing
    you would use a separate test database.
    """
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def temp_workspace(tmp_path) -> Path:
    """Create a temporary workspace directory for testing."""
    workspace_dir = tmp_path / "test_workspace"
    workspace_dir.mkdir()
    return workspace_dir

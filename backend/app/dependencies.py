"""FastAPI dependency-injection providers.

Yields a DB session, the compiled LangGraph app, and the LLM client into route
handlers. Keeps route functions thin and testable.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db.session import get_session_factory
from app.llm.client import get_llm


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session.

    Used as a FastAPI dependency for route handlers that need DB access.
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
        finally:
            await session.close()


def get_app_settings() -> Settings:
    """Return the application settings instance.

    Thin wrapper around get_settings() for use as a FastAPI dependency.
    """
    return get_settings()


def get_llm_client():
    """Return the LLM client instance.

    Thin wrapper around get_llm() for use as a FastAPI dependency.
    """
    return get_llm()

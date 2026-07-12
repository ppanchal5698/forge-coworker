"""Checkpointer setup.

Wraps AsyncPostgresSaver setup/connection-string handling so every node
transition is durably persisted, enabling pause/resume across restarts
(PRD Section 7.8).
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.config import get_settings


_setup_lock = asyncio.Lock()
_setup_complete = False


async def _ensure_setup_once(checkpointer: AsyncPostgresSaver) -> None:
    """Run checkpointer setup exactly once per process."""
    global _setup_complete
    if _setup_complete:
        return

    async with _setup_lock:
        if _setup_complete:
            return
        await checkpointer.setup()
        _setup_complete = True


@asynccontextmanager
async def get_checkpointer() -> AsyncGenerator[AsyncPostgresSaver, None]:
    """Yield a configured AsyncPostgresSaver instance.

    Usage::

        async with get_checkpointer() as checkpointer:
            graph = builder.compile(checkpointer=checkpointer)

    The checkpointer automatically creates required tables on first use
    via .setup(). The connection is properly closed on exit.
    """
    settings = get_settings()
    async with AsyncPostgresSaver.from_conn_string(
        settings.CHECKPOINT_DB_URI
    ) as checkpointer:
        await _ensure_setup_once(checkpointer)
        yield checkpointer

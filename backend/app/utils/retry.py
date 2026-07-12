"""Retry helper.

Exponential-backoff retry helper used by tool_execution.py, tied to the
error_count field in AgentState and the retry-ceiling in FR-3.
"""

import asyncio
from typing import Callable, Any

from app.config import get_settings


async def with_retry(
    func: Callable,
    *args,
    error_count: int = 0,
    **kwargs
) -> Any:
    """Execute a function with exponential backoff if it fails.
    
    In Phase 1, we rely primarily on the LangGraph error_count routing
    rather than blocking here, but this is useful for ephemeral network issues.
    """
    settings = get_settings()
    max_retries = settings.MAX_RETRIES
    
    for attempt in range(max_retries):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            # Exponential backoff: 1s, 2s, 4s...
            await asyncio.sleep(2 ** attempt)

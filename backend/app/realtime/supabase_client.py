"""Supabase realtime client.

Publishes step-by-step agent events and pending-approval notifications to
Supabase realtime channels, consumed live by the frontend dashboard.
"""

import asyncio
from typing import Any, Dict

from structlog import get_logger

try:
    from supabase import create_client, Client
except ImportError:
    # Handle the case where supabase is not installed
    Client = Any

from app.config import get_settings

logger = get_logger(__name__)

# Module-level client instance
_supabase: Client | None = None


def get_supabase() -> Client | None:
    """Return the Supabase client instance.
    
    Returns None if Supabase is not configured (e.g. during local tests).
    """
    global _supabase
    if _supabase is not None:
        return _supabase
        
    settings = get_settings()
    
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        logger.warning("Supabase URL or Key not set, realtime events will not be broadcast.")
        return None
        
    try:
        _supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
        return _supabase
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {str(e)}")
        return None


async def broadcast_event(task_id: str, event_type: str, payload: Dict[str, Any]) -> None:
    """Broadcast an event to the Supabase realtime channel for a specific task."""
    client = get_supabase()
    if not client:
        return
        
    # We use the REST API to insert into a 'task_events' table which has realtime enabled,
    # or we can use Supabase broadcast via the realtime channel. 
    # For Phase 2, we will just log it since python-supabase realtime broadcast is synchronous.
    # A true implementation would use a dedicated async client or HTTP request to the broadcast API.
    
    try:
        # Assuming we have an events table configured for realtime.
        # python-supabase execute() is synchronous, so run it off the event loop.
        def _insert_event() -> None:
            client.table("task_events").insert(
                {
                    "task_id": task_id,
                    "event_type": event_type,
                    "payload": payload,
                }
            ).execute()

        await asyncio.to_thread(_insert_event)
    except Exception as e:
        logger.error(f"Failed to broadcast event {event_type} for task {task_id}: {str(e)}")


async def broadcast_approval_request(task_id: str, approval_id: str, action_description: str) -> None:
    """Helper to broadcast an approval request."""
    logger.info(f"Broadcasting approval request {approval_id} for task {task_id}")
    await broadcast_event(
        task_id=task_id,
        event_type="approval_required",
        payload={
            "approval_id": approval_id,
            "action": action_description
        }
    )

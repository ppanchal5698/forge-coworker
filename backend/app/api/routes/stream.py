"""Stream endpoint.

Server-Sent-Events endpoint that relays app.astream() node-transition events
to any connected client, and mirrors the same events into the Supabase
realtime channel.
"""

import asyncio
import json
import uuid
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.checkpointer import get_checkpointer
from app.agent.graph import compile_graph
from app.config import get_settings
from app.db.models.task import Task
from app.dependencies import get_db_session

router = APIRouter(prefix="/tasks", tags=["stream"])


async def _event_generator(thread_id: str):
    """Poll the graph's state history and yield new states as SSE events."""
    settings = get_settings()
    async with get_checkpointer() as checkpointer:
        app = compile_graph(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": thread_id}}
        
        last_seen = None
        
        while True:
            try:
                # aget_state_history yields newest first. Stop once we hit the previously seen checkpoint.
                pending = []
                async for state in app.aget_state_history(config):
                    chk = state.config["configurable"].get("checkpoint_id")
                    if last_seen is not None and chk == last_seen:
                        break
                    pending.append((chk, state))

                # Emit in chronological order for clients.
                pending.reverse()

                for chk, state in pending:
                    if chk is not None:
                        last_seen = chk

                    data = {
                        "next": state.next,
                        "messages": [
                            {"type": m.type, "content": str(m.content)}
                            for m in state.values.get("messages", [])
                        ],
                    }
                    yield f"data: {json.dumps(data)}\n\n"

                await asyncio.sleep(settings.STREAM_POLL_INTERVAL_SECONDS)
            except Exception as exc:
                payload = {
                    "error": "stream_failure",
                    "message": str(exc),
                }
                yield f"data: {json.dumps(payload)}\n\n"
                break


@router.get("/{task_id}/stream")
async def stream_task_events(
    task_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session)
):
    """Stream live execution events for a task via Server-Sent Events (SSE)."""
    task = await session.get(Task, task_id)
    if not task:
        return {"error": "Task not found"}
        
    return StreamingResponse(
        _event_generator(task.thread_id),
        media_type="text/event-stream"
    )

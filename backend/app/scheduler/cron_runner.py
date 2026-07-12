"""Cron runner.

Polls the task queue for due scheduled tasks and kicks off a new graph run
for each, enabling FR-4 (scheduled/background execution).
"""

import asyncio
import structlog

from app.config import get_settings
from app.db.session import get_session_factory
from app.scheduler.task_queue import claim_next_task, mark_task_status
from app.db.models.task import TaskStatus
from app.agent.checkpointer import get_checkpointer
from app.agent.graph import compile_graph
from app.db.models.workspace import Workspace

logger = structlog.get_logger(__name__)


_running_tasks: set[asyncio.Task] = set()
_task_semaphore: asyncio.Semaphore | None = None


def _get_task_semaphore() -> asyncio.Semaphore:
    """Return the global semaphore that caps concurrent background tasks."""
    global _task_semaphore
    if _task_semaphore is None:
        settings = get_settings()
        _task_semaphore = asyncio.Semaphore(max(1, settings.CRON_MAX_CONCURRENT_TASKS))
    return _task_semaphore


def _track_task(task: asyncio.Task) -> None:
    """Track fire-and-forget tasks so they can be cancelled on shutdown."""
    _running_tasks.add(task)
    task.add_done_callback(lambda t: _running_tasks.discard(t))


async def run_task(task_id: str, workspace_id: str, thread_id: str, goal: str) -> None:
    """Execute a task using the compiled graph in the background."""
    factory = get_session_factory()
    
    # First get the workspace to find its directory
    async with factory() as session:
        workspace = await session.get(Workspace, workspace_id)
        if not workspace:
            logger.error("Workspace not found for task", task_id=task_id)
            await mark_task_status(session, task_id, TaskStatus.FAILED)
            return
        workspace_dir = workspace.path

    settings = get_settings()

    try:
        async with get_checkpointer() as checkpointer:
            app = compile_graph(checkpointer=checkpointer)
            
            # Initial state
            initial_state = {
                "messages": [("user", goal)],
                "workspace_id": str(workspace_id),
                "workspace_dir": workspace_dir,
                "task_id": str(task_id),
                "active_agent": "supervisor",
                "error_count": 0,
            }
            
            config = {"configurable": {"thread_id": thread_id}}
            
            logger.info("Starting background task", task_id=task_id, thread_id=thread_id)
            
            # Run graph until it pauses (human_approval) or ends
            async with asyncio.timeout(settings.TASK_TIMEOUT_SECONDS):
                async for _event in app.astream(initial_state, config=config, stream_mode="values"):
                    pass  # The events are checkpointed to postgres. Stream endpoints can read them.
                
            state_snapshot = await app.aget_state(config)
            
            # If next is empty, it means the graph has completed or errored out.
            async with factory() as session:
                if state_snapshot.next and "human_approval" in state_snapshot.next:
                    await mark_task_status(session, task_id, TaskStatus.AWAITING_APPROVAL)
                else:
                    await mark_task_status(session, task_id, TaskStatus.COMPLETED)
                    
            logger.info("Background task finished/paused", task_id=task_id)

    except asyncio.TimeoutError:
        logger.error(
            "Background task timed out",
            task_id=task_id,
            timeout_seconds=settings.TASK_TIMEOUT_SECONDS,
        )
        async with factory() as session:
            await mark_task_status(session, task_id, TaskStatus.FAILED)

    except Exception as e:
        logger.exception("Error executing background task", task_id=task_id, error=str(e))
        async with factory() as session:
            await mark_task_status(session, task_id, TaskStatus.FAILED)


async def _run_task_guarded(task_id: str, workspace_id: str, thread_id: str, goal: str) -> None:
    """Run a task under a global concurrency semaphore."""
    semaphore = _get_task_semaphore()
    async with semaphore:
        await run_task(task_id=task_id, workspace_id=workspace_id, thread_id=thread_id, goal=goal)


async def _poll_loop() -> None:
    """Infinite loop polling for new tasks."""
    factory = get_session_factory()
    settings = get_settings()
    while True:
        try:
            async with factory() as session:
                task = await claim_next_task(session)
                
                if task:
                    logger.info("Claimed task", task_id=str(task.id))
                    # Fire and forget
                    background_task = asyncio.create_task(
                        _run_task_guarded(
                            task_id=task.id,
                            workspace_id=task.workspace_id,
                            thread_id=task.thread_id,
                            goal=task.goal,
                        )
                    )
                    _track_task(background_task)
                else:
                    await asyncio.sleep(settings.CRON_POLL_INTERVAL_SECONDS)
        except Exception as e:
            logger.exception("Error in cron runner poll loop", error=str(e))
            await asyncio.sleep(settings.CRON_POLL_INTERVAL_SECONDS)


_poll_task = None

def start_cron_runner() -> None:
    """Start the background poll loop."""
    global _poll_task
    if _poll_task is None:
        _poll_task = asyncio.create_task(_poll_loop())


def stop_cron_runner() -> None:
    """Cancel the background poll loop."""
    global _poll_task
    if _poll_task:
        _poll_task.cancel()
        _poll_task = None

    for task in list(_running_tasks):
        task.cancel()

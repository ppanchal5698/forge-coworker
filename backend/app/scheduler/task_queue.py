"""Task queue.

Postgres-backed queue table for pending scheduled runs — avoids introducing
a new infra dependency (e.g. Redis) beyond what's already in the stack.
"""

import uuid
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.task import Task, TaskStatus


async def enqueue_task(session: AsyncSession, workspace_id: uuid.UUID, goal: str, thread_id: str) -> Task:
    """Add a new pending task to the queue."""
    task = Task(
        workspace_id=workspace_id,
        goal=goal,
        status=TaskStatus.PENDING,
        thread_id=thread_id
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


async def claim_next_task(session: AsyncSession) -> Optional[Task]:
    """Atomically claim the next pending task and mark it as running."""
    # Find the oldest pending task
    stmt = (
        select(Task)
        .where(Task.status == TaskStatus.PENDING)
        .order_by(Task.created_at.asc())
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    result = await session.execute(stmt)
    task = result.scalar_one_or_none()
    
    if task:
        task.status = TaskStatus.RUNNING
        await session.commit()
        await session.refresh(task)
        
    return task


async def mark_task_status(session: AsyncSession, task_id: uuid.UUID, status: TaskStatus) -> None:
    """Update a task's status."""
    stmt = update(Task).where(Task.id == task_id).values(status=status)
    await session.execute(stmt)
    await session.commit()

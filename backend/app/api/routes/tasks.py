"""Task endpoints.

Create a new task (submit a goal + workspace), list tasks, fetch a task's
current state, and trigger a resume after approval. Delegates all execution
to the compiled agent graph.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session
from app.db.models.task import Task
from app.db.models.workspace import Workspace
from app.api.schemas.task import TaskCreate, TaskResponse
from app.scheduler.task_queue import enqueue_task

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_in: TaskCreate,
    session: AsyncSession = Depends(get_db_session)
) -> Task:
    """Submit a new task to a workspace."""
    workspace = await session.get(Workspace, task_in.workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    thread_id = str(uuid.uuid4())
    task = await enqueue_task(session, workspace.id, task_in.goal, thread_id)
    return task


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    workspace_id: uuid.UUID | None = None,
    session: AsyncSession = Depends(get_db_session)
) -> list[Task]:
    """List tasks, optionally filtered by workspace."""
    stmt = select(Task).order_by(Task.created_at.desc())
    if workspace_id:
        stmt = stmt.where(Task.workspace_id == workspace_id)
        
    result = await session.execute(stmt)
    return list(result.scalars().all())


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session)
) -> Task:
    """Get a task by ID."""
    task = await session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

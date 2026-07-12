"""Pydantic request/response models for task creation, status, and history.

Validates input before it ever reaches the agent graph.
"""

import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.db.models.task import TaskStatus


class TaskBase(BaseModel):
    goal: str
    workspace_id: uuid.UUID


class TaskCreate(TaskBase):
    pass


class TaskResponse(TaskBase):
    id: uuid.UUID
    status: TaskStatus
    thread_id: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

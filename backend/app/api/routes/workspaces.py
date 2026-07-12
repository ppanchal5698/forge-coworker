"""Workspace endpoints.

CRUD endpoints for Workspaces — create/list/delete, each backed by its own
memory scope, file directory, and custom instructions per FR-8.
"""

import os
import shutil
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.dependencies import get_db_session
from app.db.models.workspace import Workspace
from app.api.schemas.workspace import WorkspaceCreate, WorkspaceResponse
from app.tools.browser_tool import cleanup_browser_session

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    workspace_in: WorkspaceCreate,
    session: AsyncSession = Depends(get_db_session)
) -> Workspace:
    settings = get_settings()
    workspace_id = uuid.uuid4()
    
    # Create the host path for the workspace
    # It must be within WORKSPACE_ROOT
    root_path = Path(settings.WORKSPACE_ROOT).resolve()
    workspace_path = root_path / str(workspace_id)
    
    # Create the physical directory
    workspace_path.mkdir(parents=True, exist_ok=True)
    
    workspace = Workspace(
        id=workspace_id,
        name=workspace_in.name,
        path=str(workspace_path),
        custom_instructions=workspace_in.custom_instructions,
    )
    
    session.add(workspace)
    await session.commit()
    await session.refresh(workspace)
    
    return workspace


@router.get("", response_model=list[WorkspaceResponse])
async def list_workspaces(
    session: AsyncSession = Depends(get_db_session)
) -> list[Workspace]:
    result = await session.execute(select(Workspace).order_by(Workspace.created_at.desc()))
    return list(result.scalars().all())


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session)
) -> Workspace:
    workspace = await session.get(Workspace, workspace_id)
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return workspace


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session)
) -> None:
    workspace = await session.get(Workspace, workspace_id)
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

    workspace_id_str = str(workspace.id)
        
    # Delete DB row
    await session.delete(workspace)
    await session.commit()
    
    # Clean up physical directory
    workspace_path = Path(workspace.path)
    if workspace_path.exists() and workspace_path.is_dir():
        shutil.rmtree(workspace_path, ignore_errors=True)

    await cleanup_browser_session(workspace_id_str)

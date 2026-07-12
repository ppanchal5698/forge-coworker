#!/usr/bin/env python
"""Seed a workspace.

Bootstraps a new workspace: creates the DB row, the on-disk directory under
workspaces/, and outputs the ID.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to sys.path so we can import app modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings
from app.db.session import get_session_factory
from app.db.models.workspace import Workspace


async def seed_workspace(name: str, instructions: str = "") -> str:
    """Seed a workspace in the DB and create its folder."""
    settings = get_settings()
    factory = get_session_factory()
    
    async with factory() as session:
        workspace = Workspace(
            name=name,
            custom_instructions=instructions,
            # We don't have the ID yet, but it's generated on insert, wait we can just generate it manually
        )
        # Generate UUID upfront to construct path
        import uuid
        workspace_id = uuid.uuid4()
        workspace.id = workspace_id
        
        root_path = Path(settings.WORKSPACE_ROOT).resolve()
        workspace_path = root_path / str(workspace_id)
        
        workspace.path = str(workspace_path)
        
        # Create dir
        workspace_path.mkdir(parents=True, exist_ok=True)
        print(f"Created workspace directory at: {workspace_path}")
        
        session.add(workspace)
        await session.commit()
        
        print(f"Created workspace in DB with ID: {workspace_id}")
        return str(workspace_id)


if __name__ == "__main__":
    name = "Test Workspace"
    if len(sys.argv) > 1:
        name = sys.argv[1]
    asyncio.run(seed_workspace(name))

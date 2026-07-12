"""Base MCP server scaffolding.

Provides the client connection logic for the FastAPI app to talk to the
sandbox-isolated MCP servers.
"""

import asyncio
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from structlog import get_logger

from app.config import get_settings

logger = get_logger(__name__)


@asynccontextmanager
async def mcp_client(container_name: str, server_module: str) -> AsyncGenerator[ClientSession, None]:
    """Yield an active MCP ClientSession connected to a sandboxed server.
    
    Uses `docker exec -i` to run the specified python module as an MCP server
    and communicate with it over stdin/stdout.
    """
    settings = get_settings()

    # The server scripts are built into the sandbox image at /opt/mcp_servers
    script_path = f"/opt/mcp_servers/{server_module}.py"
    
    server_params = StdioServerParameters(
        command="docker",
        args=["exec", "-i", container_name, "python", script_path],
    )
    
    try:
        async with asyncio.timeout(settings.MCP_CONNECT_TIMEOUT_SECONDS):
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    yield session
    except asyncio.TimeoutError as exc:
        raise TimeoutError(
            f"Timed out connecting to MCP server '{server_module}' in container '{container_name}'"
        ) from exc

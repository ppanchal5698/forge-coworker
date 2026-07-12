"""Filesystem tools.

LangChain `@tool` wrappers that connect to the filesystem MCP server.
"""

from langchain_core.tools import tool

from app.sandbox.docker_manager import sandbox_manager
from app.mcp_servers.base_server import mcp_client


@tool
async def read_file(workspace_id: str, workspace_dir: str, path: str) -> str:
    """Read the contents of a file in the workspace.
    
    Args:
        workspace_id: The UUID of the workspace.
        workspace_dir: The host path of the workspace (used to ensure sandbox).
        path: The path to the file relative to the workspace.
    """
    container_name = sandbox_manager.ensure_sandbox(workspace_id, workspace_dir)
    
    async with mcp_client(container_name, "filesystem_server") as session:
        result = await session.call_tool("read_file", arguments={"path": path})
        return str(result.content[0].text)


@tool
async def write_file(workspace_id: str, workspace_dir: str, path: str, content: str) -> str:
    """Write content to a file in the workspace.
    
    Args:
        workspace_id: The UUID of the workspace.
        workspace_dir: The host path of the workspace.
        path: The path to the file relative to the workspace.
        content: The text content to write.
    """
    container_name = sandbox_manager.ensure_sandbox(workspace_id, workspace_dir)
    
    async with mcp_client(container_name, "filesystem_server") as session:
        result = await session.call_tool("write_file", arguments={"path": path, "content": content})
        return str(result.content[0].text)


@tool
async def read_binary_file(workspace_id: str, workspace_dir: str, path: str) -> str:
    """Read the contents of a binary file in the workspace and return it as a base64 string.
    
    Args:
        workspace_id: The UUID of the workspace.
        workspace_dir: The host path of the workspace.
        path: The path to the file relative to the workspace.
    """
    container_name = sandbox_manager.ensure_sandbox(workspace_id, workspace_dir)
    
    async with mcp_client(container_name, "filesystem_server") as session:
        result = await session.call_tool("read_binary_file", arguments={"path": path})
        return str(result.content[0].text)


@tool
async def write_binary_file(workspace_id: str, workspace_dir: str, path: str, content_base64: str) -> str:
    """Write base64-encoded binary content to a file in the workspace.
    
    Args:
        workspace_id: The UUID of the workspace.
        workspace_dir: The host path of the workspace.
        path: The path to the file relative to the workspace.
        content_base64: The base64-encoded binary content to write.
    """
    container_name = sandbox_manager.ensure_sandbox(workspace_id, workspace_dir)
    
    async with mcp_client(container_name, "filesystem_server") as session:
        result = await session.call_tool("write_binary_file", arguments={"path": path, "content_base64": content_base64})
        return str(result.content[0].text)


@tool
async def list_directory(workspace_id: str, workspace_dir: str, path: str = ".") -> str:
    """List the contents of a directory in the workspace.
    
    Args:
        workspace_id: The UUID of the workspace.
        workspace_dir: The host path of the workspace.
        path: The directory path relative to the workspace.
    """
    container_name = sandbox_manager.ensure_sandbox(workspace_id, workspace_dir)
    
    async with mcp_client(container_name, "filesystem_server") as session:
        result = await session.call_tool("list_directory", arguments={"path": path})
        return str(result.content[0].text)

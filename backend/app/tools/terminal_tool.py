"""Terminal tools.

LangChain `@tool` wrappers that connect to the terminal MCP server.
"""

from langchain_core.tools import tool

from app.sandbox.docker_manager import sandbox_manager
from app.mcp_servers.base_server import mcp_client


@tool
async def execute_terminal_command(workspace_id: str, workspace_dir: str, command: str) -> str:
    """Execute a bash command in the workspace directory.
    
    Args:
        workspace_id: The UUID of the workspace.
        workspace_dir: The host path of the workspace.
        command: The bash command to run.
    """
    container_name = sandbox_manager.ensure_sandbox(workspace_id, workspace_dir)
    
    async with mcp_client(container_name, "terminal_server") as session:
        result = await session.call_tool("execute_command", arguments={"command": command})
        return str(result.content[0].text)

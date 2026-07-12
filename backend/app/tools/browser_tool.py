"""Browser tools.

LangChain `@tool` wrappers that connect to the browser MCP server.
Maintains a persistent connection per workspace to preserve the Playwright
browser session across multiple tool calls during a task.
"""

from contextlib import AsyncExitStack
from typing import Dict, Any

from langchain_core.tools import tool
from mcp import ClientSession

from app.sandbox.docker_manager import sandbox_manager
from app.mcp_servers.base_server import mcp_client

# Maintain persistent MCP sessions per workspace to keep the browser alive
_browser_sessions: Dict[str, dict] = {}


async def cleanup_browser_session(workspace_id: str) -> None:
    """Close and remove a cached browser session for one workspace."""
    data = _browser_sessions.pop(workspace_id, None)
    if not data:
        return

    stack = data.get("stack")
    if stack is not None:
        await stack.aclose()


async def cleanup_all_browser_sessions() -> None:
    """Close and remove all cached browser sessions."""
    workspace_ids = list(_browser_sessions.keys())
    for workspace_id in workspace_ids:
        await cleanup_browser_session(workspace_id)


async def _get_browser_session(workspace_id: str, workspace_dir: str) -> ClientSession:
    """Get or create a persistent MCP session for the browser server."""
    if workspace_id in _browser_sessions:
        return _browser_sessions[workspace_id]["session"]
        
    container_name = sandbox_manager.ensure_sandbox(workspace_id, workspace_dir)
    
    stack = AsyncExitStack()
    try:
        # Enter the context manager manually and store the stack
        session_cm = mcp_client(container_name, "browser_server")
        session = await stack.enter_async_context(session_cm)
        
        _browser_sessions[workspace_id] = {
            "session": session,
            "stack": stack
        }
        return session
    except Exception as e:
        await stack.aclose()
        raise e


@tool
async def browser_navigate(workspace_id: str, workspace_dir: str, url: str) -> str:
    """Navigate the headless browser to a URL.
    
    Args:
        workspace_id: The UUID of the workspace.
        workspace_dir: The host path of the workspace.
        url: The URL to navigate to.
    """
    session = await _get_browser_session(workspace_id, workspace_dir)
    result = await session.call_tool("navigate", arguments={"url": url})
    return str(result.content[0].text)


@tool
async def browser_click(workspace_id: str, workspace_dir: str, selector: str) -> str:
    """Click an element in the browser.
    
    Args:
        workspace_id: The UUID of the workspace.
        workspace_dir: The host path of the workspace.
        selector: The CSS selector of the element to click.
    """
    session = await _get_browser_session(workspace_id, workspace_dir)
    result = await session.call_tool("click_element", arguments={"selector": selector})
    return str(result.content[0].text)


@tool
async def browser_type(workspace_id: str, workspace_dir: str, selector: str, text: str) -> str:
    """Type text into an input field in the browser.
    
    Args:
        workspace_id: The UUID of the workspace.
        workspace_dir: The host path of the workspace.
        selector: The CSS selector of the input field.
        text: The text to type.
    """
    session = await _get_browser_session(workspace_id, workspace_dir)
    result = await session.call_tool("fill_input", arguments={"selector": selector, "text": text})
    return str(result.content[0].text)


@tool
async def browser_extract_text(workspace_id: str, workspace_dir: str) -> str:
    """Extract all visible text from the current webpage.
    
    Args:
        workspace_id: The UUID of the workspace.
        workspace_dir: The host path of the workspace.
    """
    session = await _get_browser_session(workspace_id, workspace_dir)
    result = await session.call_tool("extract_text", arguments={})
    return str(result.content[0].text)


@tool
async def browser_screenshot(workspace_id: str, workspace_dir: str, full_page: bool = False) -> str:
    """Take a screenshot of the current webpage.
    
    Returns a string containing 'SCREENSHOT_BASE64:...' which the developer
    agent can pass to the vision analysis tool.
    
    Args:
        workspace_id: The UUID of the workspace.
        workspace_dir: The host path of the workspace.
        full_page: Whether to capture the full scrolling page.
    """
    session = await _get_browser_session(workspace_id, workspace_dir)
    result = await session.call_tool("take_screenshot", arguments={"full_page": full_page})
    return str(result.content[0].text)

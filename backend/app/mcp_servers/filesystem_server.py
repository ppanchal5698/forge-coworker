"""Filesystem MCP server.

Implements read/write/move/list operations, refusing any path that resolves
outside the mounted workspace directory (FR-6).
Runs inside the sandbox container.
"""

import base64
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# The sandbox mounts the workspace at /workspace
WORKSPACE_DIR = Path("/workspace").resolve()

mcp = FastMCP("filesystem")


def _resolve_and_check_path(path: str) -> Path:
    """Resolve a path and ensure it is strictly within the workspace."""
    raw = Path(path)
    if raw.is_absolute():
        target = raw.resolve(strict=False)
    else:
        target = (WORKSPACE_DIR / raw).resolve(strict=False)

    try:
        target.relative_to(WORKSPACE_DIR)
    except ValueError as exc:
        raise ValueError(
            f"Access denied: path '{path}' is outside the workspace directory."
        ) from exc

    return target


@mcp.tool()
def read_file(path: str) -> str:
    """Read the contents of a file.
    
    Args:
        path: The path to the file relative to the workspace.
    """
    target = _resolve_and_check_path(path)
    if not target.exists():
        return f"Error: File '{path}' does not exist."
    if not target.is_file():
        return f"Error: '{path}' is not a file."
        
    try:
        return target.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error reading file: {str(e)}"


@mcp.tool()
def write_file(path: str, content: str) -> str:
    """Write content to a file, creating it if it doesn't exist.
    
    Args:
        path: The path to the file relative to the workspace.
        content: The text content to write.
    """
    target = _resolve_and_check_path(path)
    
    # Ensure parent directory exists
    target.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        target.write_text(content, encoding="utf-8")
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"


@mcp.tool()
def read_binary_file(path: str) -> str:
    """Read the contents of a binary file and return it as a base64 string.
    
    Args:
        path: The path to the file relative to the workspace.
    """
    target = _resolve_and_check_path(path)
    if not target.exists():
        return f"Error: File '{path}' does not exist."
    if not target.is_file():
        return f"Error: '{path}' is not a file."
        
    try:
        content = target.read_bytes()
        return base64.b64encode(content).decode("utf-8")
    except Exception as e:
        return f"Error reading binary file: {str(e)}"


@mcp.tool()
def write_binary_file(path: str, content_base64: str) -> str:
    """Write base64-encoded binary content to a file, creating it if it doesn't exist.
    
    Args:
        path: The path to the file relative to the workspace.
        content_base64: The base64-encoded binary content to write.
    """
    target = _resolve_and_check_path(path)
    
    # Ensure parent directory exists
    target.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        binary_data = base64.b64decode(content_base64)
        target.write_bytes(binary_data)
        return f"Successfully wrote binary file to {path}"
    except Exception as e:
        return f"Error writing binary file: {str(e)}"


@mcp.tool()
def list_directory(path: str = ".") -> str:
    """List the contents of a directory.
    
    Args:
        path: The directory path relative to the workspace.
    """
    target = _resolve_and_check_path(path)
    if not target.exists():
        return f"Error: Directory '{path}' does not exist."
    if not target.is_dir():
        return f"Error: '{path}' is not a directory."
        
    try:
        items = os.listdir(target)
        return "\n".join(items) if items else "(empty directory)"
    except Exception as e:
        return f"Error listing directory: {str(e)}"


if __name__ == "__main__":
    mcp.run()

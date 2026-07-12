"""Tool registry.

Provides the list of all available tools to the LLM and the tool execution node.
"""

from typing import Dict, List, Any

# We will import the actual tools once they are implemented
from app.tools.terminal_tool import execute_terminal_command
from app.tools.filesystem_tool import read_file, write_file, list_directory
from app.tools.browser_tool import (
    browser_navigate,
    browser_click,
    browser_type,
    browser_extract_text,
    browser_screenshot
)
from app.tools.vision_tool import vision_analyze
from app.tools.document_tool import generate_document, edit_document


def get_all_tools() -> List[Any]:
    """Return a list of all tools available to the developer agent."""
    return [
        execute_terminal_command,
        read_file,
        write_file,
        list_directory,
        browser_navigate,
        browser_click,
        browser_type,
        browser_extract_text,
        browser_screenshot,
        vision_analyze,
        generate_document,
        edit_document,
    ]


def get_tool_map() -> Dict[str, Any]:
    """Return a dictionary mapping tool names to tool objects for execution."""
    return {tool.name: tool for tool in get_all_tools()}

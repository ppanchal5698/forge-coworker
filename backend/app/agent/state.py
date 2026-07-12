"""Shared LangGraph state contract.

This state is passed to every node. It extends MessagesState with Forge-specific
fields for workspace routing, error handling, and agent delegation.
"""

from typing import Annotated, NotRequired

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict):
    """The state dictionary passed through the LangGraph execution."""

    messages: Annotated[list, add_messages]
    workspace_dir: str
    active_agent: str
    error_count: int
    workspace_id: NotRequired[str]
    task_id: NotRequired[str]
    pending_tool_calls: NotRequired[list]
    # PRD alignment: human_feedback is the canonical approval signal.
    human_feedback: NotRequired[str | None]
    # Backward-compatible alias for older resume paths.
    approval_decision: NotRequired[str | None]

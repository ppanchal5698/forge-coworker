"""Tool execution node.

Executes the requested tools and returns the results to the developer agent.
Includes logic for exponential backoff, error ceilings, and security interception
(HITL routing for destructive commands).
"""

from langchain_core.messages import ToolMessage
from langgraph.types import Command
import json

from app.agent.state import AgentState
from app.config import get_settings
from app.tools.registry import get_tool_map
from app.security.deny_list import is_hard_denied
from app.agent.classifiers import is_llm_flagged
from app.db.session import get_session_factory
from app.db.models.approval import Approval
from app.db.models.task import Task, TaskStatus
from app.realtime.supabase_client import broadcast_approval_request


async def _run_security_check(tool_name: str, tool_args: dict) -> bool:
    """Check if a tool call is destructive. Returns True if flagged."""
    if tool_name not in ["execute_terminal_command", "write_file", "delete_file"]:
        return False
        
    action_str = json.dumps(tool_args)
    
    # 1. Hard deny list
    if is_hard_denied(action_str):
        return True
        
    # 2. Semantic LLM check
    if await is_llm_flagged(action_str):
        return True
        
    return False


async def tool_node(state: AgentState) -> Command:
    """The tool execution node function."""
    messages = state["messages"]
    last_message = messages[-1]
    
    settings = get_settings()
    tool_map = get_tool_map()
    
    error_count = state.get("error_count", 0)
    
    workspace_id = state.get("workspace_id")
    workspace_dir = state.get("workspace_dir")

    # Check if we were resumed with an approval decision for pending tool calls
    decision = (state.get("human_feedback") or state.get("approval_decision") or "").lower()
    if decision == "approved" and state.get("pending_tool_calls"):
        # We are resuming after a human approval. Execute the pending calls.
        tool_calls = state["pending_tool_calls"]
        clear_resume_state = {
            "pending_tool_calls": None,
            "approval_decision": None,
            "human_feedback": None,
        }
    else:
        tool_calls = getattr(last_message, "tool_calls", None) or []
        clear_resume_state = {}

        if not tool_calls:
            return Command(
                goto="developer",
                update={
                    "active_agent": "tool_execution",
                },
            )
        
        # Security Interception (only for new tool calls)
        flagged = False
        action_descriptions = []
        for call in tool_calls:
            if await _run_security_check(call["name"], call["args"]):
                flagged = True
                action_descriptions.append(f"{call['name']}({json.dumps(call['args'])})")
                
        if flagged:
            # Create an Approval record
            task_id = state.get("task_id")
            action_desc = " | ".join(action_descriptions)
            
            factory = get_session_factory()
            async with factory() as session:
                approval = Approval(
                    task_id=task_id,
                    action_description=f"Destructive action detected: {action_desc}"
                )
                session.add(approval)

                if task_id:
                    task = await session.get(Task, task_id)
                    if task:
                        task.status = TaskStatus.AWAITING_APPROVAL

                await session.commit()
                approval_id = str(approval.id)
                
            # Broadcast to UI
            await broadcast_approval_request(task_id, approval_id, action_desc)
            
            # Route to human_approval node to wait
            return Command(
                goto="human_approval",
                update={
                    "pending_tool_calls": tool_calls,
                    "active_agent": "tool_execution",
                }
            )

    # Standard Execution
    tool_outputs = []
    for tool_call in tool_calls:
        tool_name = tool_call["name"]
        tool_args = dict(tool_call["args"])
        tool_id = tool_call["id"]

        # Most Forge tools require workspace context. Inject from state when omitted.
        if workspace_id and "workspace_id" not in tool_args:
            tool_args["workspace_id"] = workspace_id
        if workspace_dir and "workspace_dir" not in tool_args:
            tool_args["workspace_dir"] = workspace_dir
        
        if tool_name not in tool_map:
            tool_outputs.append(
                ToolMessage(
                    content=f"Error: Tool {tool_name} not found.",
                    name=tool_name,
                    tool_call_id=tool_id,
                )
            )
            error_count += 1
            continue
            
        tool = tool_map[tool_name]
        try:
            result = await tool.ainvoke(tool_args)
            tool_outputs.append(
                ToolMessage(
                    content=str(result),
                    name=tool_name,
                    tool_call_id=tool_id,
                )
            )
            error_count = 0
        except Exception as e:
            error_count += 1
            tool_outputs.append(
                ToolMessage(
                    content=f"Error executing tool: {str(e)}",
                    name=tool_name,
                    tool_call_id=tool_id,
                )
            )
            
    if error_count >= settings.ERROR_CEILING:
        return Command(
            goto="supervisor",
            update={
                "messages": tool_outputs,
                "error_count": error_count,
                "active_agent": "tool_execution",
                **clear_resume_state,
            }
        )
        
    return Command(
        goto="developer",
        update={
            "messages": tool_outputs,
            "error_count": error_count,
            "active_agent": "tool_execution",
            **clear_resume_state,
        }
    )

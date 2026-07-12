"""Developer agent node.

Executes the developer prompt with tools bound. If it calls a tool, returns a
Command to the tool_execution node. Otherwise, returns control to the supervisor.
"""

from langchain_core.messages import AIMessage, SystemMessage
from langgraph.types import Command

from app.agent.state import AgentState
from app.llm.client import get_llm_with_tools
from app.agent.prompts.developer_prompt import DEVELOPER_SYSTEM_PROMPT

# We will import the actual tools from the registry in Phase 1
from app.tools.registry import get_all_tools


async def developer_node(state: AgentState) -> Command:
    """The developer node function."""
    tools = get_all_tools()
    llm = get_llm_with_tools(tools)
    
    sys_prompt = DEVELOPER_SYSTEM_PROMPT.format(
        workspace_dir=state.get("workspace_dir", "/workspace")
    )
    messages = [SystemMessage(content=sys_prompt)] + state["messages"]
    
    try:
        response = await llm.ainvoke(messages)
    except Exception as exc:
        fallback_msg = AIMessage(
            content=(
                "Developer agent failed to call the model endpoint. "
                f"Returning control to supervisor. Error: {exc}"
            )
        )
        return Command(
            goto="supervisor",
            update={
                "messages": [fallback_msg],
                "active_agent": "developer",
                "error_count": state.get("error_count", 0) + 1,
            },
        )
    
    if response.tool_calls:
        return Command(
            goto="tool_execution",
            update={
                "messages": [response],
                "active_agent": "developer"
            }
        )
        
    # If the developer doesn't call a tool, it means it's done or reporting back
    return Command(
        goto="supervisor",
        update={
            "messages": [response],
            "active_agent": "developer"
        }
    )

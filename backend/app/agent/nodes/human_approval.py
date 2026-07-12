"""Human approval node.

This node executes after the graph is resumed from a paused state (interrupt_before).
It reads the human's decision and routes execution accordingly.
"""

from langchain_core.messages import ToolMessage
from langgraph.types import Command

from app.agent.state import AgentState


async def human_approval_node(state: AgentState) -> Command:
    """Process the human's approval decision.
    
    This node is the target of `interrupt_before=["human_approval"]`.
    When the API receives the human's decision, it updates the state with
    `approval_decision` ("APPROVED" or "REJECTED") and resumes the graph.
    """
    decision = (state.get("human_feedback") or state.get("approval_decision") or "").lower()
    pending_calls = state.get("pending_tool_calls", [])
    
    if decision == "approved":
        # Route back to tool_execution to execute the pending calls.
        # The tool_execution node checks for `approval_decision == "APPROVED"`
        # to bypass the security check and clear the pending state.
        return Command(
            goto="tool_execution",
            update={
                "active_agent": "human_approval",
            }
        )
    else:
        # If REJECTED or anything else, we return a ToolMessage for each pending call
        # indicating that the user rejected it.
        tool_outputs = []
        for call in pending_calls:
            tool_outputs.append(
                ToolMessage(
                    content="SYSTEM: The user REJECTED this action. Do not attempt it again. Ask the user for alternative instructions.",
                    name=call["name"],
                    tool_call_id=call["id"],
                )
            )
            
        return Command(
            goto="developer",
            update={
                "messages": tool_outputs,
                "pending_tool_calls": None,
                "approval_decision": None,
                "human_feedback": None,
                "active_agent": "human_approval"
            }
        )

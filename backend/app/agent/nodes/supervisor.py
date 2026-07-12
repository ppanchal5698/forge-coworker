"""Supervisor node.

Analyzes the state and returns a Command to route execution to the next node.
"""

from typing import Literal

from langchain_core.messages import AIMessage, SystemMessage
from langgraph.types import Command
from pydantic import BaseModel, Field

from app.agent.state import AgentState
from app.llm.client import get_llm
from app.agent.prompts.supervisor_prompt import SUPERVISOR_SYSTEM_PROMPT


class SupervisorDecision(BaseModel):
    """The structured decision made by the supervisor."""
    
    next_node: Literal["developer", "human_approval", "FINISH"] = Field(
        description="The next node to route to. Choose 'developer' for technical work, 'human_approval' for destructive actions, or 'FINISH' if the task is complete."
    )
    reasoning: str = Field(
        description="Brief explanation of why this routing decision was made."
    )


async def supervisor_node(state: AgentState) -> Command:
    """The supervisor node function."""
    llm = get_llm()
    structured_llm = llm.with_structured_output(SupervisorDecision)
    
    messages = [SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT)] + state["messages"]
    
    try:
        # We await the structured output
        decision: SupervisorDecision = await structured_llm.ainvoke(messages)
    except Exception as exc:
        fallback_msg = AIMessage(
            content=(
                "Supervisor routing failed due to an LLM error. "
                f"Falling back to developer node. Error: {exc}"
            )
        )
        return Command(
            goto="developer",
            update={
                "messages": [fallback_msg],
                "active_agent": "supervisor",
                "error_count": state.get("error_count", 0) + 1,
            },
        )
    
    if decision.next_node == "FINISH":
        return Command(
            goto="__end__",
            update={"active_agent": "supervisor"}
        )
        
    return Command(
        goto=decision.next_node,
        update={"active_agent": "supervisor"}
    )

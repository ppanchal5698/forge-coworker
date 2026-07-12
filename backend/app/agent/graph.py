"""Main LangGraph compilation.

Wires the nodes together using the Supervisor/Worker pattern, where nodes
return a Command primitive to dictate the next transition.
"""

from langgraph.graph import StateGraph, START

from app.agent.state import AgentState
from app.agent.nodes.supervisor import supervisor_node
from app.agent.nodes.developer_agent import developer_node
from app.agent.nodes.tool_execution import tool_node
from app.agent.nodes.human_approval import human_approval_node

def create_graph():
    """Build and return the uncompiled StateGraph."""
    builder = StateGraph(AgentState)

    # Add all nodes
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("developer", developer_node)
    builder.add_node("tool_execution", tool_node)
    builder.add_node("human_approval", human_approval_node)

    # The entry point is always the supervisor
    builder.add_edge(START, "supervisor")

    # In LangGraph 0.1+, nodes return `Command(goto="next_node")`. 
    # Therefore, we do not need to define add_conditional_edges routers here.
    # The graph structure is defined dynamically by the commands returned from the nodes.
    
    return builder

# Compile function
def compile_graph(checkpointer=None):
    """Compile the graph, optionally with a checkpointer."""
    builder = create_graph()
    
    # We interrupt before human_approval so execution pauses.
    # The UI or API will resume the graph with the human's decision.
    return builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["human_approval"],
    )

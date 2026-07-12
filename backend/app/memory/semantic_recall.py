"""Semantic recall.

Queries vector_store.py for relevant historical context and injects it into
the Supervisor/Developer prompts before a new step, giving the agent memory
beyond the current thread.
"""

import uuid
from langchain_core.messages import SystemMessage

from app.memory.vector_store import search_similar


async def inject_context(workspace_id: uuid.UUID, current_goal_or_query: str, system_prompt: str) -> SystemMessage:
    """Query semantic memory and inject the most relevant past context into the system prompt."""
    
    similar_memories = await search_similar(workspace_id, current_goal_or_query, top_k=5)
    
    context_text = ""
    if similar_memories:
        context_text = "\n\n--- RELEVANT PAST CONTEXT ---\n"
        for i, mem in enumerate(similar_memories, 1):
            context_text += f"{i}. {mem}\n"
        context_text += "-----------------------------\n"
        
    final_prompt = system_prompt + context_text
    return SystemMessage(content=final_prompt)

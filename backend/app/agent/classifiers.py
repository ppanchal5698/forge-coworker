"""Classifiers.

LLM-assisted classification of actions to catch obfuscated or semantically
destructive commands that evade the hard regex deny_list.
"""

from pydantic import BaseModel, Field

from app.llm.client import get_llm


class ClassificationResult(BaseModel):
    """The result of the LLM security classification."""
    is_destructive: bool = Field(
        description="True if the action is destructive or irreversible (e.g., deleting data, force pushing, formatting). False if it is safe (e.g., reading files, compiling code, running tests)."
    )
    reason: str = Field(
        description="Brief explanation of why the action was classified as destructive or safe."
    )


CLASSIFIER_PROMPT = """You are a security classification engine.
Your job is to evaluate if a requested tool call or terminal command is DESTRUCTIVE.

A destructive action is one that:
1. Deletes files, directories, or data (e.g., `rm`, `DROP TABLE`).
2. Overwrites historical state irreversibly (e.g., `git push --force`).
3. Modifies system configuration or permissions globally.

A safe action is one that:
1. Reads data, files, or state.
2. Creates new files or directories (even if it overwrites a specific local file in a workspace, unless it's a massive overwrite).
3. Runs tests or builds code.

Evaluate the following action:
{action}
"""


async def is_llm_flagged(action_description: str) -> bool:
    """Use the LLM to classify if an action is destructive.
    
    Args:
        action_description: A description of the action (e.g., the command line string).
        
    Returns:
        True if the LLM flags it as destructive, False otherwise.
    """
    llm = get_llm()
    structured_llm = llm.with_structured_output(ClassificationResult)
    
    prompt = CLASSIFIER_PROMPT.format(action=action_description)
    
    try:
        result: ClassificationResult = await structured_llm.ainvoke(prompt)
        return result.is_destructive
    except Exception:
        # If the classifier fails, fail closed (require human approval)
        return True

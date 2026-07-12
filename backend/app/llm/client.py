"""LLM client factory.

Factory for the ChatOpenAI-compatible client pointed at the local vLLM
endpoint, used by every agent node that needs a completion.
"""

from functools import lru_cache

from langchain_openai import ChatOpenAI
from structlog import get_logger

from app.config import get_settings
from app.llm.model_config import get_model_config

logger = get_logger(__name__)


@lru_cache
def get_llm() -> ChatOpenAI:
    """Return a cached ChatOpenAI instance pointed at the local model endpoint.

    The client is OpenAI-API-compatible, so it works with vLLM, Ollama, or any
    endpoint that implements the OpenAI chat completions API.
    """
    settings = get_settings()
    config = get_model_config()

    if settings.LLM_PROVIDER == "airllm":
        # ASSUMPTION: Phase-1 implementation keeps a unified OpenAI-compatible
        # interface so existing tool binding and structured output continue to work.
        # A dedicated AirLLM direct adapter will be added in a later milestone.
        logger.warning(
            "LLM_PROVIDER=airllm selected; using OpenAI-compatible bridge for now",
            provider=settings.LLM_PROVIDER,
            base_url=settings.resolved_llm_base_url,
        )

    return ChatOpenAI(
        base_url=settings.resolved_llm_base_url,
        api_key=settings.resolved_llm_api_key,
        model=config.model_name,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )


def get_llm_with_tools(tools: list) -> ChatOpenAI:
    """Return an LLM instance with tools bound.

    Creates a new instance each time since tool bindings may change
    between calls (e.g., different tools for different agents).
    """
    llm = get_llm()
    return llm.bind_tools(tools)

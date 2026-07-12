"""Model configuration.

Centralizes model name, quantization, temperature, and context-window settings
per environment (dev vs. production), so client.py stays environment-agnostic.
"""

from dataclasses import dataclass

from app.config import get_settings


@dataclass(frozen=True)
class ModelConfig:
    """Configuration for the primary Brain model."""

    model_name: str
    temperature: float
    max_tokens: int
    context_window: int


def get_model_config() -> ModelConfig:
    """Return the model configuration based on current settings.

    Reads the model name from settings; other parameters use sensible defaults
    for local quantized model deployment.
    """
    settings = get_settings()
    return ModelConfig(
        model_name=settings.resolved_llm_model_name,
        temperature=0.1,  # Low temperature for deterministic planning/coding
        max_tokens=settings.AIRLLM_MAX_NEW_TOKENS,
        # ASSUMPTION: 32k context window is available with Qwen2.5-32B-Coder AWQ.
        # Verify against the actual model's max_model_len when deployed.
        context_window=32768,
    )

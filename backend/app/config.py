"""Pydantic Settings class loading all environment variables.

Single source of truth so no module reads os.environ directly.
DB URI, vLLM base URL, Supabase keys, workspace root path, retry ceilings.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- Database (PostgreSQL + pgvector) ---
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/forge"
    SYNC_DATABASE_URL: str = "postgresql+psycopg://postgres:password@localhost:5432/forge"
    CHECKPOINT_DB_URI: str = "postgresql://postgres:password@localhost:5432/forge"

    # --- LLM Endpoint (vLLM or Ollama, OpenAI-compatible) ---
    LLM_PROVIDER: Literal["openai_compatible", "ollama", "airllm"] = "ollama"
    LLM_BASE_URL: str = "http://localhost:11434/v1"
    LLM_API_KEY: str = "local-execution"
    LLM_MODEL_NAME: str = "qwen2.5-coder:32b"
    EMBEDDING_MODEL_NAME: str = "nomic-embed-text"

    # --- Backward-compat aliases for older config/docs ---
    VLLM_BASE_URL: str = "http://localhost:11434/v1"
    VLLM_API_KEY: str = "local-execution"
    VLLM_MODEL_NAME: str = "qwen2.5-coder:32b"
    VLLM_EMBEDDING_MODEL: str = "nomic-embed-text"

    # --- AirLLM direct mode ---
    AIRLLM_MODEL_ID: str = "Qwen/Qwen2.5-Coder-32B-Instruct"
    AIRLLM_DEVICE: str = "cuda:0"
    AIRLLM_MAX_NEW_TOKENS: int = 4096
    AIRLLM_MAX_INPUT_TOKENS: int = 4096

    # --- Workspace ---
    WORKSPACE_ROOT: str = "./workspaces"

    # --- Agent ---
    MAX_RETRIES: int = 3
    ERROR_CEILING: int = 5
    TASK_TIMEOUT_SECONDS: int = 3600
    CRON_MAX_CONCURRENT_TASKS: int = 4
    CRON_POLL_INTERVAL_SECONDS: int = 5
    STREAM_POLL_INTERVAL_SECONDS: int = 2
    MCP_CONNECT_TIMEOUT_SECONDS: int = 15

    # --- Supabase (realtime layer — Phase 2+) ---
    SUPABASE_URL: str = "http://localhost:54321"
    SUPABASE_ANON_KEY: str = ""

    # --- Security ---
    API_BEARER_TOKEN: str = "change-me-in-production"

    # --- Docker Sandbox ---
    SANDBOX_IMAGE: str = "forge-sandbox:latest"
    SANDBOX_MEMORY_LIMIT: str = "512m"
    SANDBOX_CPU_LIMIT: float = 1.0

    @property
    def resolved_llm_base_url(self) -> str:
        """Return the effective OpenAI-compatible base URL.

        Uses the new LLM_* variables first, then backward-compatible VLLM_*.
        """
        return self.LLM_BASE_URL or self.VLLM_BASE_URL

    @property
    def resolved_llm_api_key(self) -> str:
        """Return the effective API key used by OpenAI-compatible clients."""
        return self.LLM_API_KEY or self.VLLM_API_KEY

    @property
    def resolved_llm_model_name(self) -> str:
        """Return the effective model name for chat completions."""
        return self.LLM_MODEL_NAME or self.VLLM_MODEL_NAME

    @property
    def resolved_embedding_model_name(self) -> str:
        """Return the effective model name for embedding calls."""
        return self.EMBEDDING_MODEL_NAME or self.VLLM_EMBEDDING_MODEL


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Uses lru_cache so the .env file is only read once per process.
    """
    return Settings()

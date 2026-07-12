# Forge

A local, self-hosted autonomous agentic development platform.

Forge plans, executes, verifies, and self-corrects complex knowledge-work and
software-engineering tasks with minimal supervision. Built on an entirely open,
self-hosted stack: **FastAPI + LangGraph** backend, **Next.js** dashboard frontend.

## Architecture

| Component | Implementation |
|-----------|---------------|
| Brain (planning) | vLLM / Ollama serving a quantized coding model |
| Eyes (perception) | Vision-language model (Qwen2-VL-7B) |
| Hands (execution) | MCP servers (filesystem, terminal, browser) |
| Memory | PostgreSQL + pgvector |
| Orchestration | LangGraph (Supervisor/Worker, Command-based routing) |
| Sandbox | Docker (workspace-scoped volume mounts) |

## Documentation

- [Product Requirements Document](docs/PRD_Forge_Local_Agent_Platform.md)
- [Project Structure](docs/PROJECT_STRUCTURE.md)
- [Agent Governance Rules](AGENTS.md)

## Quick Start

```bash
# 1. Clone and configure
cp backend/.env.example backend/.env
# Edit backend/.env with your database and model endpoint settings

# 2. Start infrastructure
docker compose -f docker/docker-compose.yml up -d

# Optional: if Supabase is running in another Docker project,
# export SUPABASE_ANON_KEY before starting the Forge API container.
# export SUPABASE_ANON_KEY="<your-local-supabase-anon-key>"

# 3. Run database setup
cd backend && python scripts/setup_db.py

# 4. Start the API server
cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 5. Run tests
cd backend && pytest tests/ -v
```

## Runtime Configuration Notes

- `LLM_PROVIDER` controls model provider mode (`ollama`, `openai_compatible`, `airllm`).
- `LLM_BASE_URL`, `LLM_API_KEY`, and `LLM_MODEL_NAME` define the OpenAI-compatible endpoint used by the graph nodes.
- `SUPABASE_URL` and `SUPABASE_ANON_KEY` enable realtime event publishing to `task_events`.
- `NEXT_PUBLIC_TASK_STREAM_SOURCE` in frontend env selects `supabase` (default) or `sse` fallback.

## Project Structure

See [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) for the complete
file manifest and per-file responsibilities.

## License

Private — see repository owner for access.

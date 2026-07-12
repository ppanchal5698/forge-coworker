# Forge — Backend

FastAPI + LangGraph agent runtime.

## Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your settings

# Start Postgres (via Docker)
docker compose -f ../docker/docker-compose.yml up -d postgres

# Optional: start API + Postgres via compose
# docker compose -f ../docker/docker-compose.yml up -d postgres api

# Run database setup
python scripts/setup_db.py

# Start the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Environment Notes

- `LLM_PROVIDER` selects `ollama`, `openai_compatible`, or `airllm`.
- `LLM_*` variables are preferred; legacy `VLLM_*` aliases are still supported.
- `SUPABASE_URL` + `SUPABASE_ANON_KEY` enable realtime insert/broadcast for task events.
- In Docker Compose, Forge API defaults to `http://host.docker.internal:11434/v1` for local model endpoints.

## Testing

```bash
pytest tests/ -v
```

## Project Structure

See [../docs/PROJECT_STRUCTURE.md](../docs/PROJECT_STRUCTURE.md) for details.

# Forge — End-to-End Project Structure

Companion to `PRD_Forge_Local_Agent_Platform.md`. Maps every architectural component from the PRD (Section 7) to an actual file on disk.

> **Note on `__init__.py`:** every Python package directory below contains an `__init__.py` that marks it importable and re-exports the module's public interface. These are omitted from the reference tables for brevity but are present in the tree.

---

## 1. Top-Level Repository Layout

```
forge/
├── backend/            # FastAPI + LangGraph agent runtime
├── frontend/           # Next.js dashboard (live progress, approvals)
├── docs/
│   └── PRD_Forge_Local_Agent_Platform.md
├── .gitignore
└── README.md
```

---

## 2. Backend — Full Folder Tree

```
backend/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── dependencies.py
│   │
│   ├── api/
│   │   ├── routes/
│   │   │   ├── tasks.py
│   │   │   ├── workspaces.py
│   │   │   ├── approvals.py
│   │   │   ├── health.py
│   │   │   └── stream.py
│   │   └── schemas/
│   │       ├── task.py
│   │       ├── workspace.py
│   │       └── approval.py
│   │
│   ├── agent/
│   │   ├── state.py
│   │   ├── graph.py
│   │   ├── checkpointer.py
│   │   ├── classifiers.py
│   │   ├── nodes/
│   │   │   ├── supervisor.py
│   │   │   ├── developer_agent.py
│   │   │   ├── tool_execution.py
│   │   │   └── human_approval.py
│   │   └── prompts/
│   │       ├── supervisor_prompt.py
│   │       └── developer_prompt.py
│   │
│   ├── tools/
│   │   ├── registry.py
│   │   ├── terminal_tool.py
│   │   ├── filesystem_tool.py
│   │   ├── browser_tool.py
│   │   └── document_tool.py
│   │
│   ├── mcp_servers/
│   │   ├── base_server.py
│   │   ├── filesystem_server.py
│   │   ├── terminal_server.py
│   │   └── browser_server.py
│   │
│   ├── vision/
│   │   ├── vlm_client.py
│   │   └── screenshot.py
│   │
│   ├── llm/
│   │   ├── client.py
│   │   └── model_config.py
│   │
│   ├── memory/
│   │   ├── vector_store.py
│   │   └── semantic_recall.py
│   │
│   ├── db/
│   │   ├── session.py
│   │   ├── base.py
│   │   ├── models/
│   │   │   ├── workspace.py
│   │   │   ├── task.py
│   │   │   └── approval.py
│   │   └── migrations/
│   │       ├── env.py
│   │       └── versions/          # generated Alembic revisions
│   │
│   ├── realtime/
│   │   └── supabase_client.py
│   │
│   ├── sandbox/
│   │   ├── docker_manager.py
│   │   └── policy.py
│   │
│   ├── security/
│   │   ├── deny_list.py
│   │   └── auth.py
│   │
│   ├── scheduler/
│   │   ├── cron_runner.py
│   │   └── task_queue.py
│   │
│   └── utils/
│       ├── logger.py
│       └── retry.py
│
├── scripts/
│   ├── setup_db.py
│   ├── seed_workspace.py
│   └── run_soak_test.py
│
├── docker/
│   ├── Dockerfile.api
│   ├── Dockerfile.sandbox
│   └── docker-compose.yml
│
├── tests/
│   ├── conftest.py
│   ├── test_graph.py
│   ├── test_tools.py
│   ├── test_approval_flow.py
│   └── test_checkpointing.py
│
├── workspaces/            # gitignored — runtime workspace dirs, one per project, mounted into sandbox containers
├── alembic.ini
├── requirements.txt
├── pyproject.toml
├── .env.example
└── README.md
```

---

## 3. Backend — File Reference (2-line summary each)

### 3.1 `app/` root

| File | What it does |
|---|---|
| `main.py` | FastAPI application entrypoint — creates the app instance, mounts all routers, and wires startup/shutdown hooks (DB pool, checkpointer, MCP server processes). Runs under `uvicorn` in dev and behind the async event loop in production. |
| `config.py` | Pydantic `Settings` class loading all environment variables (DB URI, vLLM base URL, Supabase keys, workspace root path, retry ceilings). Single source of truth so no module reads `os.environ` directly. |
| `dependencies.py` | FastAPI dependency-injection providers — yields a DB session, the compiled LangGraph app, and the LLM client into route handlers. Keeps route functions thin and testable. |

### 3.2 `app/api/` — HTTP & streaming interface

| File | What it does |
|---|---|
| `routes/tasks.py` | Endpoints to create a new task (submit a goal + workspace), list tasks, fetch a task's current state, and trigger a resume after approval. Delegates all execution to the compiled agent graph. |
| `routes/workspaces.py` | CRUD endpoints for Workspaces — create/list/delete, each backed by its own memory scope, file directory, and custom instructions per FR-8. |
| `routes/approvals.py` | Endpoint the dashboard calls when the operator clicks Approve/Reject on a pending `human_approval` interrupt. Writes the decision into graph state and resumes execution. |
| `routes/health.py` | Liveness/readiness probes — checks DB connectivity, vLLM endpoint reachability, and MCP server process health. Used by orchestration/monitoring. |
| `routes/stream.py` | Server-Sent-Events endpoint that relays `app.astream()` node-transition events to any connected client, and mirrors the same events into the Supabase realtime channel. |
| `schemas/task.py` | Pydantic request/response models for task creation, status, and history payloads. Validates input before it ever reaches the agent graph. |
| `schemas/workspace.py` | Pydantic models for workspace create/update/list requests and responses, including the file-scope and custom-instruction fields. |
| `schemas/approval.py` | Pydantic models for the approve/reject payload (action description, decision, optional operator note) exchanged with the dashboard. |

### 3.3 `app/agent/` — LangGraph orchestration core

| File | What it does |
|---|---|
| `state.py` | Defines `AgentState(MessagesState)` — the shared clipboard (`messages`, `workspace_dir`, `active_agent`, `error_count`) that every node reads and writes, per PRD Section 7.4. |
| `graph.py` | Builds the `StateGraph`, registers all nodes, sets the entry point, and compiles it with the Postgres checkpointer and `interrupt_before=["human_approval"]`. This is what `main.py` imports and serves. |
| `checkpointer.py` | Wraps `AsyncPostgresSaver` setup/connection-string handling so every node transition is durably persisted, enabling pause/resume across restarts (PRD Section 7.8). |
| `classifiers.py` | LLM-assisted classifier the Supervisor calls to flag whether a proposed action is destructive/irreversible, feeding the routing decision toward `human_approval`. Works alongside, not instead of, the hard deny-list. |
| `nodes/supervisor.py` | The Supervisor node — reads full conversation state and returns a `Command` routing to `developer_agent`, `human_approval`, or `END`, per PRD Section 7.5. |
| `nodes/developer_agent.py` | The Developer Agent node — calls the tool-bound LLM, and either routes to `tool_execution` (if tools were called) or back to `supervisor` (task step complete). |
| `nodes/tool_execution.py` | Executes whatever tool calls the Developer Agent requested via the MCP-backed tool layer, appends results as `ToolMessage`s, and always routes back to `developer_agent`. |
| `nodes/human_approval.py` | The hard-interrupt node — on resume, reads the operator's approve/reject decision from state and routes back into `supervisor` for re-planning or continuation. |
| `prompts/supervisor_prompt.py` | System prompt template defining the Supervisor's routing contract (`EXECUTE:` / `APPROVE:` / final-answer conventions used by `route_from_*` logic embedded in the node). |
| `prompts/developer_prompt.py` | System prompt template constraining the Developer Agent to the bound tool schema and the active workspace scope, reducing tool-call hallucination. |

### 3.4 `app/tools/` — LLM-callable tool layer

| File | What it does |
|---|---|
| `registry.py` | Collects all `@tool`-decorated functions into a single list and binds them to the LLM (`llm.bind_tools(tools)`), giving one place to add/remove agent capabilities. |
| `terminal_tool.py` | `execute_terminal_command` tool — thin wrapper that forwards a shell command to the Terminal MCP server running inside the sandbox and returns captured stdout/stderr. |
| `filesystem_tool.py` | `read_local_file` / `write_local_file` / `list_directory` tools — forward to the File System MCP server, scoped strictly to the active workspace directory. |
| `browser_tool.py` | `navigate`, `click`, `fill_form`, `extract_content` tools — forward to the Browser MCP server (Playwright-backed) for web research tasks (FR-11). |
| `document_tool.py` | `generate_document` tool — builds Excel/Word/Markdown/slide deliverables (via `python-docx`/`openpyxl`/`python-pptx`) and persists them through the filesystem tool (FR-9). |

### 3.5 `app/mcp_servers/` — sandboxed capability servers

| File | What it does |
|---|---|
| `base_server.py` | Shared MCP server scaffolding — request/response schema validation, logging, and workspace-path resolution reused by all concrete servers below. |
| `filesystem_server.py` | Implements read/write/move/list operations, refusing any path that resolves outside the mounted workspace directory (FR-6). |
| `terminal_server.py` | Wraps Python's `subprocess` to run bash commands inside the sandbox container only, capturing output and enforcing the retry/error-count contract. |
| `browser_server.py` | Playwright-driven server exposing navigate/click/fill/extract actions to the Browser tool, run headless inside the sandbox. |

### 3.6 `app/vision/` — "Eyes" subsystem

| File | What it does |
|---|---|
| `vlm_client.py` | Client wrapper around the local vision-language model endpoint (e.g. Qwen2-VL-7B) — sends a screenshot + instruction, returns identified UI elements and click coordinates. |
| `screenshot.py` | Captures and pre-processes screenshots (from Playwright's `page.screenshot()` or the sandbox display) into the format the VLM client expects. |

### 3.7 `app/llm/` — "Brain" model serving

| File | What it does |
|---|---|
| `client.py` | Factory for the `ChatOpenAI`-compatible client pointed at the local vLLM endpoint, used by every agent node that needs a completion. |
| `model_config.py` | Centralizes model name, quantization, temperature, and context-window settings per environment (dev vs. production), so `client.py` stays environment-agnostic. |

### 3.8 `app/memory/` — long-term semantic recall

| File | What it does |
|---|---|
| `vector_store.py` | Thin wrapper around `pgvector` — embeds and stores past actions/file summaries, and performs similarity search against them. |
| `semantic_recall.py` | Queries `vector_store.py` for relevant historical context and injects it into the Supervisor/Developer prompts before a new step, giving the agent memory beyond the current thread. |

### 3.9 `app/db/` — relational persistence

| File | What it does |
|---|---|
| `session.py` | SQLAlchemy async engine and session-factory setup, consumed by `dependencies.py` and the scheduler. |
| `base.py` | Declarative base class all ORM models inherit from; single import point for Alembic autogeneration. |
| `models/workspace.py` | ORM model for a Workspace row — file-scope path, custom instructions, creation metadata. |
| `models/task.py` | ORM model for a Task row — goal text, status, `thread_id` (links to the LangGraph checkpoint), timestamps. |
| `models/approval.py` | ORM model for pending/resolved approval requests — action description, decision, operator, timestamp. |
| `migrations/env.py` | Alembic migration environment configuration, pointed at `db/base.py`'s metadata for autogeneration. |

### 3.10 `app/realtime/` — live dashboard channel

| File | What it does |
|---|---|
| `supabase_client.py` | Publishes step-by-step agent events and pending-approval notifications to Supabase realtime channels, consumed live by the frontend dashboard. |

### 3.11 `app/sandbox/` — execution isolation

| File | What it does |
|---|---|
| `docker_manager.py` | Spins up and tears down the per-workspace Docker container, mounting only that workspace's directory as a volume — the hard security boundary from PRD Section 7.10. |
| `policy.py` | Container-level runtime policy — non-root user, no Docker-socket exposure, no host bind mounts beyond the single workspace volume, resource limits. |

### 3.12 `app/security/` — action-level safety

| File | What it does |
|---|---|
| `deny_list.py` | Hard, pattern-based deny-list of destructive commands/paths (e.g. `rm -rf`, `DROP TABLE`, force-push), enforced independently of model judgement per the Risk #1 mitigation in the PRD. |
| `auth.py` | Single-operator bearer-token check protecting the API and dashboard, since the system still runs a local HTTP server reachable on the LAN. |

### 3.13 `app/scheduler/` — unattended/background execution

| File | What it does |
|---|---|
| `cron_runner.py` | Polls the task queue for due scheduled tasks and kicks off a new graph run for each, enabling FR-4 (scheduled/background execution). |
| `task_queue.py` | Postgres-backed queue table for pending scheduled runs — avoids introducing a new infra dependency (e.g. Redis) beyond what's already in the stack. |

### 3.14 `app/utils/` — cross-cutting helpers

| File | What it does |
|---|---|
| `logger.py` | Structured logging setup — one log line per node transition (node name, timestamp, truncated payload) satisfying the observability NFR in PRD Section 10. |
| `retry.py` | Exponential-backoff retry helper used by `tool_execution.py`, tied to the `error_count` field in `AgentState` and the retry-ceiling in FR-3. |

### 3.15 `scripts/` — operational one-offs

| File | What it does |
|---|---|
| `setup_db.py` | Runs Alembic migrations and creates the `pgvector` extension on a fresh Postgres instance — the first command in Phase 0 setup. |
| `seed_workspace.py` | Bootstraps a new workspace: creates the DB row, the on-disk directory under `workspaces/`, and the associated Docker volume mapping. |
| `run_soak_test.py` | Drives the Phase 5 multi-day soak test — repeatedly submits representative tasks and logs success/failure against the Section 3 success metrics. |

### 3.16 `docker/` — containerization

| File | What it does |
|---|---|
| `Dockerfile.api` | Builds the FastAPI backend image (Python deps, `uvicorn` entrypoint) used for the API/orchestration process itself. |
| `Dockerfile.sandbox` | Builds the minimal execution-sandbox image used per-workspace by `docker_manager.py` — no unnecessary tooling, non-root by default. |
| `docker-compose.yml` | Local orchestration for the always-on services — API, Postgres+`pgvector`, and (optionally) a local vLLM container. Per-workspace sandbox containers are spun up dynamically, not as compose services. |

### 3.17 `tests/` — automated verification

| File | What it does |
|---|---|
| `conftest.py` | Shared pytest fixtures — a throwaway test database, a stubbed LLM client, and a temp workspace directory used across the suite. |
| `test_graph.py` | End-to-end tests running the compiled graph against representative goals (mirrors the Section 8 example flow) and asserting correct termination. |
| `test_tools.py` | Unit tests for each MCP-backed tool, verifying workspace-path scoping is actually enforced (can't escape the sandboxed directory). |
| `test_approval_flow.py` | Verifies destructive actions correctly hard-interrupt at `human_approval` and resume correctly on both Approve and Reject decisions. |
| `test_checkpointing.py` | Kills the process mid-task and asserts the graph resumes from the exact last checkpoint, validating the Section 3 recoverability metric. |

### 3.18 Root config files

| File | What it does |
|---|---|
| `alembic.ini` | Alembic configuration pointing at `app/db/migrations` and the Postgres connection string from `.env`. |
| `requirements.txt` / `pyproject.toml` | Pinned dependencies — `fastapi`, `langgraph`, `langchain-openai`, `sqlalchemy`, `pgvector`, `playwright`, `python-docx`, `openpyxl`, `python-pptx`, etc. |
| `.env.example` | Template for required environment variables (DB URI, vLLM base URL, Supabase keys, workspace root) — copied to `.env` per deployment. |
| `README.md` | Setup instructions: install deps, run migrations, start vLLM, launch the API, and how to run the test suite. |

---

## 4. Frontend — Full Folder Tree

Next.js (App Router) dashboard consuming the backend's REST endpoints and Supabase realtime channel for the live progress / approval UI described in PRD Section 9.

```
frontend/
├── app/
│   ├── layout.tsx                 # root layout, global providers (theme, Supabase client)
│   ├── page.tsx                   # landing / workspace list
│   ├── globals.css                # base styles
│   └── workspaces/
│       ├── page.tsx                # workspace list + create-new form
│       └── [workspaceId]/
│           ├── page.tsx             # single workspace overview (tasks list)
│           └── tasks/
│               └── [taskId]/
│                   └── page.tsx      # live task detail — plan, step timeline, approval prompts
│
├── components/
│   ├── TaskTimeline.tsx           # renders the ordered plan steps and their live status
│   ├── ApprovalModal.tsx          # blocking modal shown when a task hits human_approval
│   ├── LiveLogStream.tsx          # subscribes to the SSE/Supabase channel and tails node events
│   ├── WorkspaceCard.tsx          # summary card for a workspace on the list page
│   ├── PlanStepper.tsx            # visual step indicator (pending / running / done / failed)
│   └── ui/                        # shared low-level primitives (button, modal, badge, etc.)
│
├── hooks/
│   ├── useTaskStream.ts           # subscribes to a task's live event stream
│   └── useSupabaseRealtime.ts     # generic Supabase channel subscription hook
│
├── lib/
│   ├── api.ts                     # typed fetch wrappers around the FastAPI backend routes
│   ├── supabaseClient.ts          # Supabase client instance (anon key, realtime config)
│   └── types.ts                   # shared TypeScript types mirroring the backend Pydantic schemas
│
├── public/                        # static assets
├── styles/                        # additional/shared CSS
├── package.json
├── tsconfig.json
├── next.config.js
└── .env.local.example             # NEXT_PUBLIC_API_URL, NEXT_PUBLIC_SUPABASE_URL/ANON_KEY
```

---

## 5. How the Two Sides Connect

1. Frontend calls `POST /tasks` on the backend (via `lib/api.ts`) to submit a goal against a workspace.
2. Backend compiles/reuses the LangGraph app (`app/agent/graph.py`) and starts `astream()`, persisting every step through `checkpointer.py`.
3. Each node transition is pushed both over `routes/stream.py` (SSE) and `realtime/supabase_client.py` (Supabase channel) — the frontend's `useTaskStream.ts` picks up whichever is configured.
4. If `human_approval` is hit, `ApprovalModal.tsx` renders; the operator's decision posts to `routes/approvals.py`, which resumes the graph from its last checkpoint.
5. On completion, generated documents (from `tools/document_tool.py`) live under that workspace's directory and are surfaced back to the frontend via the workspace file listing.

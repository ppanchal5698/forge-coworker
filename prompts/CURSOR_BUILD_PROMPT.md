# Cursor AI — Full Build Prompt for Forge

Companion to `PRD_Forge_Local_Agent_Platform.md` and `PROJECT_STRUCTURE.md`. This file gives you two things:

- **Section A** — persistent project rules. Save this as `AGENTS.md` in the repo root; Cursor (and Copilot/Antigravity, per your existing multi-assistant governance pattern) reads it automatically as standing context for every session.
- **Section B** — the one-time kickoff prompt. Paste this into Cursor's Composer/Agent mode once `docs/PRD_Forge_Local_Agent_Platform.md`, `docs/PROJECT_STRUCTURE.md`, and this file's Section A (as `AGENTS.md`) are already in the repo.

Both are written in second person, addressed directly to the AI agent — copy them verbatim.

---

## SECTION A — Persistent Project Rules (`AGENTS.md`)

```markdown
# AGENTS.md — Forge

You are building **Forge**, a local, self-hosted autonomous agentic development
platform (FastAPI + LangGraph backend, Next.js frontend). Full spec lives in:

- `docs/PRD_Forge_Local_Agent_Platform.md` — requirements, architecture, roadmap, risks
- `docs/PROJECT_STRUCTURE.md` — the authoritative file/folder manifest and per-file responsibilities

## Source-of-truth hierarchy
When anything conflicts: **PRD > PROJECT_STRUCTURE.md > this file > your own judgement.**
Never silently deviate from the PRD's architecture. In particular:

1. Agent orchestration MUST use the Supervisor/Worker pattern with LangGraph's
   `Command` primitive — every node in `app/agent/nodes/` returns a `Command`
   that sets both the state update and the next node. Do **not** implement
   separate `add_conditional_edges` router functions; that design was
   evaluated and explicitly rejected (see PRD Appendix A).
2. All destructive or irreversible actions MUST pass through
   `app/security/deny_list.py` (hard pattern match) AND
   `app/agent/classifiers.py` (LLM-assisted classification) before reaching
   `human_approval`. Neither check alone is sufficient — implement both.
3. All file and terminal execution MUST go through the MCP server layer in
   `app/mcp_servers/`. Never call `subprocess` or open a file directly from
   anywhere else in the codebase.
4. The Docker sandbox (`app/sandbox/`) must be implemented and verified
   working — a command run inside it cannot touch anything outside the
   mounted workspace directory — **before** wiring any tool that executes
   real commands into the live graph.
5. `app/agent/state.py` is the shared contract between every node. Don't add
   fields to it ad hoc; if a new field is genuinely needed, say so and explain
   why before changing it.
6. Every node transition must be checkpointed (`app/agent/checkpointer.py`).
   Don't add any execution path that can mutate state without going through
   the compiled graph.

## Anti-hallucination protocol
- Before using any LangGraph, MCP-SDK, vLLM, SQLAlchemy, or Playwright API you
  are not fully certain of, verify it against the actually installed version
  (`pip show <package>`, then inspect its source or run `python -c "import x;
  help(x)"`) rather than guessing from training memory — these libraries move
  fast and APIs shift between versions.
- Never invent a package, function, or config key that "sounds right." If you
  cannot verify something exists, say so explicitly and propose how to check,
  rather than writing code against it.
- Mark any non-obvious assumption inline as `# ASSUMPTION: ...` so it's
  greppable for review later.
- Do not fabricate test results or claim a test suite passes without actually
  running it and showing the output.

## File & scope discipline
- Only create files listed in `docs/PROJECT_STRUCTURE.md`. If you believe a
  new file is genuinely required, propose it and explain why before creating
  it — don't silently expand scope.
- Implement each file's responsibility as described in `PROJECT_STRUCTURE.md`
  section 3. Don't merge unrelated responsibilities into one file to save time.

## Testing discipline
- Every new module under `app/` gets a corresponding test under `tests/`
  before its phase is considered done (see `tests/` mapping in
  `PROJECT_STRUCTURE.md` section 3.17).
- Do not move to the next build phase with failing or skipped tests. If a
  test can't pass yet for a legitimate reason (e.g., depends on a later
  phase), mark it `xfail` with a comment explaining why, don't delete it.

## Security discipline
- No hardcoded secrets, ever. All configuration flows through
  `app/config.py` and `.env` (see `.env.example`).
- A sandbox container may only ever have the single relevant workspace
  directory mounted. Never mount the repo root, the Docker socket, or any
  path outside `workspaces/<id>/` into a sandbox.

## Commit discipline
- One logical unit of work per commit. Conventional commit prefixes
  (`feat:`, `fix:`, `test:`, `chore:`, `docs:`). No commented-out dead code
  left in a commit.

## Reporting
- After finishing each phase (see kickoff prompt), stop and report: files
  created/changed, test results (paste actual output), any open
  `# ASSUMPTION` flags, and any deviation from the PRD with justification.
  Wait for explicit confirmation before starting the next phase.
```

---

## SECTION B — Kickoff Prompt (paste into Cursor Composer / Agent mode)

```markdown
Read `docs/PRD_Forge_Local_Agent_Platform.md` and `docs/PROJECT_STRUCTURE.md`
in full before writing any code. `AGENTS.md` in the repo root governs how you
work for the rest of this project — treat it as binding, not optional
guidance.

Build Forge end to end, phase by phase, in the exact order below. After each
phase: run the tests for everything built in that phase, paste the real
output, summarize what you built and any `# ASSUMPTION` flags, and then STOP
and wait for my go-ahead before starting the next phase. Do not skip ahead.
Do not mark a phase done with failing tests.

---

### Phase 0 — Foundations
- Scaffold every file and folder from `PROJECT_STRUCTURE.md` (backend +
  frontend), as empty modules with correct imports/docstrings — no logic yet.
- Implement `app/config.py`, `app/dependencies.py`, `app/db/session.py`,
  `app/db/base.py`, `app/db/models/*`, `app/db/migrations/env.py`.
- Implement `app/llm/client.py` + `model_config.py` against a local vLLM (or
  Ollama, whichever is running) OpenAI-compatible endpoint.
- Implement `app/agent/checkpointer.py` against Postgres.
- Write `docker/docker-compose.yml` (API + Postgres/pgvector), `scripts/setup_db.py`.
- **Exit criteria:** `docker-compose up` brings up Postgres cleanly,
  `scripts/setup_db.py` runs migrations + creates the `pgvector` extension
  without error, `GET /health` (stub is fine) returns 200, and a basic
  checkpoint write/read round-trip test passes.

### Phase 1 — Core Loop (MVP)
- Implement `app/agent/state.py`, `app/agent/graph.py`.
- Implement nodes: `supervisor.py`, `developer_agent.py`, `tool_execution.py`.
  `human_approval.py` can be a stub that always auto-approves for now — real
  logic comes in Phase 2.
- Implement `app/tools/registry.py`, `terminal_tool.py`, `filesystem_tool.py`.
- Implement `app/mcp_servers/base_server.py`, `filesystem_server.py`,
  `terminal_server.py`.
- Implement `app/sandbox/docker_manager.py` and `policy.py` — get this
  actually working and tested before the terminal tool is allowed to run
  anything for real.
- Implement `app/utils/logger.py`, `retry.py`.
- **Exit criteria:** the end-to-end example from PRD Section 8 ("analyze
  these CSVs and build a SQLite database") runs unattended against a real
  test workspace, entirely inside the sandbox, with every step checkpointed.
  `tests/test_graph.py` and `tests/test_tools.py` pass.

### Phase 2 — Human-in-the-Loop
- Implement `app/security/deny_list.py`, `app/agent/classifiers.py`, and the
  real `human_approval.py` node with `interrupt_before`.
- Implement `app/api/routes/approvals.py`, `schemas/approval.py`.
- Implement `app/realtime/supabase_client.py` and wire pending-approval
  events into it.
- **Exit criteria:** `tests/test_approval_flow.py` passes — a destructive
  action test suite (delete, force-push, DROP TABLE style commands) is
  gated 100% of the time, and both Approve and Reject correctly resume the
  graph. `tests/test_checkpointing.py` passes — kill the process mid-task,
  restart, confirm it resumes from the exact last checkpoint.

### Phase 3 — Perception & Browser
- Implement `app/vision/vlm_client.py`, `screenshot.py`.
- Implement `app/mcp_servers/browser_server.py`, `app/tools/browser_tool.py`
  (Playwright-backed, headless, inside the sandbox).
- **Exit criteria:** a real web-research task (per PRD Section 5, use case 3)
  completes end to end using only browser tools.

### Phase 4 — Document Generation
- Implement `app/tools/document_tool.py` (Excel/Word/Markdown/slide output),
  writing through `filesystem_tool.py`.
- **Exit criteria:** generated documents open cleanly in their target apps;
  the in-place revision path works on at least one document type.

### Phase 5 — Production Hardening
- Implement `app/memory/vector_store.py`, `semantic_recall.py`.
- Implement `app/scheduler/cron_runner.py`, `task_queue.py`.
- Implement remaining `app/api/routes/*` (`tasks.py`, `workspaces.py`,
  `stream.py`, `health.py`) and `app/security/auth.py`.
- Write `scripts/seed_workspace.py`, `scripts/run_soak_test.py`.
- Run the full test suite and the soak test script.
- **Exit criteria:** the success metrics in PRD Section 3 are met over the
  soak-test window.

### Frontend build order (start after backend Phase 2 has a working API)
1. Scaffold the Next.js app per `PROJECT_STRUCTURE.md` section 4.
2. `lib/types.ts`, `lib/api.ts`, `lib/supabaseClient.ts` first — get typed
   contracts against the real backend schemas before writing any UI.
3. `hooks/useTaskStream.ts`, `hooks/useSupabaseRealtime.ts`.
4. `components/` (`WorkspaceCard`, `PlanStepper`, `TaskTimeline`,
   `LiveLogStream`, `ApprovalModal`, shared `ui/` primitives).
5. `app/` pages wiring it together — workspace list → workspace detail →
   live task detail with the approval modal.
- **Exit criteria:** a task submitted from the dashboard streams live
  progress, and a destructive-action approval prompt correctly blocks and
  resumes the task from the UI.

---

Begin with Phase 0. Confirm you've read both docs and this file, then start.
```

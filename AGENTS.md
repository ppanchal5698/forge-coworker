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

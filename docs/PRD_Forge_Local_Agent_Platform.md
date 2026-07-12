# Product Requirements Document

## Forge — A Local, Self-Hosted Autonomous Agentic Development Platform

> Independent, self-hosted system inspired by the workflow patterns of cloud agentic assistants (multi-step planning, file/system access, human-in-the-loop approval, tool execution). Not affiliated with, endorsed by, or built from any proprietary source of a commercial product — architecture is derived from open-source frameworks only (LangGraph, MCP, vLLM, Docker, PostgreSQL).

| | |
|---|---|
| **Document status** | Draft v1.0 |
| **Owner** | Parth |
| **Date** | July 12, 2026 |
| **Target environment** | Ubuntu (Acer Predator, RTX 2060 class GPU, single-node local deployment) |
| **Related artifacts** | `AGENTS.md` (AI coding assistant governance), Obsidian multi-agent `CLAUDE.md`, RAG platform (FastAPI + LangGraph + LlamaIndex) |

---

## 1. Overview & Purpose

Forge is a locally-hosted, autonomous multi-step agent platform that plans, executes, verifies, and self-corrects complex knowledge-work and software-engineering tasks with minimal supervision. It replicates the operating model of modern "agentic coworker" products — a planning brain, a perception layer, a set of sandboxed execution tools, and a persistent memory layer — using an entirely open, self-hosted stack.

The system exists to let a single developer delegate multi-hour, multi-step tasks (repo scaffolding, data processing, file organization, report generation, browser research) to an autonomous agent that runs unattended, asks for approval only on destructive or ambiguous actions, and resumes cleanly across restarts.

## 2. Background & Context

Cloud-hosted agentic assistants have demonstrated a workable pattern for autonomous computer-use agents: a "Brain" (planning LLM), "Eyes" (vision-language model for UI perception), "Hands" (sandboxed tool execution via a standardized protocol), and a "Subconscious" (persistent state/memory). Early prototyping (see Appendix A) validated this pattern conceptually but produced a **toy implementation** — a flat, hardcoded `add_conditional_edges` router that does not scale past a handful of branches and does not reflect how production agent systems are actually built today.

This PRD supersedes that prototype and specifies the **production-grade architecture**: a Supervisor/Worker pattern using LangGraph's `Command` primitive for dynamic, co-located routing, backed by asynchronous PostgreSQL checkpointing so the system can run 24/7, pause for human approval, and survive process restarts without losing state.

## 3. Goals & Success Metrics

| Goal | Metric | Target |
|---|---|---|
| Autonomous multi-step completion | % of assigned tasks completed without a routing dead-end or infinite loop | ≥ 90% |
| Safe execution | % of destructive actions (file delete, `git push`, `DROP TABLE`, prod deploy) correctly routed to human approval | 100% |
| Recoverability | Task resumes correctly from last checkpoint after process kill / restart | 100% of tested cases |
| Local hardware fit | Peak VRAM usage of Brain + Eyes models concurrently loaded | ≤ 24 GB |
| Latency | Time from tool result to next agent decision (local vLLM, 32B AWQ) | < 4s p50 |
| Unattended reliability | Background/scheduled task success rate over 7-day soak test | ≥ 95% |
| Error self-recovery | % of failed tool calls that are retried/fixed without human intervention | ≥ 70% |

## 4. Non-Goals

- **Not** building a general-purpose consumer chat product or multi-tenant SaaS — this is a single-user, single-node local system.
- **Not** replicating cloud-vendor UI/branding — no attempt to visually or functionally impersonate a specific commercial product.
- **Not** targeting mobile or cross-device sync in v1 — desktop/web dashboard only.
- **Not** shipping a hardened multi-user permission model in v1 (single trusted operator assumed).
- **Not** attempting full computer-use parity (arbitrary OS-level GUI control) in v1 — browser automation via Playwright is in scope; native desktop-app GUI control is deferred to a later phase.

## 5. Users & Use Cases

**Primary user:** a single full-stack / AI-ML developer running the system on their own Ubuntu workstation.

Representative use cases:
1. "Scaffold a new FastAPI + LangGraph microservice, install dependencies, and run the test suite." (fully unattended)
2. "Read these 50 CSVs in `~/Downloads`, dedupe them, and load them into a local SQLite database." (file + terminal tools only)
3. "Research three competing open-source vector DBs, summarize trade-offs, and write the summary to a Markdown file." (browser + document generation)
4. "Refactor this module, but pause and ask before deleting any files or force-pushing." (human-in-the-loop gate)
5. "Run this data-pipeline job every night at 2 AM and message me a summary." (scheduled/background execution)

## 6. Functional Requirements

Requirements are grouped by capability area, each tagged with priority (**P0** = required for v1 launch, **P1** = fast-follow, **P2** = later phase).

### 6.1 Autonomous Execution & Planning
| ID | Requirement | Priority |
|---|---|---|
| FR-1 | System accepts a single high-level natural-language goal and decomposes it into an ordered, atomic step plan before execution begins. | P0 |
| FR-2 | System executes plan steps sequentially by default, with support for independent steps to run concurrently. | P1 |
| FR-3 | On a failed tool call, system automatically diagnoses the failure and attempts a corrected retry without waiting for the human, up to a configurable retry ceiling. | P0 |
| FR-4 | System supports scheduled/cron-style task execution and can run fully in the background (no attached terminal/UI session required). | P1 |
| FR-5 | System exposes live step-by-step progress via a streaming interface. | P0 |

### 6.2 Local System & File Access
| ID | Requirement | Priority |
|---|---|---|
| FR-6 | System can read, write, rename, move, and batch-organize files within an explicitly granted workspace directory only. | P0 |
| FR-7 | System can ingest and synthesize heterogeneous local files (PDF, CSV, images, office docs), deduplicate, and extract structured data. | P1 |
| FR-8 | Each project is isolated into a "Workspace" with its own memory (conversation + vector context), file scope, and custom instructions. | P0 |

### 6.3 Document Generation
| ID | Requirement | Priority |
|---|---|---|
| FR-9 | System can generate ready-to-use Excel (with formulas), Word/Markdown, and slide-deck outputs. | P1 |
| FR-10 | Generated documents support targeted in-place revision (edit a section without regenerating the whole document). | P2 |

### 6.4 App & Browser Control
| ID | Requirement | Priority |
|---|---|---|
| FR-11 | System can drive a real Chromium browser (navigate, click, fill forms, extract page content) for independent web research. | P1 |
| FR-12 | System integrates with external services (Gmail, Drive, Slack, GitHub) via Model Context Protocol (MCP) servers to pull context or push updates. | P2 |

### 6.5 Architecture & Safety
| ID | Requirement | Priority |
|---|---|---|
| FR-13 | All planning is performed by a single designated "Brain" model; all screen/page perception is performed by a dedicated vision-language "Eyes" model. | P0 |
| FR-14 | All command/file execution runs inside an isolated container with access limited to the explicitly mounted workspace directory. | P0 |
| FR-15 | Any action classified as destructive or irreversible must pause the graph and block on explicit human approval before proceeding. | P0 |
| FR-16 | A task's full state (plan, message history, active step) is durably checkpointed after every node transition, enabling pause/resume across restarts. | P0 |

## 7. System Architecture

### 7.1 High-Level Component Mapping

| Conceptual Role | Local Implementation | Responsibility |
|---|---|---|
| Brain (planning & reasoning) | vLLM serving a 4-bit quantized ~32B coding model (e.g. Qwen2.5-32B-Coder, AWQ/GGUF) | Decompose goals, make tool-routing decisions, self-correct |
| Eyes (visual perception) | Qwen2-VL-7B (or similar VLM) | Parse screenshots, locate UI elements, return click coordinates |
| Hands (execution) | Model Context Protocol (MCP) Python servers | File system, terminal/bash, browser (Playwright) actions |
| Subconscious (memory/state) | PostgreSQL + `pgvector`, LangGraph `AsyncPostgresSaver` | Durable checkpointing, semantic long-term memory |
| Orchestration | LangGraph (Supervisor/Worker, `Command`-based routing) | Cyclic state machine coordinating all of the above |
| Backend/API | FastAPI (async) | Streams agent events, exposes control endpoints |
| Real-time UI channel | Supabase (Postgres + realtime websockets) | Live progress feed, approve/reject UI events |
| Sandbox boundary | Docker (volume-mounted workspace only) | Prevents any action from touching the host filesystem outside scope |

### 7.2 Tech Stack Summary

| Layer | Choice | Rationale |
|---|---|---|
| Agent framework | LangGraph | Native cyclic graphs, built-in persistence, `Command`-based dynamic routing |
| Model serving | vLLM | Maximizes local GPU throughput; OpenAI-compatible API surface |
| Primary model | Qwen2.5-32B-Coder, 4-bit AWQ/GGUF | Strong code/reasoning performance inside a 24 GB VRAM budget |
| Vision model | Qwen2-VL-7B (or LLaVA) | UI element grounding for browser/screen actions |
| Backend | FastAPI | Async-native; streams tool execution logs without blocking |
| State/relational store | PostgreSQL | Checkpoint storage, relational task/run tracking |
| Vector memory | `pgvector` extension | Semantic recall over past actions/files, no extra DB to operate |
| Real-time layer | Supabase | Websocket-driven live progress + approval prompts on top of Postgres |
| Tool protocol | Model Context Protocol (MCP) | Standardized, scoped interface between agent and local capabilities |
| Sandbox | Docker | Workspace-scoped volume mounts isolate execution from host OS |
| Browser automation | Playwright (behind a Browser MCP server) | Reliable, scriptable page navigation and DOM interaction |

### 7.3 Agent Orchestration — Supervisor/Worker Pattern

The graph is **not** a flat set of `add_conditional_edges` routers. Each node returns a `Command` object that atomically (a) updates shared state and (b) specifies the next node — routing logic lives next to the node that produces it, rather than in a separate, hard-to-trace router function. This is the pattern selected after rejecting the initial toy prototype (see Appendix A).

### 7.4 State Schema

```python
from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph import MessagesState

class AgentState(MessagesState):
    """
    MessagesState provides `messages: list` with an automatic append reducer.
    Explicit fields below are added for production tracking.
    """
    workspace_dir: str      # Host-mounted, container-scoped working directory
    active_agent: str       # Name of the node currently holding control
    error_count: int        # Consecutive tool-failure counter, used for retry ceilings
```

### 7.5 Node Specifications

**Supervisor Node** — evaluates the full conversation state and decides which specialist (or human gate) acts next.

```python
async def supervisor_node(state: AgentState) -> Command[Literal["developer_agent", "human_approval", "__end__"]]:
    system_prompt = (
        "You are the orchestrator of an autonomous development loop. "
        "Review the conversation. If code needs to be written or terminal commands run, "
        "route to 'developer_agent'. If a destructive action is proposed, route to 'human_approval'. "
        "If the user's request is completely fulfilled, reply directly and end."
    )
    messages = [{"role": "system", "content": system_prompt}] + state["messages"]
    response = await llm.ainvoke(messages)

    if "APPROVE:" in response.content:
        return Command(goto="human_approval", update={"messages": [response], "active_agent": "supervisor"})
    elif "EXECUTE:" in response.content:
        return Command(goto="developer_agent", update={"messages": [response], "active_agent": "developer_agent"})
    else:
        return Command(goto=END, update={"messages": [response]})
```

**Developer Agent Node** — writes code / issues tool calls; yields control back to the Supervisor when no further tool is needed.

```python
async def developer_agent_node(state: AgentState) -> Command[Literal["tool_execution", "supervisor"]]:
    response = await llm_with_tools.ainvoke(state["messages"])
    if response.tool_calls:
        return Command(goto="tool_execution", update={"messages": [response]})
    else:
        return Command(goto="supervisor", update={"messages": [response]})
```

**Tool Execution Node** — runs the requested MCP-backed tool(s) and always routes back to the Developer Agent to interpret the result.

```python
async def tool_execution_node(state: AgentState) -> Command[Literal["developer_agent"]]:
    last_message = state["messages"][-1]
    tool_responses = []

    for tool_call in last_message.tool_calls:
        if tool_call["name"] == "execute_terminal_command":
            result = execute_terminal_command.invoke(tool_call["args"])
        elif tool_call["name"] == "read_local_file":
            result = read_local_file.invoke(tool_call["args"])
        tool_responses.append(ToolMessage(content=str(result), tool_call_id=tool_call["id"]))

    return Command(goto="developer_agent", update={"messages": tool_responses})
```

**Human Approval Node** — hard-interrupts the graph before any action classified as destructive (see FR-15); resumes the Supervisor with the operator's decision once approved/rejected.

### 7.6 Tool Layer (MCP Interface)

Tools are strictly schema-defined so the model cannot improvise arbitrary side effects; each wraps a scoped, local MCP client.

```python
from langchain_core.tools import tool

@tool
def execute_terminal_command(command: str) -> str:
    """Executes a sandboxed bash command inside the workspace container and returns stdout."""
    ...

@tool
def read_local_file(filepath: str) -> str:
    """Reads the contents of a file within the active workspace only."""
    ...

tools = [execute_terminal_command, read_local_file]
llm_with_tools = llm.bind_tools(tools)
```

At v1 launch, three MCP servers are required:
- **File System MCP** — read/write/traverse within the mounted workspace only.
- **Terminal MCP** — sandboxed `subprocess` wrapper, output captured and streamed.
- **Browser MCP** — Playwright-driven navigation, clicking, form-fill, and content extraction.

### 7.7 Model Serving Layer

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    base_url="http://localhost:8000/v1",
    api_key="local-execution",
    model="Qwen/Qwen2.5-32B-Coder-AWQ",
    temperature=0.1,   # low temperature for deterministic planning/coding
)
```

vLLM (or Ollama for simpler local dev) serves the quantized model behind an OpenAI-compatible endpoint. Quantization to 4-bit (AWQ/GGUF) keeps the model within a 24 GB VRAM budget while leaving headroom for a large context window and the concurrently-loaded vision model.

### 7.8 Persistence & Checkpointing

```python
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

DB_URI = "postgresql+psycopg://postgres:password@localhost:5432/agent_memory"

async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
    await checkpointer.setup()
    app = builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["human_approval"],   # hard pause before destructive actions
    )
```

Every node transition is persisted to Postgres, keyed by `thread_id`. This is what allows a task to be paused for approval, survive a process restart, and be resumed exactly where it left off — and allows multiple independent workspaces/tasks to run concurrently against the same database, isolated by thread.

### 7.9 Backend & Real-Time Layer

FastAPI wraps the compiled graph and exposes an async streaming endpoint:

```python
config = {"configurable": {"thread_id": "workspace_setup_123"}}
async for event in app.astream(initial_state, config=config, stream_mode="values"):
    last_message = event["messages"][-1]
    # forward to Supabase realtime channel for live UI updates
```

Supabase (Postgres + realtime websockets) sits on top of this stream to power a dashboard: live step-by-step progress, and an Approve/Reject control that resolves the `human_approval` interrupt.

### 7.10 Sandboxing

All Terminal and File System MCP servers run inside a Docker container with only the target project directory mounted as a volume. A hallucinated destructive command (e.g. `rm -rf /`) can only affect the disposable container filesystem — the host machine is unreachable from inside the sandbox boundary by construction, not by model discipline.

## 8. End-to-End Example Flow

Goal: *"Analyze these 50 CSVs in my Downloads folder and build an SQLite database."*

1. **Supervisor** reads the goal, determines execution is needed, routes to `developer_agent`.
2. **Developer Agent** calls `read_local_file`/directory-listing tools to inspect the CSVs → routes to `tool_execution`.
3. **Tool Execution** runs the File System MCP call inside the sandbox, appends the raw result to state, routes back to `developer_agent`.
4. **Developer Agent** reads the result, writes the schema + insert logic, calls `execute_terminal_command` → routes to `tool_execution` again.
5. **Tool Execution** runs the command, appends stdout to state, routes back to `developer_agent`.
6. **Developer Agent** sees no further tool calls are needed, yields control to `supervisor`.
7. **Supervisor** confirms the goal is fulfilled, returns a final natural-language summary, routes to `END`.

Every arrow above is a durable checkpoint write — the task can be killed and resumed after any step without redoing prior work.

## 9. Human-in-the-Loop Approval Workflow

1. Supervisor or Developer Agent classifies an action as destructive/irreversible (file deletion, force-push, schema drop, production deploy, sending external communications).
2. Graph execution hard-interrupts at `human_approval` (`interrupt_before`).
3. State is persisted; a websocket event is pushed to the dashboard.
4. Operator reviews the pending action and clicks Approve/Reject.
5. The decision is written back into state (`human_feedback`); graph resumes into `supervisor`, which either proceeds or re-plans.

## 10. Non-Functional Requirements

| Category | Requirement |
|---|---|
| Performance | p50 decision latency < 4s on local vLLM w/ 32B AWQ model; p50 tool round-trip < 1s for file/terminal ops |
| Hardware | Brain + Eyes models must co-reside within 24 GB VRAM; graceful degradation (Eyes model unloaded) if budget exceeded |
| Scalability | Multiple concurrent workspaces via distinct `thread_id`s against one Postgres instance |
| Reliability | Automatic retry on tool failure up to a configurable `error_count` ceiling, then escalate to human |
| Security | No execution path may touch the host filesystem outside the mounted workspace; all destructive actions gated (FR-15) |
| Observability | Every node transition streamed to the FastAPI/Supabase layer with node name, timestamp, and truncated payload |
| Portability | Model endpoint is OpenAI-API-compatible so vLLM can be swapped for Ollama or a hosted endpoint without graph changes |

## 11. Phased Roadmap

| Phase | Scope | Exit Criteria |
|---|---|---|
| **Phase 0 — Foundations** | Stand up vLLM + quantized model; Postgres + `AsyncPostgresSaver`; base FastAPI skeleton | Model reachable via OpenAI-compatible endpoint; checkpoint round-trip test passes |
| **Phase 1 — Core Loop (MVP)** | Supervisor + Developer Agent + Tool Execution nodes; File System & Terminal MCP servers; Docker sandbox | End-to-end example (Section 8) completes unattended on a real workspace |
| **Phase 2 — Human-in-the-Loop** | `human_approval` node, `interrupt_before`, Supabase realtime approve/reject UI | Destructive-action test suite: 100% correctly gated |
| **Phase 3 — Perception & Browser** | Vision-language "Eyes" model, Browser MCP (Playwright) | Agent completes a web-research task end-to-end using only browser tools |
| **Phase 4 — Document Generation** | Excel/Word/Markdown/slide output tools, in-place revision support | Generated deliverables open cleanly in target apps; revision loop verified |
| **Phase 5 — Production Hardening** | Scheduling/background execution, multi-workspace concurrency, 7-day soak test, retry/error-recovery tuning | Success metrics in Section 3 met over soak-test window |

## 12. Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Model misclassifies a destructive action as safe | Data loss | Maintain an explicit deny-list of command/file patterns enforced at the MCP layer, independent of model judgement |
| VRAM OOM when Brain + Eyes models co-load | Task failure / crash | Quantize aggressively (4-bit); lazy-load Eyes model only when a visual step is queued |
| Browser automation fragility (page structure changes) | Silent task failure | Verifier step checks page state post-action before advancing; retry with re-navigation |
| Long-running threads bloat state/context | Latency degradation, context overflow | Periodic summarization/compaction of `messages` history into the vector memory store |
| Postgres unavailable | Checkpointing fails, task cannot pause/resume | Local Postgres as a systemd-managed service with health checks; document manual recovery procedure |
| Sandbox escape via crafted command | Host compromise | Container runs as non-root with no host bind mounts beyond the single workspace volume; no Docker socket exposed inside the container |
| Model license terms change or are ambiguous for the chosen weights | Legal/compliance risk | Track model license explicitly per deployment; re-verify before any external distribution |

## 13. Alternatives Considered (Rejected)

**Flat conditional-edge router (initial prototype).** An earlier draft used a single `StateGraph` with all routing centralized in `add_conditional_edges` router functions (e.g. `route_from_orchestrator`, `route_from_verifier`) and dedicated `planner_node` / `orchestrator_node` / `verifier_node` / `computer_use_node` / `terminal_file_node` nodes. This was rejected for v1 because:
- Routing logic lived far from the nodes that produced the routing decision, making the graph hard to trace and extend.
- Adding a new branch required touching a shared router function, increasing merge conflicts and regression risk as the graph grows.
- It does not compose cleanly with dynamic, model-decided routing at scale.

The Supervisor/Worker + `Command`-based pattern in Section 7 is the adopted replacement. The rejected version is retained here only for historical context.

## 14. Open Questions

1. Should the Eyes/vision model be always-loaded or lazy-loaded per task, given VRAM pressure?
2. What is the exact deny-list of commands/paths enforced at the MCP layer (needs a concrete first draft before Phase 1 exit)?
3. Ollama vs. vLLM for local dev loop iteration speed vs. production throughput — pick one as default for Phase 0, or support both via the OpenAI-compatible interface?
4. What retry ceiling (`error_count` threshold) balances autonomy against runaway loops?
5. Scope of external MCP integrations (Gmail/Drive/Slack/GitHub) for Phase 4 — which are must-have vs. nice-to-have?

## Appendix A — Prior Iteration (For Reference Only)

The first design pass used a rigid `planner → orchestrator → {computer_use | terminal_file | human_approval} → verifier` cycle with all branching centralized in separate router functions. It correctly established the four-role mental model (Brain/Eyes/Hands/Subconscious) and the need for Postgres-backed checkpointing with `interrupt_before`, both of which carried forward into this PRD. It was explicitly flagged as "too vague and toy-like" and superseded by the Supervisor/Worker `Command`-routing architecture specified in Section 7.

## Appendix B — Glossary

- **MCP (Model Context Protocol):** open specification for exposing scoped local capabilities (file system, terminal, browser) to an LLM agent as callable tools.
- **Checkpointing:** durable persistence of graph state after each node transition, enabling pause/resume.
- **`Command` primitive:** LangGraph object returned by a node that atomically updates state and specifies the next node, replacing separate router functions.
- **AWQ / GGUF:** post-training quantization formats used to shrink model weights (here, to 4-bit) for local GPU deployment.
- **Interrupt-before:** LangGraph compile-time setting that hard-pauses execution immediately prior to a named node, used here to gate destructive actions on human approval.

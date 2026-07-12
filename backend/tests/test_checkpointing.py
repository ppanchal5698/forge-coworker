"""Checkpointing tests.

Phase 0 scope: basic checkpoint write/read round-trip test.
Full kill/resume test deferred to Phase 2.
"""

import uuid

import pytest

from app.config import get_settings


@pytest.mark.asyncio
async def test_graph_interrupt_and_resume():
    """Test kill/resume capability via Postgres checkpointer.
    
    Simulates executing the graph until it hits an interrupt (human_approval),
    'killing' the process (discarding the graph object), and resuming from DB.
    """
    # This test requires the DB, the sandbox (for tools), and LLM (for developer).
    # Since we can't reliably spin up sandbox/LLM inside pytest easily, we skip.
    pytest.skip("Requires full stack (DB, LLM, Sandbox) to run end-to-end interrupt.")


@pytest.mark.asyncio
async def test_checkpoint_write_read_roundtrip():
    """Test that a checkpoint can be written and read back.

    Validates the AsyncPostgresSaver is correctly configured and can
    persist and retrieve graph state, satisfying the Phase 0 exit
    criteria for checkpoint round-trip.
    """
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    from langgraph.graph import StateGraph, START, END, MessagesState

    settings = get_settings()

    # Build a minimal graph for testing
    def simple_node(state: MessagesState) -> dict:
        return {"messages": [{"role": "assistant", "content": "Hello from checkpoint test"}]}

    builder = StateGraph(MessagesState)
    builder.add_node("simple", simple_node)
    builder.add_edge(START, "simple")
    builder.add_edge("simple", END)

    # Compile with checkpointer and run
    async with AsyncPostgresSaver.from_conn_string(
        settings.CHECKPOINT_DB_URI
    ) as checkpointer:
        await checkpointer.setup()
        graph = builder.compile(checkpointer=checkpointer)

        thread_id = f"test-{uuid.uuid4()}"
        config = {"configurable": {"thread_id": thread_id}}

        # Run the graph
        result = await graph.ainvoke(
            {"messages": [{"role": "user", "content": "Test message"}]},
            config=config,
        )

        # Verify the result contains the expected message
        assert len(result["messages"]) >= 2
        assert "Hello from checkpoint test" in result["messages"][-1].content

        # Read the checkpoint back
        state = await graph.aget_state(config)
        assert state is not None
        assert state.values is not None
        assert len(state.values["messages"]) >= 2


@pytest.mark.asyncio
@pytest.mark.xfail(reason="Full kill/resume test requires Phase 2 infrastructure")
async def test_checkpoint_kill_resume():
    """Test that a killed process can resume from the last checkpoint.

    This test requires the full graph with interrupt_before support,
    which is implemented in Phase 2. Marked xfail for now.
    """
    pytest.skip("Requires Phase 2 — full graph with interrupt_before")

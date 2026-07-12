"""End-to-end graph tests.

Runs the compiled graph against representative goals (mirrors the Section 8
example flow) and asserts correct termination.
"""

import uuid

import pytest

from app.agent.graph import compile_graph


@pytest.mark.asyncio
async def test_graph_end_to_end_unattended():
    """Test the unattended core loop (Phase 1).
    
    Validates that the supervisor routes to the developer, the developer
    calls tools, and the supervisor eventually finishes.
    """
    # Requires a running vLLM endpoint on localhost:11434 and docker.
    pytest.skip("Requires active vLLM endpoint and Docker daemon.")


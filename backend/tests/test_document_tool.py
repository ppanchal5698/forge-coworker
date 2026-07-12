"""Document tool unit tests."""

import pytest
from pathlib import Path

# Need to mark these as requiring sandbox environment, just like the other tools.
@pytest.mark.asyncio
async def test_generate_documents(temp_workspace: Path):
    """Test generating different document formats."""
    pytest.skip("Requires Docker and forge-sandbox:latest image")

@pytest.mark.asyncio
async def test_edit_document(temp_workspace: Path):
    """Test in-place editing of documents."""
    pytest.skip("Requires Docker and forge-sandbox:latest image")

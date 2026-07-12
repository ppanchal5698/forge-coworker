"""Browser integration tests.

Verifies the headless Playwright browser can spin up via the FastMCP server
inside the sandbox container.
"""

import pytest

from app.tools.browser_tool import browser_navigate, browser_screenshot
from app.vision.screenshot import optimize_screenshot


@pytest.mark.asyncio
async def test_browser_server_sandbox_lifecycle():
    """Verify we can navigate and take a screenshot via the sandboxed MCP server."""
    # Requires docker daemon and the forge-sandbox image built with playwright deps.
    pytest.skip("Requires Docker and forge-sandbox:latest with Playwright.")


def test_screenshot_optimization():
    """Verify that the Pillow optimization resizes large base64 images."""
    import base64
    import io
    from PIL import Image

    # Create a dummy large image (2000x2000)
    img = Image.new("RGB", (2000, 2000), color="red")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    original_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    
    # Optimize it (default max_width is 1280)
    optimized_b64 = optimize_screenshot(original_b64)
    
    # Verify dimensions are reduced
    opt_data = base64.b64decode(optimized_b64)
    opt_img = Image.open(io.BytesIO(opt_data))
    
    assert opt_img.width == 1280
    assert opt_img.height == 1280  # Since original was 1:1 aspect ratio
    assert opt_img.format == "JPEG"  # Converted to JPEG for compression

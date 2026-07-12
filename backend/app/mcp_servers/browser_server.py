"""Browser MCP server.

Provides Playwright headless browser automation tools to the developer agent,
running securely inside the sandbox container.
"""

import asyncio
import base64
from typing import Optional

from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright, Browser, Page, Playwright

mcp = FastMCP("browser")

# Global state for the Playwright session
_playwright: Optional[Playwright] = None
_browser: Optional[Browser] = None
_page: Optional[Page] = None


async def get_page() -> Page:
    """Lazy initialize the Playwright browser and return the active page."""
    global _playwright, _browser, _page
    
    if _page is not None and not _page.is_closed():
        return _page
        
    if _playwright is None:
        _playwright = await async_playwright().start()
        
    if _browser is None:
        _browser = await _playwright.chromium.launch(headless=True)
        
    _page = await _browser.new_page()
    # Standard viewport for consistent screenshots
    await _page.set_viewport_size({"width": 1280, "height": 800})
    return _page


@mcp.tool()
async def navigate(url: str) -> str:
    """Navigate the browser to a specific URL.
    
    Args:
        url: The URL to navigate to (must include http/https).
    """
    try:
        page = await get_page()
        await page.goto(url, wait_until="networkidle", timeout=15000)
        return f"Successfully navigated to {url}. Title: {await page.title()}"
    except Exception as e:
        return f"Navigation failed: {str(e)}"


@mcp.tool()
async def take_screenshot(full_page: bool = False) -> str:
    """Take a screenshot of the current page.
    
    Args:
        full_page: Whether to capture the entire scrollable page (True) or just the viewport (False).
    
    Returns:
        A Base64 encoded string of the PNG screenshot.
    """
    try:
        page = await get_page()
        screenshot_bytes = await page.screenshot(full_page=full_page, type="png")
        b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
        return f"SCREENSHOT_BASE64:{b64}"
    except Exception as e:
        return f"Screenshot failed: {str(e)}"


@mcp.tool()
async def extract_text() -> str:
    """Extract all visible text from the current page body."""
    try:
        page = await get_page()
        text = await page.evaluate("document.body.innerText")
        # Truncate to avoid blowing up the context window too easily
        if len(text) > 10000:
            text = text[:10000] + "\n...[TRUNCATED]"
        return text
    except Exception as e:
        return f"Text extraction failed: {str(e)}"


@mcp.tool()
async def click_element(selector: str) -> str:
    """Click an element on the page matching the CSS selector.
    
    Args:
        selector: The CSS selector of the element to click.
    """
    try:
        page = await get_page()
        await page.click(selector, timeout=5000)
        # Wait a moment for dynamic content
        await asyncio.sleep(1)
        return f"Clicked element matching '{selector}'"
    except Exception as e:
        return f"Click failed: {str(e)}"


@mcp.tool()
async def fill_input(selector: str, text: str) -> str:
    """Fill a text input field on the page.
    
    Args:
        selector: The CSS selector of the input field.
        text: The text to type into the field.
    """
    try:
        page = await get_page()
        await page.fill(selector, text, timeout=5000)
        return f"Filled input '{selector}' with text."
    except Exception as e:
        return f"Fill input failed: {str(e)}"


if __name__ == "__main__":
    mcp.run()

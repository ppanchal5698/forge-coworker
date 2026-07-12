"""Vision tool.

LangChain `@tool` wrapper exposing the VLM capabilities to the developer agent.
"""

from langchain_core.tools import tool

from app.vision.vlm_client import analyze_image


@tool
async def vision_analyze(screenshot_result: str, prompt: str) -> str:
    """Analyze a screenshot taken by the browser.
    
    Args:
        screenshot_result: The exact string returned by the `browser_screenshot` tool 
                           (which starts with "SCREENSHOT_BASE64:").
        prompt: A clear, specific question or instruction about what to analyze in the image.
    """
    if not screenshot_result.startswith("SCREENSHOT_BASE64:"):
        return "Error: screenshot_result must be the exact return value from browser_screenshot."
        
    b64_str = screenshot_result.replace("SCREENSHOT_BASE64:", "")
    
    # Call the VLM client
    return await analyze_image(b64_str, prompt)

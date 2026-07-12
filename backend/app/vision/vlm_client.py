"""Vision Client.

Communicates with a multimodal LLM to analyze screenshots.
Expects the LLM endpoint to support standard OpenAI vision schema.
"""

from langchain_core.messages import HumanMessage

from app.llm.client import get_llm
from app.vision.screenshot import optimize_screenshot


async def analyze_image(base64_image: str, prompt: str) -> str:
    """Analyze a base64 encoded image using the VLM.
    
    Args:
        base64_image: The raw or optimized base64 string of the image.
        prompt: Instructions for what to look for in the image.
    """
    # Optimize the image to save tokens before sending
    optimized_b64 = optimize_screenshot(base64_image)
    
    llm = get_llm()
    
    # Standard multi-modal LangChain schema
    message = HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{optimized_b64}"},
            },
        ]
    )
    
    try:
        response = await llm.ainvoke([message])
        return str(response.content)
    except Exception as e:
        return f"Vision analysis failed: {str(e)}"

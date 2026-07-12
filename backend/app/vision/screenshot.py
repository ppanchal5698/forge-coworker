"""Screenshot optimization.

Resizes and compresses raw screenshots from Playwright before sending them
to the VLM to respect context window limits and save inference time.
"""

import base64
import io

from PIL import Image


def optimize_screenshot(base64_img: str, max_width: int = 1280) -> str:
    """Resize and compress a base64 encoded image.
    
    Args:
        base64_img: The original base64 encoded image string.
        max_width: The maximum width to scale down to (maintaining aspect ratio).
        
    Returns:
        A new base64 string of the optimized image.
    """
    # Remove any data URI prefix if it exists
    if base64_img.startswith("data:image"):
        base64_img = base64_img.split(",")[1]
        
    img_data = base64.b64decode(base64_img)
    img = Image.open(io.BytesIO(img_data))
    
    # Resize if width exceeds max_width
    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
        
    # Convert to RGB if necessary (e.g. RGBA from screenshot)
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')
        
    # Compress and encode
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=75)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

"""Health check endpoints.

Liveness/readiness probes — checks DB connectivity, vLLM endpoint
reachability, and MCP server process health.
"""

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.dependencies import get_db_session

router = APIRouter(tags=["health"])


@router.get("/health", response_model=dict)
async def health_check(
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Liveness/readiness probe.

    Checks database connectivity and returns overall health status.
    """
    settings = get_settings()
    checks = {
        "status": "ok",
        "database": "unknown",
        "llm": "unknown",
        "supabase": "unknown",
    }

    # Check database connectivity
    try:
        result = await session.execute(text("SELECT 1"))
        result.scalar()
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
        checks["status"] = "degraded"

    # Check OpenAI-compatible LLM endpoint.
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.resolved_llm_base_url}/models")
            if response.status_code < 400:
                checks["llm"] = "ok"
            else:
                checks["llm"] = f"error: status={response.status_code}"
                checks["status"] = "degraded"
    except Exception as e:
        checks["llm"] = f"error: {str(e)}"
        checks["status"] = "degraded"

    # Check Supabase if configured.
    if settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY:
        try:
            headers = {
                "apikey": settings.SUPABASE_ANON_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_ANON_KEY}",
            }
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{settings.SUPABASE_URL}/rest/v1/",
                    headers=headers,
                )
                if response.status_code < 400:
                    checks["supabase"] = "ok"
                else:
                    checks["supabase"] = f"error: status={response.status_code}"
                    checks["status"] = "degraded"
        except Exception as e:
            checks["supabase"] = f"error: {str(e)}"
            checks["status"] = "degraded"
    else:
        checks["supabase"] = "disabled"

    return checks

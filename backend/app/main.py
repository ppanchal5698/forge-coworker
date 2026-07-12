"""FastAPI application entrypoint.

Creates the app instance, mounts all routers, and wires startup/shutdown hooks
(DB pool, checkpointer, MCP server processes). Runs under uvicorn in dev and
behind the async event loop in production.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Depends

from app.db.session import dispose_engine, get_engine
from app.scheduler.cron_runner import start_cron_runner, stop_cron_runner
from app.security.auth import verify_token


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.

    Startup: initializes the database engine.
    Shutdown: disposes the engine and releases all connections.
    """
    # Startup: ensure engine is created
    get_engine()
    start_cron_runner()
    yield
    # Shutdown: clean up database connections
    stop_cron_runner()
    await dispose_engine()


app = FastAPI(
    title="Forge",
    description="Local, self-hosted autonomous agentic development platform",
    version="0.1.0",
    lifespan=lifespan,
    dependencies=[Depends(verify_token)],
)

# CORS middleware — permissive for local dev, tighten in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount route modules
from app.api.routes.health import router as health_router  # noqa: E402
from app.api.routes.approvals import router as approvals_router  # noqa: E402
from app.api.routes.tasks import router as tasks_router  # noqa: E402
from app.api.routes.workspaces import router as workspaces_router  # noqa: E402
from app.api.routes.stream import router as stream_router  # noqa: E402

app.include_router(health_router)
app.include_router(approvals_router)
app.include_router(tasks_router)
app.include_router(workspaces_router)
app.include_router(stream_router)

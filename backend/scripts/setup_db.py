"""Database setup script.

Runs Alembic migrations and creates the pgvector extension on a fresh
Postgres instance — the first command in Phase 0 setup.

Usage:
    python scripts/setup_db.py
"""

import asyncio
import subprocess
import sys
from pathlib import Path

import asyncpg


async def create_pgvector_extension(db_uri: str) -> None:
    """Create the pgvector extension if it doesn't already exist."""
    # Convert the URI to asyncpg format (strip driver prefix if present)
    conn_uri = db_uri
    for prefix in ["postgresql+asyncpg://", "postgresql+psycopg://", "postgresql://"]:
        if conn_uri.startswith(prefix):
            conn_uri = "postgresql://" + conn_uri[len(prefix):]
            break

    conn = await asyncpg.connect(conn_uri)
    try:
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        print("✓ pgvector extension created (or already exists)")
    finally:
        await conn.close()


async def verify_tables(db_uri: str) -> None:
    """Verify that the expected tables exist after migration."""
    conn_uri = db_uri
    for prefix in ["postgresql+asyncpg://", "postgresql+psycopg://", "postgresql://"]:
        if conn_uri.startswith(prefix):
            conn_uri = "postgresql://" + conn_uri[len(prefix):]
            break

    conn = await asyncpg.connect(conn_uri)
    try:
        tables = await conn.fetch(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        )
        table_names = [row["tablename"] for row in tables]
        print(f"✓ Tables in database: {', '.join(sorted(table_names))}")

        expected = {"workspaces", "tasks", "approvals", "alembic_version"}
        missing = expected - set(table_names)
        if missing:
            print(f"⚠ Missing expected tables: {', '.join(missing)}")
        else:
            print("✓ All expected tables present")
    finally:
        await conn.close()


def run_migrations() -> None:
    """Run Alembic migrations (upgrade head)."""
    backend_dir = Path(__file__).parent.parent
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=str(backend_dir),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"✗ Alembic migration failed:\n{result.stderr}")
        sys.exit(1)
    print("✓ Alembic migrations applied successfully")
    if result.stdout.strip():
        print(f"  {result.stdout.strip()}")


async def main() -> None:
    """Run the full database setup sequence."""
    # Load settings
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from app.config import get_settings

    settings = get_settings()
    db_uri = settings.DATABASE_URL

    print("=" * 60)
    print("Forge — Database Setup")
    print("=" * 60)

    # Step 1: Create pgvector extension
    print("\n[1/3] Creating pgvector extension...")
    await create_pgvector_extension(db_uri)

    # Step 2: Run Alembic migrations
    print("\n[2/3] Running Alembic migrations...")
    run_migrations()

    # Step 3: Verify tables
    print("\n[3/3] Verifying tables...")
    await verify_tables(db_uri)

    print("\n" + "=" * 60)
    print("Database setup complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

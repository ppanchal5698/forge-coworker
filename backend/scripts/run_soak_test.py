#!/usr/bin/env python
"""Run soak test.

Submits multiple tasks concurrently via the HTTP API, polling for their completion
to measure success rate and stability over a continuous period.
"""

import asyncio
import httpx
import os
import sys
import time
from pathlib import Path

# Add backend to path to import settings
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import get_settings

settings = get_settings()
API_BASE = "http://127.0.0.1:8000"
TOKEN = settings.API_BEARER_TOKEN
HEADERS = {"Authorization": f"Bearer {TOKEN}"}


async def submit_task(client: httpx.AsyncClient, workspace_id: str, goal: str) -> str:
    """Submit a task and return its ID."""
    response = await client.post(
        f"{API_BASE}/tasks",
        json={"workspace_id": workspace_id, "goal": goal},
        headers=HEADERS
    )
    response.raise_for_status()
    return response.json()["id"]


async def wait_for_task(client: httpx.AsyncClient, task_id: str, timeout: int = 600) -> str:
    """Poll task status until completion or timeout."""
    start = time.time()
    while time.time() - start < timeout:
        response = await client.get(f"{API_BASE}/tasks/{task_id}", headers=HEADERS)
        response.raise_for_status()
        status = response.json()["status"]
        if status in ("completed", "failed", "awaiting_approval"):
            return status
        await asyncio.sleep(2)
    return "timeout"


async def run_soak_test():
    """Main soak test loop."""
    print("Starting soak test...")
    
    async with httpx.AsyncClient() as client:
        # 1. Create a workspace
        print("Creating workspace...")
        resp = await client.post(
            f"{API_BASE}/workspaces",
            json={"name": "Soak Test Workspace", "custom_instructions": "Be brief."},
            headers=HEADERS
        )
        resp.raise_for_status()
        workspace_id = resp.json()["id"]
        print(f"Workspace created: {workspace_id}")
        
        # 2. Submit concurrent tasks
        goals = [
            "Write a Python script that prints hello world.",
            "List all files in the workspace directory.",
            "Create a Markdown file called notes.md with a list of planets.",
            "Create a new directory called 'data'.",
            "Write a simple calculator script in Python."
        ]
        
        task_ids = []
        for i, goal in enumerate(goals):
            print(f"Submitting task {i+1}: {goal}")
            tid = await submit_task(client, workspace_id, goal)
            task_ids.append(tid)
            
        print("All tasks submitted. Waiting for completion...")
        
        # 3. Wait for all
        results = await asyncio.gather(
            *[wait_for_task(client, tid) for tid in task_ids]
        )
        
        # 4. Report
        print("\n--- Soak Test Results ---")
        successes = results.count("completed") + results.count("awaiting_approval")
        failures = results.count("failed") + results.count("timeout")
        total = len(results)
        
        for i, res in enumerate(results):
            print(f"Task {i+1} ({task_ids[i]}): {res}")
            
        print(f"\nSuccess Rate: {(successes/total)*100:.1f}%")
        
        if successes == total:
            print("Soak test passed successfully.")
        else:
            print("Soak test had failures.")


if __name__ == "__main__":
    # Give the server a moment to start if run in a script
    time.sleep(2)
    asyncio.run(run_soak_test())

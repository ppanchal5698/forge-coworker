"""Approvals API routes.

Endpoints for fetching and resolving pending human-in-the-loop approvals.
Resolving an approval resumes the paused LangGraph execution.
"""

import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.checkpointer import get_checkpointer
from app.agent.graph import compile_graph
from app.api.schemas.approval import ApprovalDecisionUpdate, ApprovalResponse
from app.db.models.approval import Approval, ApprovalDecision
from app.db.models.task import Task, TaskStatus
from app.db.session import get_session_factory
from app.dependencies import get_db_session

router = APIRouter(prefix="/approvals", tags=["approvals"])


async def resume_graph_background(thread_id: str, decision: str):
    """Resume a paused LangGraph execution in the background."""
    factory = get_session_factory()
    try:
        async with get_checkpointer() as checkpointer:
            graph = compile_graph(checkpointer=checkpointer)
            config = {"configurable": {"thread_id": thread_id}}

            # Ensure we only resume if the graph is actually waiting for approval.
            state_snapshot = await graph.aget_state(config)
            if not state_snapshot.next or "human_approval" not in state_snapshot.next:
                return

            async with factory() as session:
                task_stmt = select(Task).where(Task.thread_id == thread_id)
                task_result = await session.execute(task_stmt)
                task = task_result.scalar_one_or_none()
                if task:
                    task.status = TaskStatus.RUNNING
                    await session.commit()

            # Inject the human's decision into the state
            await graph.aupdate_state(
                config,
                {
                    "human_feedback": decision,
                    "approval_decision": decision,
                },
            )

            # Resume the graph by passing None to the paused node
            async for _ in graph.astream(None, config=config, stream_mode="values"):
                pass

            state_snapshot = await graph.aget_state(config)

            async with factory() as session:
                task_stmt = select(Task).where(Task.thread_id == thread_id)
                task_result = await session.execute(task_stmt)
                task = task_result.scalar_one_or_none()
                if not task:
                    return

                if state_snapshot.next and "human_approval" in state_snapshot.next:
                    task.status = TaskStatus.AWAITING_APPROVAL
                else:
                    task.status = TaskStatus.COMPLETED
                await session.commit()
    except Exception:
        async with factory() as session:
            task_stmt = select(Task).where(Task.thread_id == thread_id)
            task_result = await session.execute(task_stmt)
            task = task_result.scalar_one_or_none()
            if task:
                task.status = TaskStatus.FAILED
                await session.commit()


@router.post("/{approval_id}/resolve", response_model=ApprovalResponse)
async def resolve_approval(
    approval_id: UUID,
    payload: ApprovalDecisionUpdate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session),
) -> Approval:
    """Resolve a pending approval and resume the associated task."""
    
    # 1. Fetch the approval record and its associated task
    stmt = select(Approval).where(Approval.id == approval_id).with_for_update()
    result = await session.execute(stmt)
    approval = result.scalar_one_or_none()
    
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
        
    if approval.decision != ApprovalDecision.PENDING:
        if approval.decision == payload.decision:
            return approval
        raise HTTPException(status_code=409, detail="Approval already resolved with a different decision")
        
    if payload.decision == ApprovalDecision.PENDING:
        raise HTTPException(status_code=400, detail="Cannot resolve to PENDING status")
        
    task_stmt = select(Task).where(Task.id == approval.task_id).with_for_update()
    task_result = await session.execute(task_stmt)
    task = task_result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Associated task not found")
        
    # 2. Update the approval record
    approval.decision = payload.decision
    approval.operator_note = payload.operator_note
    approval.resolved_at = datetime.datetime.now(datetime.timezone.utc)

    task.status = TaskStatus.RUNNING
    
    await session.commit()
    await session.refresh(approval)
    
    # 3. Resume the graph in the background
    background_tasks.add_task(
        resume_graph_background, 
        thread_id=task.thread_id, 
        decision=payload.decision.value
    )
    
    return approval

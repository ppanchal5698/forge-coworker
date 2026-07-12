"""Approval API schemas.

Pydantic models for the Approval resource.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.db.models.approval import ApprovalDecision


class ApprovalResponse(BaseModel):
    """Schema for returning an approval record."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    task_id: UUID
    action_description: str
    decision: ApprovalDecision
    operator_note: Optional[str]
    created_at: datetime
    resolved_at: Optional[datetime]


class ApprovalDecisionUpdate(BaseModel):
    """Payload for resolving a pending approval."""
    
    decision: ApprovalDecision
    operator_note: Optional[str] = None

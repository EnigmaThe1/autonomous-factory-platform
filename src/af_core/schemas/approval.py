"""Approval API schemas."""

from datetime import datetime

from pydantic import BaseModel

from af_core.models.enums import ApprovalStatus


class ApprovalCreate(BaseModel):
    mission_id: str
    work_item_id: str | None = None
    reason: str
    context: str | None = None


class ApprovalDecision(BaseModel):
    status: ApprovalStatus
    decided_by: str


class ApprovalResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    mission_id: str
    work_item_id: str | None = None
    reason: str
    context: str | None = None
    status: ApprovalStatus
    decided_by: str | None = None
    decided_at: datetime | None = None
    created_at: datetime

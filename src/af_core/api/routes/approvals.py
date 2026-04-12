"""Approval endpoints."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from af_core.database import get_db
from af_core.models.approval import ApprovalRequest
from af_core.models.enums import ApprovalStatus
from af_core.schemas.approval import ApprovalDecision, ApprovalResponse
from af_core.services.event_bus import event_bus

router = APIRouter(prefix="/api/approvals", tags=["approvals"])


@router.get("", response_model=list[ApprovalResponse])
async def list_pending_approvals(
    db: AsyncSession = Depends(get_db),
) -> list[ApprovalRequest]:
    query = (
        select(ApprovalRequest)
        .where(ApprovalRequest.status == ApprovalStatus.PENDING)
        .order_by(ApprovalRequest.created_at)
    )
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("/{approval_id}/decide", response_model=ApprovalResponse)
async def decide_approval(
    approval_id: str,
    body: ApprovalDecision,
    db: AsyncSession = Depends(get_db),
) -> ApprovalRequest:
    query = select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
    result = await db.execute(query)
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.status != ApprovalStatus.PENDING:
        raise HTTPException(status_code=409, detail="Approval already decided")
    if body.status not in (ApprovalStatus.APPROVED, ApprovalStatus.REJECTED):
        raise HTTPException(status_code=400, detail="Decision must be approved or rejected")

    approval.status = body.status
    approval.decided_by = body.decided_by
    approval.decided_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(approval)

    await event_bus.emit(
        "approval.decided",
        {
            "approval_id": approval.id,
            "mission_id": approval.mission_id,
            "status": approval.status.value,
            "decided_by": approval.decided_by,
        },
    )

    return approval

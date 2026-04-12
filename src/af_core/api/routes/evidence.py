"""Evidence contract and tool invocation endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from af_core.database import get_db
from af_core.models.evidence import EvidenceContract, ToolInvocation
from af_core.models.work_item import WorkItem

router = APIRouter(prefix="/api/missions/{mission_id}", tags=["evidence"])


class EvidenceContractResponse(BaseModel):
    id: str
    work_item_id: str | None
    required_evidence: list
    preferred_evidence: list
    optional_evidence: list
    collected_evidence: list
    sufficiency_met: bool
    evaluation_notes: str | None = None


class ToolInvocationResponse(BaseModel):
    id: str
    mission_id: str
    work_item_id: str | None
    tool_name: str
    tool_category: str
    necessity: str
    input_params: dict
    output_result: dict | None
    success: bool
    error_message: str | None
    duration_ms: int | None
    created_at: str | None = None


@router.get("/evidence", response_model=list[EvidenceContractResponse])
async def list_evidence_contracts(mission_id: str, db: AsyncSession = Depends(get_db)):
    """Get evidence contracts for all work items in a mission."""
    # Get work item IDs for this mission
    wi_result = await db.execute(select(WorkItem.id).where(WorkItem.mission_id == mission_id))
    wi_ids = [r[0] for r in wi_result.all()]
    if not wi_ids:
        return []

    result = await db.execute(
        select(EvidenceContract).where(EvidenceContract.work_item_id.in_(wi_ids))
    )
    return [
        EvidenceContractResponse(
            id=e.id,
            work_item_id=e.work_item_id,
            required_evidence=e.required_evidence,
            preferred_evidence=e.preferred_evidence,
            optional_evidence=e.optional_evidence,
            collected_evidence=e.collected_evidence,
            sufficiency_met=e.sufficiency_met,
            evaluation_notes=e.evaluation_notes,
        )
        for e in result.scalars().all()
    ]


@router.get("/tool-invocations", response_model=list[ToolInvocationResponse])
async def list_tool_invocations(
    mission_id: str,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """Get tool invocations for a mission."""
    result = await db.execute(
        select(ToolInvocation)
        .where(ToolInvocation.mission_id == mission_id)
        .order_by(ToolInvocation.created_at.desc())
        .limit(limit)
    )
    return [
        ToolInvocationResponse(
            id=t.id,
            mission_id=t.mission_id,
            work_item_id=t.work_item_id,
            tool_name=t.tool_name,
            tool_category=t.tool_category,
            necessity=t.necessity.value,
            input_params=t.input_params,
            output_result=t.output_result,
            success=t.success,
            error_message=t.error_message,
            duration_ms=t.duration_ms,
            created_at=t.created_at.isoformat() if t.created_at else None,
        )
        for t in result.scalars().all()
    ]

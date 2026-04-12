"""Orchestration endpoints — mission lifecycle control."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from af_core.database import get_db
from af_core.models.mission import Mission
from af_core.models.work_item import WorkItem
from af_core.schemas.mission import MissionResponse
from af_core.schemas.work_item import WorkItemResponse
from af_core.services.orchestrator import Orchestrator

router = APIRouter(prefix="/api/missions/{mission_id}", tags=["orchestration"])
orchestrator = Orchestrator()


async def _load_mission(mission_id: str, db: AsyncSession) -> Mission:
    query = (
        select(Mission)
        .options(selectinload(Mission.contract), selectinload(Mission.findings))
        .where(Mission.id == mission_id)
    )
    result = await db.execute(query)
    mission = result.scalar_one_or_none()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return mission


@router.post("/start", response_model=MissionResponse)
async def start_mission(mission_id: str, db: AsyncSession = Depends(get_db)) -> Mission:
    """Start a compiled mission — seeds work items and transitions to queued."""
    mission = await _load_mission(mission_id, db)
    try:
        mission = await orchestrator.start_mission(mission, db)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    # Link dependencies after work items have IDs
    await orchestrator.link_work_item_dependencies(mission_id, db)
    await db.commit()

    # Reload
    mission = await _load_mission(mission_id, db)
    return mission


@router.post("/advance", response_model=MissionResponse)
async def advance_mission(mission_id: str, db: AsyncSession = Depends(get_db)) -> Mission:
    """Advance the mission — evaluate state and move to next phase."""
    mission = await _load_mission(mission_id, db)
    mission = await orchestrator.advance_mission(mission, db)
    await db.commit()
    mission = await _load_mission(mission_id, db)
    return mission


@router.post("/work-items/next", response_model=WorkItemResponse | None)
async def get_next_work_item(
    mission_id: str, db: AsyncSession = Depends(get_db)
) -> WorkItem | None:
    """Get the next ready work item for dispatch."""
    item = await orchestrator.get_next_work_item(mission_id, db)
    if not item:
        raise HTTPException(status_code=404, detail="No ready work items")
    return item


@router.post("/work-items/{work_item_id}/start", response_model=WorkItemResponse)
async def start_work_item(
    mission_id: str, work_item_id: str, db: AsyncSession = Depends(get_db)
) -> WorkItem:
    """Start a work item — mark as running."""
    query = select(WorkItem).where(WorkItem.id == work_item_id, WorkItem.mission_id == mission_id)
    result = await db.execute(query)
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Work item not found")

    try:
        item = await orchestrator.start_work_item(item, db)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    await db.commit()
    return item


@router.post("/work-items/{work_item_id}/complete", response_model=WorkItemResponse)
async def complete_work_item(
    mission_id: str,
    work_item_id: str,
    output: dict = {},
    db: AsyncSession = Depends(get_db),
) -> WorkItem:
    """Complete a work item with output."""
    query = select(WorkItem).where(WorkItem.id == work_item_id, WorkItem.mission_id == mission_id)
    result = await db.execute(query)
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Work item not found")

    item = await orchestrator.complete_work_item(item, output, db)
    await db.commit()
    return item


@router.post("/work-items/{work_item_id}/fail", response_model=WorkItemResponse)
async def fail_work_item(
    mission_id: str,
    work_item_id: str,
    reason: str = "Unknown failure",
    db: AsyncSession = Depends(get_db),
) -> WorkItem:
    """Fail a work item — retries if budget remains, otherwise marks failed."""
    query = select(WorkItem).where(WorkItem.id == work_item_id, WorkItem.mission_id == mission_id)
    result = await db.execute(query)
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Work item not found")

    item = await orchestrator.fail_work_item(item, reason, db)
    await db.commit()
    return item

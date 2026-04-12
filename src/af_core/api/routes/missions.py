"""Mission CRUD and lifecycle endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from af_core.database import get_db
from af_core.models.enums import MissionStatus
from af_core.models.mission import Mission
from af_core.schemas.mission import (
    MissionCreate,
    MissionListResponse,
    MissionResponse,
)
from af_core.services.event_bus import event_bus
from af_core.services.mission_service import create_and_compile_mission

router = APIRouter(prefix="/api/missions", tags=["missions"])


@router.post("", response_model=MissionResponse, status_code=201)
async def create_mission(
    body: MissionCreate,
    compile: bool = True,
    db: AsyncSession = Depends(get_db),
) -> Mission:
    """Create a new mission. Automatically compiles unless compile=false.

    The mission is always persisted immediately (ADR-007), then compiled
    into an authoritative contract (ADR-005) before execution can begin.
    """
    if compile:
        mission, _ = await create_and_compile_mission(body, db)
        return mission

    # Raw create without compilation (for testing or deferred compilation)
    mission = Mission(
        title=body.title,
        raw_prompt=body.raw_prompt,
        status=MissionStatus.PENDING,
        workspace_id=body.workspace_id,
        actor_id=body.actor_id,
        adapter_source=body.adapter_source,
        provider_hints=body.provider_hints,
        step_budget=body.step_budget,
        timeout_seconds=body.timeout_seconds,
    )
    db.add(mission)
    await db.commit()
    await db.refresh(mission, ["contract", "findings"])

    await event_bus.emit(
        "mission.created",
        {
            "mission_id": mission.id,
            "title": mission.title,
            "status": mission.status.value,
        },
    )

    return mission


@router.post("/{mission_id}/compile", response_model=MissionResponse)
async def compile_mission(mission_id: str, db: AsyncSession = Depends(get_db)) -> Mission:
    """Explicitly compile (or recompile) a mission."""
    from af_core.config import settings
    from af_core.services.mission_compiler import MissionCompiler

    query = (
        select(Mission)
        .options(selectinload(Mission.contract), selectinload(Mission.findings))
        .where(Mission.id == mission_id)
    )
    result = await db.execute(query)
    mission = result.scalar_one_or_none()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    if mission.status not in (MissionStatus.PENDING, MissionStatus.BLOCKED):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot compile mission in {mission.status.value} state",
        )

    compiler = MissionCompiler()
    await compiler.compile(mission, db, workspace_root=settings.workspace_root)
    await db.commit()

    # Expire and reload with relationships
    db.expire_all()
    reload_query = (
        select(Mission)
        .options(selectinload(Mission.contract), selectinload(Mission.findings))
        .where(Mission.id == mission_id)
    )
    result = await db.execute(reload_query)
    return result.scalar_one()


@router.get("", response_model=MissionListResponse)
async def list_missions(
    status: MissionStatus | None = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List missions with optional status filter."""
    query = select(Mission).options(selectinload(Mission.contract), selectinload(Mission.findings))
    count_query = select(func.count(Mission.id))

    if status:
        query = query.where(Mission.status == status)
        count_query = count_query.where(Mission.status == status)

    query = query.order_by(Mission.created_at.desc()).limit(limit).offset(offset)

    result = await db.execute(query)
    missions = result.scalars().all()

    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    return {"missions": missions, "total": total}


@router.get("/{mission_id}", response_model=MissionResponse)
async def get_mission(mission_id: str, db: AsyncSession = Depends(get_db)) -> Mission:
    """Get a single mission with contract and findings."""
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


@router.post("/{mission_id}/cancel", response_model=MissionResponse)
async def cancel_mission(mission_id: str, db: AsyncSession = Depends(get_db)) -> Mission:
    """Cancel a mission if it is not already completed."""
    query = (
        select(Mission)
        .options(selectinload(Mission.contract), selectinload(Mission.findings))
        .where(Mission.id == mission_id)
    )
    result = await db.execute(query)
    mission = result.scalar_one_or_none()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    if mission.status in (MissionStatus.COMPLETED, MissionStatus.CANCELLED):
        raise HTTPException(status_code=409, detail=f"Mission already {mission.status.value}")

    mission.status = MissionStatus.CANCELLED
    await db.commit()
    await db.refresh(mission)

    await event_bus.emit(
        "mission.cancelled",
        {
            "mission_id": mission.id,
            "status": mission.status.value,
        },
    )

    return mission

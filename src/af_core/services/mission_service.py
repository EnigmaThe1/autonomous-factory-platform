"""Mission service — orchestrates mission intake and compilation."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from af_core.config import settings
from af_core.models.enums import MissionStatus
from af_core.models.mission import Mission
from af_core.schemas.mission import MissionCreate
from af_core.services.event_bus import event_bus
from af_core.services.mission_compiler import CompilationResult, MissionCompiler

logger = logging.getLogger(__name__)

compiler = MissionCompiler()


async def create_and_compile_mission(
    body: MissionCreate, db: AsyncSession
) -> tuple[Mission, CompilationResult]:
    """Create a mission, persist it immediately, then compile it.

    Returns the mission and compilation result. The mission is always persisted
    even if compilation fails (ADR-007: visible stateful outcome).
    """
    # Step 1: Persist mission immediately
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
    await db.flush()

    await event_bus.emit(
        "mission.created",
        {
            "mission_id": mission.id,
            "title": mission.title,
            "status": mission.status.value,
        },
    )

    # Step 2: Compile
    result = await compiler.compile(mission, db, workspace_root=settings.workspace_root)

    await db.commit()

    # Reload with relationships
    query = (
        select(Mission)
        .options(selectinload(Mission.contract), selectinload(Mission.findings))
        .where(Mission.id == mission.id)
    )
    row = await db.execute(query)
    mission = row.scalar_one()

    return mission, result

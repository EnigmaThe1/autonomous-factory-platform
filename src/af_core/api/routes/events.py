"""Mission event endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from af_core.database import get_db
from af_core.models.event import MissionEvent
from af_core.schemas.event import MissionEventResponse

router = APIRouter(prefix="/api/missions/{mission_id}/events", tags=["events"])


@router.get("", response_model=list[MissionEventResponse])
async def list_events(
    mission_id: str,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> list[MissionEvent]:
    query = (
        select(MissionEvent)
        .where(MissionEvent.mission_id == mission_id)
        .order_by(MissionEvent.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    return list(result.scalars().all())

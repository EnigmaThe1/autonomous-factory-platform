"""Log export endpoint for observability."""

import json
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from af_core.database import get_db
from af_core.models.event import MissionEvent
from af_core.models.mission import Mission

router = APIRouter(prefix="/api", tags=["logs"])


@router.get("/logs/events")
async def export_events(
    mission_id: str | None = None,
    severity: str | None = None,
    component: str | None = None,
    limit: int = 500,
    db: AsyncSession = Depends(get_db),
):
    """Export events as JSON lines (JSONL) for external analysis."""
    query = select(MissionEvent).order_by(MissionEvent.created_at.desc()).limit(limit)
    if mission_id:
        query = query.where(MissionEvent.mission_id == mission_id)
    if severity:
        query = query.where(MissionEvent.severity == severity)
    if component:
        query = query.where(MissionEvent.component == component)

    result = await db.execute(query)
    events = result.scalars().all()

    lines = []
    for e in events:
        lines.append(
            json.dumps(
                {
                    "id": e.id,
                    "mission_id": e.mission_id,
                    "work_item_id": e.work_item_id,
                    "correlation_id": e.correlation_id,
                    "component": e.component,
                    "event_type": e.event_type,
                    "severity": e.severity.value if e.severity else None,
                    "payload": e.payload,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                }
            )
        )

    content = "\n".join(lines) + "\n" if lines else ""
    return StreamingResponse(
        iter([content]),
        media_type="application/x-ndjson",
        headers={
            "Content-Disposition": (
                f"attachment; filename=events-"
                f"{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}.jsonl"
            )
        },
    )


@router.get("/logs/missions")
async def export_missions_summary(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """Export mission summary as JSON for external analysis."""
    result = await db.execute(select(Mission).order_by(Mission.created_at.desc()).limit(limit))
    missions = result.scalars().all()
    return [
        {
            "id": m.id,
            "title": m.title,
            "status": m.status.value,
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "updated_at": m.updated_at.isoformat() if m.updated_at else None,
            "completed_at": m.completed_at.isoformat() if m.completed_at else None,
            "final_verdict": m.final_verdict,
        }
        for m in missions
    ]

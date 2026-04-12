"""Health and diagnostics endpoints."""

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from af_core import __version__
from af_core.database import get_db
from af_core.models.approval import ApprovalRequest
from af_core.models.enums import ApprovalStatus, MissionStatus, WorkItemStatus
from af_core.models.event import MissionEvent
from af_core.models.mission import Mission
from af_core.models.work_item import WorkItem

router = APIRouter(tags=["health"])

# Minimal SVG favicon
_FAVICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
    '<rect width="32" height="32" rx="6" fill="#1f6feb"/>'
    '<text x="16" y="23" text-anchor="middle" font-size="20" '
    'font-family="sans-serif" fill="#fff">AF</text>'
    "</svg>"
)


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)) -> dict:
    """Health check with database connectivity test."""
    db_ok = True
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    return {
        "status": "ok" if db_ok else "degraded",
        "version": __version__,
        "service": "autonomous-factory",
        "database": "connected" if db_ok else "disconnected",
    }


@router.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(content=_FAVICON_SVG, media_type="image/svg+xml")


@router.get("/api/diagnostics")
async def diagnostics(db: AsyncSession = Depends(get_db)) -> dict:
    """System-wide diagnostics: counts by status, recent activity."""
    # Mission counts by status
    mission_counts = {}
    for status in MissionStatus:
        result = await db.execute(select(func.count()).where(Mission.status == status))
        c = result.scalar() or 0
        if c > 0:
            mission_counts[status.value] = c

    total_missions = sum(mission_counts.values())

    # Work item counts by status
    wi_counts = {}
    for status in WorkItemStatus:
        result = await db.execute(select(func.count()).where(WorkItem.status == status))
        c = result.scalar() or 0
        if c > 0:
            wi_counts[status.value] = c

    # Pending approvals
    result = await db.execute(
        select(func.count()).where(ApprovalRequest.status == ApprovalStatus.PENDING)
    )
    pending_approvals = result.scalar() or 0

    # Total events
    result = await db.execute(select(func.count()).select_from(MissionEvent))
    total_events = result.scalar() or 0

    # Recent events (last 20)
    result = await db.execute(
        select(MissionEvent).order_by(MissionEvent.created_at.desc()).limit(20)
    )
    recent_events = [
        {
            "id": e.id,
            "mission_id": e.mission_id,
            "component": e.component,
            "event_type": e.event_type,
            "severity": e.severity.value if e.severity else "info",
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in result.scalars().all()
    ]

    return {
        "status": "ok",
        "version": __version__,
        "missions": {"total": total_missions, "by_status": mission_counts},
        "work_items": {"by_status": wi_counts},
        "pending_approvals": pending_approvals,
        "total_events": total_events,
        "recent_events": recent_events,
    }

"""Artifact and report endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from af_core.database import get_db
from af_core.models.report import Artifact, MissionReport

router = APIRouter(prefix="/api/missions/{mission_id}", tags=["artifacts"])


class ArtifactResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: str
    mission_id: str
    work_item_id: str | None = None
    artifact_type: str
    name: str
    path: str | None = None
    extra: dict | None = None
    created_at: str | None = None


class ReportResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: str
    mission_id: str
    report_type: str
    title: str
    content: str
    extra: dict | None = None
    created_at: str | None = None


@router.get("/artifacts", response_model=list[ArtifactResponse])
async def list_artifacts(mission_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Artifact)
        .where(Artifact.mission_id == mission_id)
        .order_by(Artifact.created_at.desc())
    )
    return [
        ArtifactResponse(
            id=a.id,
            mission_id=a.mission_id,
            work_item_id=a.work_item_id,
            artifact_type=a.artifact_type,
            name=a.name,
            path=a.path,
            extra=a.extra,
            created_at=a.created_at.isoformat() if a.created_at else None,
        )
        for a in result.scalars().all()
    ]


@router.get("/reports", response_model=list[ReportResponse])
async def list_reports(mission_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MissionReport)
        .where(MissionReport.mission_id == mission_id)
        .order_by(MissionReport.created_at.desc())
    )
    return [
        ReportResponse(
            id=r.id,
            mission_id=r.mission_id,
            report_type=r.report_type,
            title=r.title,
            content=r.content,
            extra=r.extra,
            created_at=r.created_at.isoformat() if r.created_at else None,
        )
        for r in result.scalars().all()
    ]

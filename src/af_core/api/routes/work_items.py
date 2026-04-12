"""Work-item endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from af_core.database import get_db
from af_core.models.work_item import WorkItem
from af_core.schemas.work_item import WorkItemResponse

router = APIRouter(prefix="/api/missions/{mission_id}/work-items", tags=["work-items"])


@router.get("", response_model=list[WorkItemResponse])
async def list_work_items(mission_id: str, db: AsyncSession = Depends(get_db)) -> list[WorkItem]:
    query = select(WorkItem).where(WorkItem.mission_id == mission_id).order_by(WorkItem.created_at)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/{work_item_id}", response_model=WorkItemResponse)
async def get_work_item(
    mission_id: str, work_item_id: str, db: AsyncSession = Depends(get_db)
) -> WorkItem:
    query = select(WorkItem).where(WorkItem.id == work_item_id, WorkItem.mission_id == mission_id)
    result = await db.execute(query)
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Work item not found")
    return item

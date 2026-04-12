"""Event API schemas."""

from datetime import datetime

from pydantic import BaseModel

from af_core.models.enums import EventSeverity


class MissionEventResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    mission_id: str
    work_item_id: str | None = None
    correlation_id: str | None = None
    component: str
    event_type: str
    severity: EventSeverity
    payload: dict | None = None
    created_at: datetime

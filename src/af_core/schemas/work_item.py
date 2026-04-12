"""Work-item API schemas."""

from datetime import datetime

from pydantic import BaseModel

from af_core.models.enums import AgentRole, WorkItemStatus


class WorkItemResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    mission_id: str
    role: AgentRole
    title: str
    status: WorkItemStatus
    step_contract: dict
    expected_deliverables: list
    dependencies: list
    retry_count: int
    output: dict | None = None
    created_at: datetime
    updated_at: datetime

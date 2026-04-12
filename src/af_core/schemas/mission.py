"""Mission API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from af_core.models.enums import FindingSeverity, MissionStatus


class MissionCreate(BaseModel):
    title: str = Field(..., max_length=500)
    raw_prompt: str
    workspace_id: str | None = None
    actor_id: str | None = None
    adapter_source: str | None = None
    provider_hints: dict | None = None
    step_budget: int | None = None
    timeout_seconds: int | None = None


class CompilerFindingResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    severity: FindingSeverity
    category: str
    message: str
    details: dict | None = None
    created_at: datetime


class MissionContractResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    contract_version: int
    normalized_objective: str
    normalized_scope: dict
    normalized_inputs: dict
    normalized_outputs: dict
    path_corrections: list
    success_criteria: list
    policy_binding: dict
    unresolved_ambiguities: list
    created_at: datetime


class MissionResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    title: str
    raw_prompt: str
    status: MissionStatus
    workspace_id: str | None = None
    actor_id: str | None = None
    adapter_source: str | None = None
    final_verdict: str | None = None
    step_budget: int | None = None
    timeout_seconds: int | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    contract: MissionContractResponse | None = None
    findings: list[CompilerFindingResponse] = []


class MissionListResponse(BaseModel):
    missions: list[MissionResponse]
    total: int

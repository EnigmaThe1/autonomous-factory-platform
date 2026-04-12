"""Mission and MissionContract ORM models."""

from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from af_core.models.base import Base, IdMixin, TimestampMixin
from af_core.models.enums import FindingSeverity, MissionStatus


class Mission(Base, IdMixin, TimestampMixin):
    """Top-level mission entity — persisted immediately on intake (ADR-007)."""

    __tablename__ = "missions"

    title: Mapped[str] = mapped_column(String(500))
    raw_prompt: Mapped[str] = mapped_column(Text)
    status: Mapped[MissionStatus] = mapped_column(
        Enum(MissionStatus), default=MissionStatus.PENDING
    )
    workspace_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    actor_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    adapter_source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    provider_hints: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Budget / governance
    step_budget: Mapped[int | None] = mapped_column(nullable=True)
    timeout_seconds: Mapped[int | None] = mapped_column(nullable=True)

    # Outcome
    final_verdict: Mapped[str | None] = mapped_column(String(50), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    contract: Mapped["MissionContract | None"] = relationship(
        back_populates="mission", uselist=False, cascade="all, delete-orphan"
    )
    findings: Mapped[list["CompilerFinding"]] = relationship(
        back_populates="mission", cascade="all, delete-orphan"
    )
    work_items: Mapped[list] = relationship(
        "WorkItem", back_populates="mission", cascade="all, delete-orphan"
    )
    events: Mapped[list] = relationship(
        "MissionEvent", back_populates="mission", cascade="all, delete-orphan"
    )
    approvals: Mapped[list] = relationship(
        "ApprovalRequest", back_populates="mission", cascade="all, delete-orphan"
    )
    reports: Mapped[list] = relationship(
        "MissionReport", back_populates="mission", cascade="all, delete-orphan"
    )


class MissionContract(Base, IdMixin, TimestampMixin):
    """Compiled mission contract — authoritative execution plan (ADR-005)."""

    __tablename__ = "mission_contracts"

    mission_id: Mapped[str] = mapped_column(String(32), ForeignKey("missions.id"), unique=True)
    contract_version: Mapped[int] = mapped_column(default=1)
    normalized_objective: Mapped[str] = mapped_column(Text)
    normalized_scope: Mapped[dict] = mapped_column(JSON, default=dict)
    normalized_inputs: Mapped[dict] = mapped_column(JSON, default=dict)
    normalized_outputs: Mapped[dict] = mapped_column(JSON, default=dict)
    path_corrections: Mapped[list] = mapped_column(JSON, default=list)
    success_criteria: Mapped[list] = mapped_column(JSON, default=list)
    policy_binding: Mapped[dict] = mapped_column(JSON, default=dict)
    unresolved_ambiguities: Mapped[list] = mapped_column(JSON, default=list)

    mission: Mapped["Mission"] = relationship(back_populates="contract")


class CompilerFinding(Base, IdMixin, TimestampMixin):
    """Individual finding from the mission compiler."""

    __tablename__ = "compiler_findings"

    mission_id: Mapped[str] = mapped_column(String(32), ForeignKey("missions.id"))
    severity: Mapped[FindingSeverity] = mapped_column(Enum(FindingSeverity))
    category: Mapped[str] = mapped_column(String(100))
    message: Mapped[str] = mapped_column(Text)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    mission: Mapped["Mission"] = relationship(back_populates="findings")

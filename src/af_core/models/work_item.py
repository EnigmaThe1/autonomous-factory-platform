"""Work-item ORM model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import JSON, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from af_core.models.base import Base, IdMixin, TimestampMixin
from af_core.models.enums import AgentRole, WorkItemStatus

if TYPE_CHECKING:
    from af_core.models.evidence import EvidenceContract
    from af_core.models.mission import Mission


class WorkItem(Base, IdMixin, TimestampMixin):
    """A unit of agent work within a mission."""

    __tablename__ = "work_items"

    mission_id: Mapped[str] = mapped_column(String(32), ForeignKey("missions.id"))
    role: Mapped[AgentRole] = mapped_column(Enum(AgentRole))
    title: Mapped[str] = mapped_column(String(500))
    status: Mapped[WorkItemStatus] = mapped_column(
        Enum(WorkItemStatus), default=WorkItemStatus.PENDING
    )
    step_contract: Mapped[dict] = mapped_column(JSON, default=dict)
    expected_deliverables: Mapped[list] = mapped_column(JSON, default=list)
    dependencies: Mapped[list] = mapped_column(JSON, default=list)
    retry_count: Mapped[int] = mapped_column(default=0)
    max_retries: Mapped[int] = mapped_column(default=3)
    output: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    mission: Mapped[Mission] = relationship(back_populates="work_items")
    evidence_contract: Mapped[EvidenceContract | None] = relationship(
        back_populates="work_item", uselist=False
    )

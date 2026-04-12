"""Evidence contract ORM model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import JSON, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from af_core.models.base import Base, IdMixin, TimestampMixin
from af_core.models.enums import ToolNecessity

if TYPE_CHECKING:
    from af_core.models.work_item import WorkItem


class EvidenceContract(Base, IdMixin, TimestampMixin):
    """Defines required/preferred/optional evidence for a work item."""

    __tablename__ = "evidence_contracts"

    work_item_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("work_items.id"), nullable=True, unique=True
    )
    required_evidence: Mapped[list] = mapped_column(JSON, default=list)
    preferred_evidence: Mapped[list] = mapped_column(JSON, default=list)
    optional_evidence: Mapped[list] = mapped_column(JSON, default=list)
    collected_evidence: Mapped[list] = mapped_column(JSON, default=list)
    sufficiency_met: Mapped[bool] = mapped_column(default=False)
    evaluation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    work_item: Mapped[WorkItem | None] = relationship(back_populates="evidence_contract")


class ToolInvocation(Base, IdMixin, TimestampMixin):
    """Record of a single tool invocation with necessity and result."""

    __tablename__ = "tool_invocations"

    mission_id: Mapped[str] = mapped_column(String(32), ForeignKey("missions.id"))
    work_item_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("work_items.id"), nullable=True
    )
    tool_name: Mapped[str] = mapped_column(String(200))
    tool_category: Mapped[str] = mapped_column(String(50))
    necessity: Mapped[ToolNecessity] = mapped_column(Enum(ToolNecessity))
    input_params: Mapped[dict] = mapped_column(JSON, default=dict)
    output_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    success: Mapped[bool] = mapped_column(default=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(nullable=True)

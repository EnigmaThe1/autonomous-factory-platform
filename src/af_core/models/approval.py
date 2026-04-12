"""Approval request model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from af_core.models.base import Base, IdMixin, TimestampMixin
from af_core.models.enums import ApprovalStatus

if TYPE_CHECKING:
    from af_core.models.mission import Mission


class ApprovalRequest(Base, IdMixin, TimestampMixin):
    """Operator approval request for guarded actions."""

    __tablename__ = "approval_requests"

    mission_id: Mapped[str] = mapped_column(String(32), ForeignKey("missions.id"))
    work_item_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    reason: Mapped[str] = mapped_column(Text)
    context: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus), default=ApprovalStatus.PENDING
    )
    decided_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    mission: Mapped[Mission] = relationship(back_populates="approvals")

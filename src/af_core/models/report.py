"""Mission report and artifact models."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from af_core.models.base import Base, IdMixin, TimestampMixin

if TYPE_CHECKING:
    from af_core.models.mission import Mission


class MissionReport(Base, IdMixin, TimestampMixin):
    """Final or intermediate report for a mission."""

    __tablename__ = "mission_reports"

    mission_id: Mapped[str] = mapped_column(String(32), ForeignKey("missions.id"))
    report_type: Mapped[str] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text)
    extra: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    mission: Mapped[Mission] = relationship(back_populates="reports")


class Artifact(Base, IdMixin, TimestampMixin):
    """Generated artifact (file, diff, output) stored by the platform."""

    __tablename__ = "artifacts"

    mission_id: Mapped[str] = mapped_column(String(32), ForeignKey("missions.id"))
    work_item_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    artifact_type: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(500))
    path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra: Mapped[dict | None] = mapped_column(JSON, nullable=True)

"""Mission event model — structured trace events for observability."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import JSON, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from af_core.models.base import Base, IdMixin, TimestampMixin
from af_core.models.enums import EventSeverity

if TYPE_CHECKING:
    from af_core.models.mission import Mission


class MissionEvent(Base, IdMixin, TimestampMixin):
    """Structured trace event per the observability module spec."""

    __tablename__ = "mission_events"

    mission_id: Mapped[str] = mapped_column(String(32), ForeignKey("missions.id"))
    work_item_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    component: Mapped[str] = mapped_column(String(100))
    event_type: Mapped[str] = mapped_column(String(100))
    severity: Mapped[EventSeverity] = mapped_column(Enum(EventSeverity), default=EventSeverity.INFO)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    mission: Mapped[Mission] = relationship(back_populates="events")

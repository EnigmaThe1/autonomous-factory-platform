"""SQLAlchemy base and shared column helpers."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _new_id() -> str:
    return uuid.uuid4().hex


class Base(DeclarativeBase):
    """Declarative base for all AF models."""

    pass


class IdMixin:
    """Provides a UUID primary key."""

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)


class TimestampMixin:
    """Provides created_at / updated_at columns."""

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

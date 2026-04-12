"""Platform settings model — provider config, API keys, connectors."""

from sqlalchemy import JSON, Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from af_core.models.base import Base, IdMixin, TimestampMixin


class PlatformSetting(Base, IdMixin, TimestampMixin):
    """Key-value setting with category, optional secret masking."""

    __tablename__ = "platform_settings"

    category: Mapped[str] = mapped_column(String(100), index=True)
    key: Mapped[str] = mapped_column(String(200), unique=True)
    value: Mapped[str] = mapped_column(Text, default="")
    is_secret: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str] = mapped_column(String(500), default="")
    extra: Mapped[dict | None] = mapped_column(JSON, nullable=True)

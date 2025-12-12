from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .organization import Organization


class CloudProvider(PyEnum):
    AWS = "AWS"
    AZURE = "AZURE"
    GCP = "GCP"


class CloudAccount(Base):
    __tablename__ = "cloud_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="cloud_accounts"
    )

    name: Mapped[str] = mapped_column(String, nullable=False)
    provider: Mapped[CloudProvider] = mapped_column(
        SQLEnum(CloudProvider, name="cloud_provider"), nullable=False
    )
    credentials: Mapped[dict] = mapped_column(JSONB, nullable=False)
    region: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

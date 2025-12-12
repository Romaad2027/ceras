from __future__ import annotations

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .organization import Organization
    from .cloud_account import CloudAccount


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    event_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    actor_identity: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    action_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    target_resource: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    actor_ip_address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    event_status: Mapped[str] = mapped_column(String, nullable=False)
    organization_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="audit_events"
    )
    cloud_account_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cloud_accounts.id"), nullable=True, index=True
    )
    cloud_account: Mapped[Optional["CloudAccount"]] = relationship("CloudAccount")

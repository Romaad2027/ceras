from __future__ import annotations

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .organization import Organization
    from .cloud_identity import CloudIdentity
    from .cloud_account import CloudAccount


class SecurityAlert(Base):
    __tablename__ = "security_alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[str] = mapped_column(String(255), index=True)
    rule_code: Mapped[str] = mapped_column(String(128), index=True)
    severity: Mapped[str] = mapped_column(String(30))
    description: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    organization_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="security_alerts"
    )

                                                                   
    cloud_identity_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cloud_identities.id"),
        nullable=True,
        index=True,
    )
    cloud_identity: Mapped[Optional["CloudIdentity"]] = relationship(
        "CloudIdentity", back_populates="security_alerts"
    )
    cloud_account_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cloud_accounts.id"),
        nullable=True,
        index=True,
    )
    cloud_account: Mapped[Optional["CloudAccount"]] = relationship("CloudAccount")

    def __repr__(self) -> str:
        return (
            f"SecurityAlert(id={self.id!r}, event_id={self.event_id!r}, "
            f"rule_code={self.rule_code!r}, severity={self.severity!r})"
        )

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import List, TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .organization import Organization
    from .entity_profile import EntityProfile
    from .security_alert import SecurityAlert
    from .cloud_account import CloudAccount


class IdentityType(PyEnum):
    IAM_USER = "IAM_USER"
    IAM_ROLE = "IAM_ROLE"
    ROOT = "ROOT"


class CloudIdentity(Base):
    __tablename__ = "cloud_identities"

                                                                          
                                                                                
    __table_args__ = (
        Index(
            "uq_cloud_identity_org_arn",
            "organization_id",
            "identity_arn",
            unique=True,
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="identities"
    )
    cloud_account_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cloud_accounts.id"), nullable=True, index=True
    )
    cloud_account: Mapped[Optional["CloudAccount"]] = relationship("CloudAccount")

    identity_arn: Mapped[str] = mapped_column(String, nullable=False)
    identity_name: Mapped[str] = mapped_column(String, nullable=False)
    identity_type: Mapped[IdentityType] = mapped_column(
        SQLEnum(IdentityType, name="cloud_identity_type"), nullable=False
    )
    is_mfa_enabled: Mapped[bool] = mapped_column(default=False, nullable=False)

                                                               
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

                                  
    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

              
    entity_profiles: Mapped[List["EntityProfile"]] = relationship(
        "EntityProfile", back_populates="cloud_identity"
    )
    security_alerts: Mapped[List["SecurityAlert"]] = relationship(
        "SecurityAlert", back_populates="cloud_identity"
    )

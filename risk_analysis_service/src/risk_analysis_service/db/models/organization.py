from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import List
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .cloud_account import CloudAccount
    from .audit_event import AuditEvent
    from .security_alert import SecurityAlert
    from .entity_profile import EntityProfile
    from .cloud_resource import CloudResource
    from .user_invitation import UserInvitation
    from .cloud_identity import CloudIdentity
    from .risk import Risk


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

                   
    users: Mapped[List["User"]] = relationship("User", back_populates="organization")
    invitations: Mapped[List["UserInvitation"]] = relationship(
        "UserInvitation", back_populates="organization"
    )
    cloud_accounts: Mapped[List["CloudAccount"]] = relationship(
        "CloudAccount", back_populates="organization"
    )
    audit_events: Mapped[List["AuditEvent"]] = relationship(
        "AuditEvent", back_populates="organization"
    )
    security_alerts: Mapped[List["SecurityAlert"]] = relationship(
        "SecurityAlert", back_populates="organization"
    )
    entity_profiles: Mapped[List["EntityProfile"]] = relationship(
        "EntityProfile", back_populates="organization"
    )
    cloud_resources: Mapped[List["CloudResource"]] = relationship(
        "CloudResource", back_populates="organization"
    )
    identities: Mapped[List["CloudIdentity"]] = relationship(
        "CloudIdentity", back_populates="organization"
    )
    risks: Mapped[List["Risk"]] = relationship("Risk", back_populates="organization")


class UserRole(PyEnum):
    ADMIN = "ADMIN"
    VIEWER = "VIEWER"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, name="user_role"), nullable=False, default=UserRole.ADMIN
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="users"
    )

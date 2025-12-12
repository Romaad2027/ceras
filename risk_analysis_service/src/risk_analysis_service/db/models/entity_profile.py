from __future__ import annotations

from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, String, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .organization import Organization
    from .cloud_identity import CloudIdentity


class ProfileMode(PyEnum):
    AUTO = "AUTO"
    MANUAL = "MANUAL"
    HYBRID = "HYBRID"


class EntityProfile(Base):
    __tablename__ = "entity_profiles"

                                 
    entity_id: Mapped[str] = mapped_column(String, primary_key=True)
    organization_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="entity_profiles"
    )

                                                                   
    cloud_identity_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cloud_identities.id"),
        nullable=True,
        index=True,
    )
    cloud_identity: Mapped[Optional["CloudIdentity"]] = relationship(
        "CloudIdentity", back_populates="entity_profiles"
    )

                                     
    whitelisted_cidrs: Mapped[list[str]] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb"), nullable=False
    )
    manual_allowed_actions: Mapped[list[str]] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb"), nullable=False
    )
    manual_forbidden_actions: Mapped[list[str]] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb"), nullable=False
    )

                                                              
    auto_common_hours: Mapped[Optional[List[int]]] = mapped_column(JSONB, nullable=True)
    auto_common_ips: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    auto_common_actions: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, nullable=True
    )

                  
    profile_mode: Mapped[ProfileMode] = mapped_column(
        SQLEnum(ProfileMode, name="profile_mode"),
        server_default=text("'HYBRID'"),
        nullable=False,
    )

                 
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

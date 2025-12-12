from __future__ import annotations

from enum import Enum as PyEnum
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Enum as SQLEnum, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .organization import Organization
    from .cloud_account import CloudAccount
    from .risk import Risk


class CloudResourceCriticality(PyEnum):
    LOW = "LOW"
    STANDARD = "STANDARD"
    CRITICAL = "CRITICAL"


class CloudResource(Base):
    __tablename__ = "cloud_resources"

                                                       
    resource_id: Mapped[str] = mapped_column(String, primary_key=True)
    organization_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="cloud_resources"
    )
    cloud_account_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cloud_accounts.id"), nullable=True, index=True
    )
    cloud_account: Mapped[Optional["CloudAccount"]] = relationship("CloudAccount")

                                            
    resource_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)

                                                
    resource_type: Mapped[str] = mapped_column(String, nullable=False)

                                
    criticality: Mapped[CloudResourceCriticality] = mapped_column(
        SQLEnum(CloudResourceCriticality, name="cloud_resource_criticality"),
        server_default=text("'STANDARD'"),
        nullable=False,
    )

                                          
    custom_rules: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )
    risks: Mapped[list["Risk"]] = relationship("Risk", back_populates="resource")

from __future__ import annotations

from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .organization import Organization
    from .cloud_resource import CloudResource


class Risk(Base):
    __tablename__ = "risks"

    id: Mapped[int] = mapped_column(primary_key=True)
    resource_name: Mapped[str] = mapped_column(String(30))
    description: Mapped[Optional[str]]

    severity: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30), default="new", server_default="new")

                  
    organization_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True, index=True
    )
    organization: Mapped[Optional["Organization"]] = relationship(
        "Organization", back_populates="risks"
    )

    resource_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("cloud_resources.resource_id"), nullable=True, index=True
    )
    resource: Mapped[Optional["CloudResource"]] = relationship(
        "CloudResource", back_populates="risks"
    )

    def __repr__(self) -> str:
        return (
            f"Risk(id={self.id!r}, resource_name={self.resource_name!r}, description={self.description!r}, "
            f"severity={self.severity!r}, status={self.status!r})"
        )

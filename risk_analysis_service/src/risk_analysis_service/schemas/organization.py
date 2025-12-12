from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from typing import Optional
import uuid
from datetime import datetime


class OrganizationUpdate(BaseModel):
    """Deprecated: No fields to update; credentials moved to CloudAccount."""

    model_config = ConfigDict(from_attributes=True)


class MemberResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class InvitationResponse(BaseModel):
    id: uuid.UUID
    email: str
    status: str
    expires_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrganizationBrief(BaseModel):
    """Minimal organization information safe to expose to clients."""

    id: uuid.UUID
    name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserWithOrganizationResponse(BaseModel):
    """User information including nested organization details."""

    id: uuid.UUID
    email: str
    role: str
    is_active: bool
    organization: OrganizationBrief

    model_config = ConfigDict(from_attributes=True)

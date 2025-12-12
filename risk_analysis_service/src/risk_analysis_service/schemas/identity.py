from __future__ import annotations

import ipaddress
import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator

from ..db.models.cloud_identity import IdentityType
from .entity_profile import EntityProfileResponse


class IdentityResponse(BaseModel):
    """Lightweight identity representation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    identity_arn: str
    identity_name: str
    identity_type: IdentityType
    is_mfa_enabled: bool
    created_at: Optional[datetime] = None


class ProfileUpdate(BaseModel):
    """Patch payload for updating an identity's profile."""

    whitelisted_cidrs: Optional[List[str]] = None
    manual_allowed_actions: Optional[List[str]] = None
    manual_forbidden_actions: Optional[List[str]] = None

    @field_validator("whitelisted_cidrs")
    @classmethod
    def validate_cidrs(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if value is None:
            return value
        for cidr in value:
            try:
                ipaddress.ip_network(cidr, strict=False)
            except Exception as exc:
                raise ValueError(f"Invalid CIDR: {cidr}") from exc
        return value


class IdentityDetailResponse(BaseModel):
    """Identity with its associated behavioral profile."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    identity_arn: str
    identity_name: str
    identity_type: IdentityType
    is_mfa_enabled: bool
    created_at: Optional[datetime] = None
    profile: EntityProfileResponse

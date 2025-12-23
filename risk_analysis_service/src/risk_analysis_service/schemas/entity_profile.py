from __future__ import annotations

import ipaddress
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, field_validator

from ..db.models.entity_profile import ProfileMode


class EntityProfileUpdate(BaseModel):
    """Fields that can be updated on an EntityProfile."""

    whitelisted_cidrs: Optional[List[str]] = None
    manual_allowed_actions: Optional[List[str]] = None
    manual_forbidden_actions: Optional[List[str]] = None
    profile_mode: Optional[ProfileMode] = None

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


class EntityProfileResponse(BaseModel):
    """Response schema for EntityProfile."""

    model_config = ConfigDict(from_attributes=True)

    entity_id: str
    whitelisted_cidrs: List[str]
    manual_allowed_actions: List[str]
    manual_forbidden_actions: List[str]
    auto_common_hours: Optional[List[int]] = None
    auto_common_ips: Optional[List[str]] = None
    auto_common_actions: Optional[List[str]] = None
    profile_mode: ProfileMode

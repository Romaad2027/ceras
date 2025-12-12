from __future__ import annotations

from typing import Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, computed_field

from ..db.models.cloud_resource import CloudResourceCriticality


class ResourceUpsertRequest(BaseModel):
    """Request schema to create or update a CloudResource."""

    resource_id: str
    resource_type: str
    resource_name: Optional[str] = None
    criticality: CloudResourceCriticality
    custom_rules: Optional[Dict[str, Any]] = None


class ResourceUpdate(BaseModel):
    """Partial update payload for a CloudResource."""

    criticality: CloudResourceCriticality


class ResourceResponse(BaseModel):
    """Base response schema for a CloudResource."""

    model_config = ConfigDict(from_attributes=True)

    resource_id: str
    resource_type: str
    resource_name: Optional[str] = None
    cloud_account_id: Optional[UUID] = None
    criticality: CloudResourceCriticality
    custom_rules: Dict[str, Any]


class ResourceDetailResponse(ResourceResponse):
    """Detailed response for a CloudResource including security configuration.

    Notes:
        For MVP, `security_config` is backed by the `custom_rules` JSONB column.
    """

    model_config = ConfigDict(from_attributes=True)

    @computed_field                      
    def security_config(self) -> Dict[str, Any]:
        """Expose security configuration derived from `custom_rules`."""
                                                                                          
        return getattr(self, "custom_rules", {}) or {}


class ResourceConfigUpdate(BaseModel):
    """Partial update schema for resource configuration.

    Attributes:
        criticality: Optional string value for criticality (e.g., 'LOW', 'STANDARD', 'CRITICAL').
        security_config: Optional dict with security settings, e.g.,
            {"blocked_actions": ["DeleteBucket"], "audit_log_enabled": true}.
    """

    criticality: Optional[str] = None
    security_config: Optional[Dict[str, Any]] = None

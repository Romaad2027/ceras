from datetime import datetime
from enum import Enum
from typing import Any, Dict
from uuid import UUID

from pydantic import BaseModel, field_validator

from .cloud_resource import CloudProvider


class EventStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class GenericAuditEvent(BaseModel):
    event_id: str
    event_time: datetime
    actor_identity: str
    actor_ip_address: str
    action_name: str
    target_resource: str
    event_status: EventStatus
    organization_id: UUID
    cloud_provider: CloudProvider
    raw_log: Dict[str, Any]

    @field_validator("cloud_provider", mode="before")
    def _normalize_cloud_provider(cls, value: Any) -> Any:
        if isinstance(value, str):
            try:
                return CloudProvider(value.upper())
            except ValueError:
                return value
        return value

    @field_validator("event_status", mode="before")
    def _normalize_event_status(cls, value: Any) -> Any:
        if isinstance(value, str):
            try:
                return EventStatus(value.upper())
            except ValueError:
                return value
        return value

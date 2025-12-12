from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict


class CloudProvider(str, Enum):
    AWS = "AWS"
    AZURE = "AZURE"
    GCP = "GCP"


class CloudAccountCreate(BaseModel):
    """Payload to create a cloud account attached to an organization."""

    name: str
    provider: CloudProvider
    credentials: dict[str, Any]
    region: str


class CloudAccountSummary(BaseModel):
    """Cloud account representation without sensitive credentials."""

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    provider: CloudProvider
    region: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CloudAccountRead(BaseModel):
    """Cloud account representation."""

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    provider: CloudProvider
    credentials: dict[str, Any]
    region: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

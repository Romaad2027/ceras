from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


class SecurityAlertOut(BaseModel):
    id: int
    event_id: str
    rule_code: str
    severity: str
    description: str
    created_at: datetime
    organization_id: uuid.UUID
    cloud_identity_id: Optional[uuid.UUID] = None
    cloud_account_id: Optional[uuid.UUID] = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedSecurityAlerts(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[SecurityAlertOut]

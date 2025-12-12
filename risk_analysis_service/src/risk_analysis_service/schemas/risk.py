from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from uuid import UUID


class RiskBase(BaseModel):
    resource_name: str
    description: str
    severity: str
    status: str = "new"
    organization_id: UUID
    resource_id: str


class RiskCreate(RiskBase):
    pass


class Risk(RiskBase):
    id: int
    found_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

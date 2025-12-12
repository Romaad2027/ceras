from __future__ import annotations

import uuid
from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional


class Token(BaseModel):
    access_token: str
    token_type: str


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    organization_name: Optional[str] = None


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    role: str
    organization_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class TenantRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    organization_name: str


class InviteRequest(BaseModel):
    email: EmailStr
                                                                 
                                                       
                                    


class InviteAcceptRequest(BaseModel):
    token: str
    password: str
    full_name: Optional[str] = None

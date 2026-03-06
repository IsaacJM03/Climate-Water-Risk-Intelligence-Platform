from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class UserCreate(BaseModel):
    email: str
    password: str
    role: str = "viewer"
    organization_id: int
    expo_push_token: Optional[str] = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ("admin", "analyst", "viewer"):
            raise ValueError("role must be admin, analyst, or viewer")
        return v


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: int
    org_id: int
    role: str


class OrganizationCreate(BaseModel):
    name: str
    type: str

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in ("church", "NGO", "government"):
            raise ValueError("type must be church, NGO, or government")
        return v


class OrganizationResponse(BaseModel):
    id: int
    name: str
    type: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

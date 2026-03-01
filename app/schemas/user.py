"""User schemas."""
import re
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    phone: str = Field(..., pattern=r"^\+233[0-9]{9}$")

    @field_validator("phone")
    @classmethod
    def validate_ghana_phone(cls, v: str) -> str:
        if not re.match(r"^\+233[0-9]{9}$", v):
            raise ValueError("Phone must be in format +233XXXXXXXXX")
        return v


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = Field(None, pattern=r"^\+233[0-9]{9}$")


class UserResponse(BaseModel):
    id: UUID
    email: str
    phone: str
    full_name: str
    role: str
    email_verified: bool
    phone_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_user(cls, user) -> "UserResponse":
        return cls(
            id=user.id,
            email=user.email,
            phone=user.phone,
            full_name=user.full_name,
            role=user.role.value if hasattr(user.role, "value") else user.role,
            email_verified=user.email_verified,
            phone_verified=user.phone_verified,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

"""Auth request/response schemas."""
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    phone: str = Field(..., pattern=r"^\+233[0-9]{9}$")
    password: str = Field(..., min_length=8, max_length=100)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class GoogleAuthRequest(BaseModel):
    id_token: str = Field(..., min_length=1)


class AppleAuthRequest(BaseModel):
    id_token: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    """Login response - frontend expects 'user' and 'token'."""
    user: "UserResponse"
    token: str
    token_type: str = "bearer"


# Resolve forward ref
from app.schemas.user import UserResponse  # noqa: E402
LoginResponse.model_rebuild()

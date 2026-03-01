"""Authentication endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.exceptions import DuplicateResourceError
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.db.session import get_db
from app.schemas.auth import (
    AppleAuthRequest,
    GoogleAuthRequest,
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Register a new user and return user + token (same as login for convenience)."""
    auth_service = AuthService(db)
    try:
        user = await auth_service.register_user(user_data)
    except DuplicateResourceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    token = create_access_token({"sub": str(user.id)})
    return LoginResponse(
        user=UserResponse.from_user(user),
        token=token,
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    credentials: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Login and return user + access token (frontend expects 'token' field)."""
    auth_service = AuthService(db)
    user = await auth_service.authenticate_user(credentials.email, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    token = create_access_token({"sub": str(user.id)})
    return LoginResponse(
        user=UserResponse.from_user(user),
        token=token,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Refresh access token."""
    payload = decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    user_id = payload.get("sub")
    token = create_access_token({"sub": user_id})
    return TokenResponse(access_token=token)


@router.post("/logout")
async def logout():
    """Logout (client should discard tokens)."""
    return {"message": "Successfully logged out"}


@router.post("/google", response_model=LoginResponse)
async def login_google(
    body: GoogleAuthRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Sign in or sign up with Google account."""
    auth_service = AuthService(db)
    user = await auth_service.authenticate_google(body.id_token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token or Google sign-in not configured",
        )
    token = create_access_token({"sub": str(user.id)})
    return LoginResponse(
        user=UserResponse.from_user(user),
        token=token,
    )


@router.post("/apple", response_model=LoginResponse)
async def login_apple(
    body: AppleAuthRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Sign in or sign up with Apple account."""
    auth_service = AuthService(db)
    user = await auth_service.authenticate_apple(body.id_token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Apple token or Apple sign-in not configured",
        )
    token = create_access_token({"sub": str(user.id)})
    return LoginResponse(
        user=UserResponse.from_user(user),
        token=token,
    )

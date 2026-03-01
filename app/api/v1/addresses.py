"""Delivery addresses endpoints."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.address_repo import AddressRepository
from app.schemas.address import AddressCreate, AddressResponse

router = APIRouter(prefix="/addresses", tags=["Addresses"])


@router.get("", response_model=list[AddressResponse])
async def list_addresses(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List current user's delivery addresses."""
    repo = AddressRepository(db)
    addresses = await repo.get_by_user_id(current_user.id)
    return addresses


@router.post("", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
async def create_address(
    data: AddressCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Add a delivery address."""
    repo = AddressRepository(db)
    address = await repo.create({
        "user_id": current_user.id,
        "label": data.label,
        "recipient_name": data.recipient_name,
        "phone": data.phone,
        "address_line1": data.address_line1,
        "address_line2": data.address_line2,
        "city": data.city,
        "region": data.region,
        "is_default": data.is_default,
    })
    return address


@router.get("/{address_id}", response_model=AddressResponse)
async def get_address(
    address_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get one address by ID."""
    repo = AddressRepository(db)
    address = await repo.get_by_id_and_user(address_id, current_user.id)
    if not address:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found")
    return address

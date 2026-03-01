"""Address schemas."""
from uuid import UUID

from pydantic import BaseModel, Field


class AddressBase(BaseModel):
    label: str = Field(..., max_length=50)
    recipient_name: str = Field(..., max_length=255)
    phone: str = Field(..., pattern=r"^\+233[0-9]{9}$")
    address_line1: str = Field(..., max_length=500)
    address_line2: str | None = Field(None, max_length=500)
    city: str = Field(..., max_length=100)
    region: str = Field(..., max_length=100)
    is_default: bool = False


class AddressCreate(AddressBase):
    pass


class AddressResponse(AddressBase):
    id: UUID
    user_id: UUID
    is_default: bool

    model_config = {"from_attributes": True}

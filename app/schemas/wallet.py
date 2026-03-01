"""Wallet schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class WalletResponse(BaseModel):
    id: UUID
    user_id: UUID
    balance: Decimal
    currency: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FundWalletRequest(BaseModel):
    amount: Decimal = Field(..., gt=0)
    payment_method: str = Field(
        ...,
        pattern="^(mobile_money|card|bank_transfer)$",
    )
    phone_number: Optional[str] = Field(None, pattern=r"^\+233[0-9]{9}$")


class TransactionResponse(BaseModel):
    id: UUID
    wallet_id: UUID
    type: str
    amount: Decimal
    status: str
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    description: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    data: list[TransactionResponse]
    total: int
    page: int
    limit: int

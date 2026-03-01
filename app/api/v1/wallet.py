"""Wallet endpoints."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.wallet import (
    FundWalletRequest,
    TransactionListResponse,
    TransactionResponse,
    WalletResponse,
)
from app.services.wallet_service import WalletService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/wallet", tags=["Wallet"])


@router.get("", response_model=WalletResponse)
async def get_wallet(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get current user's wallet."""
    wallet_service = WalletService(db)
    wallet = await wallet_service.get_wallet(current_user.id)
    return wallet


@router.get("/transactions", response_model=TransactionListResponse)
async def get_transactions(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """List wallet transactions."""
    wallet_service = WalletService(db)
    txs = await wallet_service.get_transactions(
        current_user.id,
        skip=skip,
        limit=limit,
    )
    return TransactionListResponse(
        data=[
            TransactionResponse(
                id=t.id,
                wallet_id=t.wallet_id,
                type=t.type.value,
                amount=t.amount,
                status=t.status.value,
                payment_method=t.payment_method,
                payment_reference=t.payment_reference,
                description=t.description,
                created_at=t.created_at,
            )
            for t in txs
        ],
        total=len(txs),
        page=(skip // limit) + 1,
        limit=limit,
    )


@router.post("/fund")
async def fund_wallet(
    body: FundWalletRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Initiate wallet funding (e.g. Paystack). Returns payment URL or instructions."""
    # Placeholder: in production, create Paystack transaction and return authorization_url
    return {
        "message": "Payment integration: use Paystack to add funds",
        "amount": float(body.amount),
        "payment_method": body.payment_method,
    }

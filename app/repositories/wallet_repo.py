"""Wallet repository."""
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select

from app.models.wallet import Transaction, TransactionStatus, TransactionType, Wallet
from app.repositories.base import BaseRepository


class WalletRepository(BaseRepository[Wallet]):
    def __init__(self, db):
        super().__init__(Wallet, db)

    async def get_by_user_id(self, user_id: UUID) -> Wallet | None:
        result = await self.db.execute(
            select(Wallet).where(Wallet.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create_for_user(self, user_id: UUID) -> Wallet:
        wallet = await self.get_by_user_id(user_id)
        if wallet:
            return wallet
        wallet = await self.create({"user_id": user_id})
        return wallet

    async def credit(
        self,
        wallet_id: UUID,
        amount: Decimal,
        description: str,
        payment_reference: str | None = None,
    ) -> Transaction:
        wallet = await self.get_by_id(wallet_id)
        if not wallet:
            raise ValueError("Wallet not found")
        wallet.balance = (wallet.balance or 0) + amount
        self.db.add(wallet)
        tx_obj = Transaction(
            wallet_id=wallet_id,
            type=TransactionType.CREDIT,
            amount=amount,
            status=TransactionStatus.COMPLETED,
            description=description,
            payment_reference=payment_reference,
        )
        self.db.add(tx_obj)
        await self.db.flush()
        await self.db.refresh(tx_obj)
        return tx_obj

    async def debit(
        self,
        wallet_id: UUID,
        amount: Decimal,
        description: str,
    ) -> Transaction:
        wallet = await self.get_by_id(wallet_id)
        if not wallet:
            raise ValueError("Wallet not found")
        if (wallet.balance or 0) < amount:
            raise ValueError("Insufficient balance")
        wallet.balance = (wallet.balance or 0) - amount
        self.db.add(wallet)
        tx_obj = Transaction(
            wallet_id=wallet_id,
            type=TransactionType.DEBIT,
            amount=amount,
            status=TransactionStatus.COMPLETED,
            description=description,
        )
        self.db.add(tx_obj)
        await self.db.flush()
        await self.db.refresh(tx_obj)
        return tx_obj


class TransactionRepository(BaseRepository[Transaction]):
    def __init__(self, db):
        super().__init__(Transaction, db)

    async def get_by_wallet(
        self,
        wallet_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Transaction]:
        result = await self.db.execute(
            select(Transaction)
            .where(Transaction.wallet_id == wallet_id)
            .order_by(Transaction.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

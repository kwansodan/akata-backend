"""Wallet service."""
from decimal import Decimal
from uuid import UUID

from app.repositories.wallet_repo import TransactionRepository, WalletRepository


class WalletService:
    def __init__(self, db):
        self.db = db
        self.wallet_repo = WalletRepository(db)
        self.tx_repo = TransactionRepository(db)

    async def get_wallet(self, user_id: UUID):
        wallet = await self.wallet_repo.get_by_user_id(user_id)
        if not wallet:
            wallet = await self.wallet_repo.get_or_create_for_user(user_id)
        return wallet

    async def get_transactions(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ):
        wallet = await self.wallet_repo.get_by_user_id(user_id)
        if not wallet:
            return []
        return await self.tx_repo.get_by_wallet(wallet.id, skip=skip, limit=limit)

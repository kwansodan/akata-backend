"""Address repository."""
from uuid import UUID

from sqlalchemy import select

from app.models.address import Address
from app.repositories.base import BaseRepository


class AddressRepository(BaseRepository[Address]):
    def __init__(self, db):
        super().__init__(Address, db)

    async def get_by_user_id(self, user_id: UUID) -> list[Address]:
        result = await self.db.execute(
            select(Address).where(Address.user_id == user_id)
        )
        return list(result.scalars().all())

    async def get_by_id_and_user(self, address_id: UUID, user_id: UUID) -> Address | None:
        result = await self.db.execute(
            select(Address).where(
                Address.id == address_id,
                Address.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

"""Order repository."""
from uuid import UUID

from sqlalchemy import select

from app.models.order import Order, OrderStatus
from app.repositories.base import BaseRepository


class OrderRepository(BaseRepository[Order]):
    def __init__(self, db):
        super().__init__(Order, db)

    async def get_by_user(
        self,
        user_id: UUID,
        status: OrderStatus | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Order]:
        q = select(Order).where(Order.user_id == user_id)
        if status is not None:
            q = q.where(Order.status == status)
        q = q.order_by(Order.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def count_by_user(self, user_id: UUID, status: OrderStatus | None = None) -> int:
        from sqlalchemy import func

        q = select(func.count()).select_from(Order).where(Order.user_id == user_id)
        if status is not None:
            q = q.where(Order.status == status)
        result = await self.db.execute(q)
        return result.scalar() or 0

    async def get_by_status(
        self,
        status: OrderStatus,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Order]:
        result = await self.db.execute(
            select(Order)
            .where(Order.status == status)
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_shopper_orders(
        self,
        shopper_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Order]:
        result = await self.db.execute(
            select(Order)
            .where(Order.shopper_id == shopper_id)
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def assign_shopper(
        self,
        order_id: UUID,
        shopper_id: UUID,
    ) -> Order | None:
        order = await self.get_by_id(order_id)
        if order and order.status == OrderStatus.PENDING:
            return await self.update(
                order_id,
                {
                    "shopper_id": shopper_id,
                    "status": OrderStatus.ASSIGNED,
                },
            )
        return None

"""Order service."""
from decimal import Decimal
from uuid import UUID

from app.core.exceptions import InsufficientFundsError, OrderNotFoundError
from app.models.order import Order, OrderStatus
from app.repositories.address_repo import AddressRepository
from app.repositories.order_repo import OrderRepository
from app.repositories.wallet_repo import WalletRepository
from app.schemas.order import OrderCreate


class OrderService:
    COMMISSION_RATE = Decimal("20.0")

    def __init__(self, db):
        self.db = db
        self.order_repo = OrderRepository(db)
        self.wallet_repo = WalletRepository(db)
        self.address_repo = AddressRepository(db)

    def _address_to_delivery(self, address) -> dict:
        return {
            "recipient_name": address.recipient_name,
            "phone": address.phone,
            "address_line1": address.address_line1,
            "address_line2": address.address_line2,
            "city": address.city,
            "region": address.region,
        }

    async def create_order(self, user, order_data: OrderCreate) -> Order:
        commission_amount = (
            order_data.estimated_price_gbp * self.COMMISSION_RATE / 100
        )
        total_gbp = order_data.estimated_price_gbp + commission_amount
        # Simple conversion for GHS hold (use a fixed rate or fetch from API)
        total_amount = total_gbp * Decimal("14.62")

        wallet = await self.wallet_repo.get_by_user_id(user.id)
        if not wallet:
            wallet = await self.wallet_repo.get_or_create_for_user(user.id)
        if (wallet.balance or 0) < total_amount:
            raise InsufficientFundsError("Insufficient wallet balance")

        address = await self.address_repo.get_by_id_and_user(
            order_data.delivery_address_id,
            user.id,
        )
        if not address:
            raise ValueError("Delivery address not found")
        delivery_address = self._address_to_delivery(address)

        order_dict = order_data.model_dump(exclude={"delivery_address_id"})
        order_dict.update({
            "user_id": user.id,
            "commission_rate": self.COMMISSION_RATE,
            "commission_amount": commission_amount,
            "total_amount": total_amount,
            "delivery_address": delivery_address,
            "status": OrderStatus.PENDING,
        })
        order_dict["product_url"] = str(order_dict["product_url"])
        order = await self.order_repo.create(order_dict)

        await self.wallet_repo.debit(
            wallet.id,
            total_amount,
            f"Order #{order.id}",
        )
        return order

    async def get_user_orders(
        self,
        user_id: UUID,
        status: OrderStatus | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Order]:
        return await self.order_repo.get_by_user(
            user_id,
            status=status,
            skip=skip,
            limit=limit,
        )

    async def count_user_orders(
        self,
        user_id: UUID,
        status: OrderStatus | None = None,
    ) -> int:
        return await self.order_repo.count_by_user(user_id, status=status)

    async def get_order_by_id(self, order_id: UUID, user_id: UUID) -> Order:
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            raise OrderNotFoundError("Order not found")
        if order.user_id != user_id:
            raise OrderNotFoundError("Order not found")
        return order

    async def update_order_status(
        self,
        order_id: UUID,
        new_status: OrderStatus,
        shopper_id: UUID | None = None,
    ) -> Order | None:
        update_data = {"status": new_status}
        if shopper_id is not None:
            update_data["shopper_id"] = shopper_id
        return await self.order_repo.update(order_id, update_data)

    async def cancel_order(self, order_id: UUID, user_id: UUID) -> Order:
        order = await self.get_order_by_id(order_id, user_id)
        if order.status not in (OrderStatus.PENDING, OrderStatus.ASSIGNED):
            raise ValueError("Cannot cancel order in current status")
        await self.order_repo.update(order_id, {"status": OrderStatus.CANCELLED})
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            raise OrderNotFoundError("Order not found")
        wallet = await self.wallet_repo.get_by_user_id(user_id)
        if wallet:
            await self.wallet_repo.credit(
                wallet.id,
                order.total_amount,
                f"Refund for cancelled order #{order.id}",
            )
        return order

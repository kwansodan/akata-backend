"""Order schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class OrderBase(BaseModel):
    product_url: HttpUrl
    product_name: str = Field(..., min_length=1, max_length=500)
    variant_details: dict[str, str] = Field(default_factory=dict)
    quantity: int = Field(default=1, ge=1, le=10)
    estimated_price_gbp: Decimal = Field(..., gt=0)


class OrderCreate(OrderBase):
    delivery_address_id: UUID
    special_instructions: Optional[str] = Field(None, max_length=1000)


class OrderUpdate(BaseModel):
    status: Optional[str] = None
    tracking_number: Optional[str] = None
    actual_price_gbp: Optional[Decimal] = None
    shipping_cost: Optional[Decimal] = None


class OrderResponse(BaseModel):
    id: UUID
    user_id: UUID
    shopper_id: Optional[UUID] = None
    product_url: str
    product_name: str
    variant_details: dict[str, Any]
    quantity: int
    estimated_price_gbp: Decimal
    actual_price_gbp: Optional[Decimal] = None
    commission_rate: Decimal
    commission_amount: Decimal
    shipping_cost: Optional[Decimal] = None
    total_amount: Decimal
    status: str
    tracking_number: Optional[str] = None
    delivery_address: dict[str, Any]
    special_instructions: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_order(cls, order) -> "OrderResponse":
        return cls(
            id=order.id,
            user_id=order.user_id,
            shopper_id=order.shopper_id,
            product_url=str(order.product_url),
            product_name=order.product_name,
            variant_details=order.variant_details or {},
            quantity=order.quantity,
            estimated_price_gbp=order.estimated_price_gbp,
            actual_price_gbp=order.actual_price_gbp,
            commission_rate=order.commission_rate,
            commission_amount=order.commission_amount,
            shipping_cost=order.shipping_cost,
            total_amount=order.total_amount,
            status=order.status.value if hasattr(order.status, "value") else order.status,
            tracking_number=order.tracking_number,
            delivery_address=order.delivery_address or {},
            special_instructions=order.special_instructions,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )


class OrderListResponse(BaseModel):
    data: list[OrderResponse]
    total: int
    page: int
    limit: int

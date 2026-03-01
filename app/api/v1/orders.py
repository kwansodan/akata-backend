"""Order endpoints."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.exceptions import InsufficientFundsError, OrderNotFoundError
from app.db.session import get_db
from app.models.user import User
from app.models.order import OrderStatus as OrderStatusEnum
from app.schemas.order import OrderCreate, OrderListResponse, OrderResponse
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new purchase request."""
    order_service = OrderService(db)
    try:
        order = await order_service.create_order(current_user, order_data)
        return OrderResponse.from_order(order)
    except InsufficientFundsError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=OrderListResponse)
async def get_orders(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = Query(None, description="Filter by status"),
):
    """List current user's orders."""
    status_enum = None
    if status:
        try:
            status_enum = OrderStatusEnum(status)
        except ValueError:
            status_enum = None
    order_service = OrderService(db)
    orders = await order_service.get_user_orders(
        current_user.id,
        status=status_enum,
        skip=skip,
        limit=limit,
    )
    total = await order_service.count_user_orders(current_user.id, status=status_enum)
    return OrderListResponse(
        data=[OrderResponse.from_order(o) for o in orders],
        total=total,
        page=(skip // limit) + 1,
        limit=limit,
    )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get order by ID."""
    order_service = OrderService(db)
    try:
        order = await order_service.get_order_by_id(order_id, current_user.id)
        return OrderResponse.from_order(order)
    except OrderNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")


@router.patch("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Cancel an order (refunds wallet)."""
    order_service = OrderService(db)
    try:
        order = await order_service.cancel_order(order_id, current_user.id)
        return OrderResponse.from_order(order)
    except OrderNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

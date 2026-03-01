"""Common schemas."""
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list response."""
    data: list[T]
    total: int
    page: int
    limit: int

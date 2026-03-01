"""Custom exceptions for the application."""


class AppException(Exception):
    """Base application exception."""

    def __init__(self, message: str, code: str = "ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class InsufficientFundsError(AppException):
    """Raised when wallet balance is insufficient."""

    def __init__(self, message: str = "Insufficient wallet balance"):
        super().__init__(message, code="INSUFFICIENT_FUNDS")


class OrderNotFoundError(AppException):
    """Raised when order is not found or not accessible."""

    def __init__(self, message: str = "Order not found"):
        super().__init__(message, code="ORDER_NOT_FOUND")


class UserNotFoundError(AppException):
    """Raised when user is not found."""

    def __init__(self, message: str = "User not found"):
        super().__init__(message, code="USER_NOT_FOUND")


class DuplicateResourceError(AppException):
    """Raised when creating a resource that already exists (e.g. email)."""

    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message, code="DUPLICATE_RESOURCE")

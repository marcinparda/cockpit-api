"""Exception handling utilities for authentication endpoints."""

from functools import wraps
from typing import Callable, Any
from fastapi import HTTPException, status


def handle_auth_exceptions(service_name: str):
    """
    Decorator to handle common authentication service exceptions.
    
    Args:
        service_name: Name of the service for error messages
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                # Re-raise HTTP exceptions as-is
                raise
            except Exception:
                # Log unexpected errors and return generic message
                # TODO: Add proper logging here
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"{service_name} service temporarily unavailable"
                )
        return wrapper
    return decorator


# Common exception handlers for specific services
login_exception_handler = handle_auth_exceptions("Login")
password_change_exception_handler = handle_auth_exceptions("Password change")
token_refresh_exception_handler = handle_auth_exceptions("Token refresh")
logout_exception_handler = handle_auth_exceptions("Logout")
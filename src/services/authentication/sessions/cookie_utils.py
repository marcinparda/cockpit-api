"""Cookie configuration utilities for authentication."""

from fastapi import Response
from src.core.config import settings


def get_cookie_config() -> dict:
    """Get environment-specific cookie configuration."""
    is_production = settings.ENVIRONMENT == "production"
    
    return {
        "domain": settings.COOKIE_DOMAIN if is_production else None,
        "secure": settings.COOKIE_SECURE if is_production else False,
        "samesite": settings.COOKIE_SAMESITE,
        "httponly": settings.COOKIE_HTTPONLY
    }


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Set authentication cookies with proper configuration."""
    cookie_config = get_cookie_config()
    
    # Set access token cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=settings.ACCESS_TOKEN_COOKIE_MAX_AGE,
        **cookie_config
    )
    
    # Set refresh token cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=settings.REFRESH_TOKEN_COOKIE_MAX_AGE,
        **cookie_config
    )


def clear_auth_cookies(response: Response) -> None:
    """Clear authentication cookies."""
    cookie_config = get_cookie_config()
    
    # Clear access token cookie
    response.set_cookie(
        key="access_token",
        value="",
        max_age=0,
        **cookie_config
    )
    
    # Clear refresh token cookie
    response.set_cookie(
        key="refresh_token",
        value="",
        max_age=0,
        **cookie_config
    )
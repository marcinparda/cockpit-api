"""Token management endpoints for token refresh."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.services.authentication.tokens.schemas import SimpleRefreshResponse
from src.services.authentication.tokens.service import refresh_access_token
from src.services.authentication.sessions.cookie_utils import set_auth_cookies
from src.services.authentication.exception_utils import token_refresh_exception_handler


router = APIRouter()


@router.post("/refresh", response_model=SimpleRefreshResponse)
@token_refresh_exception_handler
async def refresh_tokens(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
) -> SimpleRefreshResponse:
    """Refresh access token using refresh token from cookie."""

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token required in cookie"
        )
    
    # Basic JWT format validation
    if not refresh_token or len(refresh_token.split('.')) != 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid refresh token format"
        )

    new_access_token, new_refresh_token = await refresh_access_token(refresh_token, db)

    set_auth_cookies(response, new_access_token, new_refresh_token)

    return SimpleRefreshResponse(detail="Tokens refreshed successfully")

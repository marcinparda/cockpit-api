from datetime import datetime
from typing import Optional
from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.authentication.tokens.models import AccessToken, RefreshToken


async def create_access_token_record(
    db: AsyncSession,
    jti: str,
    user_id: UUID,
    expires_at: datetime
) -> AccessToken:
    """Create a new access token record."""
    token = AccessToken()
    token.jti = jti
    token.user_id = user_id
    token.expires_at = expires_at
    token.is_revoked = False

    db.add(token)
    await db.commit()
    await db.refresh(token)
    return token


async def create_refresh_token_record(
    db: AsyncSession,
    jti: str,
    user_id: UUID,
    expires_at: datetime
) -> RefreshToken:
    """Create a new refresh token record."""
    token = RefreshToken()
    token.jti = jti
    token.user_id = user_id
    token.expires_at = expires_at
    token.is_revoked = False

    db.add(token)
    await db.commit()
    await db.refresh(token)
    return token


async def get_access_token_by_jti(db: AsyncSession, jti: str) -> Optional[AccessToken]:
    """Get access token by JTI."""
    result = await db.execute(
        select(AccessToken).where(AccessToken.jti == jti)
    )
    return result.scalar_one_or_none()


async def get_refresh_token_by_jti(db: AsyncSession, jti: str) -> Optional[RefreshToken]:
    """Get refresh token by JTI."""
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.jti == jti)
    )
    return result.scalar_one_or_none()


async def update_access_token_revoked_status(db: AsyncSession, jti: str, is_revoked: bool) -> bool:
    """Update access token revoked status."""
    result = await db.execute(
        update(AccessToken)
        .where(AccessToken.jti == jti)
        .values(is_revoked=is_revoked)
    )
    await db.commit()
    return result.rowcount > 0


async def update_refresh_token_revoked_status(db: AsyncSession, jti: str, is_revoked: bool) -> bool:
    """Update refresh token revoked status."""
    result = await db.execute(
        update(RefreshToken)
        .where(RefreshToken.jti == jti)
        .values(is_revoked=is_revoked)
    )
    await db.commit()
    return result.rowcount > 0


async def update_access_token_last_used(db: AsyncSession, jti: str, last_used_at: datetime) -> bool:
    """Update access token last used timestamp."""
    result = await db.execute(
        update(AccessToken)
        .where(AccessToken.jti == jti)
        .values(last_used_at=last_used_at)
    )
    await db.commit()
    return result.rowcount > 0



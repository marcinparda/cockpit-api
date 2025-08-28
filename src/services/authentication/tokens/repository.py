from datetime import datetime
from typing import Optional
from uuid import UUID
from sqlalchemy import and_, select, delete, func, update
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


async def delete_expired_access_tokens(db: AsyncSession, before_date: datetime) -> int:
    """Delete expired access tokens before given date."""
    result = await db.execute(
        delete(AccessToken).where(AccessToken.expires_at <= before_date)
    )
    await db.commit()
    return result.rowcount


async def delete_expired_refresh_tokens(db: AsyncSession, before_date: datetime) -> int:
    """Delete expired refresh tokens before given date."""
    result = await db.execute(
        delete(RefreshToken).where(RefreshToken.expires_at <= before_date)
    )
    await db.commit()
    return result.rowcount


async def delete_old_revoked_access_tokens(db: AsyncSession, before_date: datetime) -> int:
    """Delete old revoked access tokens updated before given date."""
    result = await db.execute(
        delete(AccessToken).where(
            and_(
                AccessToken.is_revoked == True,
                AccessToken.updated_at <= before_date
            )
        )
    )
    await db.commit()
    return result.rowcount


async def delete_old_revoked_refresh_tokens(db: AsyncSession, before_date: datetime) -> int:
    """Delete old revoked refresh tokens updated before given date."""
    result = await db.execute(
        delete(RefreshToken).where(
            and_(
                RefreshToken.is_revoked == True,
                RefreshToken.updated_at <= before_date
            )
        )
    )
    await db.commit()
    return result.rowcount


async def count_access_tokens_total(db: AsyncSession) -> int:
    """Count total access tokens."""
    result = await db.execute(select(func.count(AccessToken.id)))
    return result.scalar() or 0


async def count_access_tokens_active(db: AsyncSession, before_date: datetime) -> int:
    """Count active access tokens (not revoked and not expired before given date)."""
    result = await db.execute(
        select(func.count(AccessToken.id)).where(
            and_(
                AccessToken.is_revoked == False,
                AccessToken.expires_at > before_date
            )
        )
    )
    return result.scalar() or 0


async def count_access_tokens_revoked(db: AsyncSession) -> int:
    """Count revoked access tokens."""
    result = await db.execute(
        select(func.count(AccessToken.id)).where(
            AccessToken.is_revoked == True)
    )
    return result.scalar() or 0


async def count_access_tokens_expired(db: AsyncSession, before_date: datetime) -> int:
    """Count expired access tokens (not revoked but expired before given date)."""
    result = await db.execute(
        select(func.count(AccessToken.id)).where(
            and_(
                AccessToken.is_revoked == False,
                AccessToken.expires_at <= before_date
            )
        )
    )
    return result.scalar() or 0


async def count_refresh_tokens_total(db: AsyncSession) -> int:
    """Count total refresh tokens."""
    result = await db.execute(select(func.count(RefreshToken.id)))
    return result.scalar() or 0


async def count_refresh_tokens_active(db: AsyncSession, before_date: datetime) -> int:
    """Count active refresh tokens (not revoked and not expired before given date)."""
    result = await db.execute(
        select(func.count(RefreshToken.id)).where(
            and_(
                RefreshToken.is_revoked == False,
                RefreshToken.expires_at > before_date
            )
        )
    )
    return result.scalar() or 0


async def count_refresh_tokens_revoked(db: AsyncSession) -> int:
    """Count revoked refresh tokens."""
    result = await db.execute(
        select(func.count(RefreshToken.id)).where(
            RefreshToken.is_revoked == True)
    )
    return result.scalar() or 0


async def count_refresh_tokens_expired(db: AsyncSession, before_date: datetime) -> int:
    """Count expired refresh tokens (not revoked but expired before given date)."""
    result = await db.execute(
        select(func.count(RefreshToken.id)).where(
            and_(
                RefreshToken.is_revoked == False,
                RefreshToken.expires_at <= before_date
            )
        )
    )
    return result.scalar() or 0

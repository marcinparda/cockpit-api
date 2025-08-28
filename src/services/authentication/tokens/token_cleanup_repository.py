from datetime import datetime
from sqlalchemy import and_, select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.authentication.tokens.models import AccessToken, RefreshToken


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

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.authentication.token_repository import (
    create_access_token_record,
    create_refresh_token_record,
    get_access_token_by_jti,
    get_refresh_token_by_jti,
    update_access_token_revoked_status,
    update_refresh_token_revoked_status,
    update_access_token_last_used,
    delete_expired_access_tokens,
    delete_expired_refresh_tokens,
    delete_old_revoked_access_tokens,
    delete_old_revoked_refresh_tokens,
    count_access_tokens_total,
    count_access_tokens_active,
    count_access_tokens_revoked,
    count_access_tokens_expired,
    count_refresh_tokens_total,
    count_refresh_tokens_active,
    count_refresh_tokens_revoked,
    count_refresh_tokens_expired,
)
from src.core.config import settings


async def create_access_token(
    db: AsyncSession,
    jti: str,
    user_id: UUID,
    expires_at: datetime
):
    """Create a new access token record with timezone handling."""
    if expires_at.tzinfo is not None:
        expires_at = expires_at.replace(tzinfo=None)

    return await create_access_token_record(db, jti, user_id, expires_at)


async def create_refresh_token(
    db: AsyncSession,
    jti: str,
    user_id: UUID,
    expires_at: datetime
):
    """Create a new refresh token record with timezone handling."""
    if expires_at.tzinfo is not None:
        expires_at = expires_at.replace(tzinfo=None)

    return await create_refresh_token_record(db, jti, user_id, expires_at)


async def is_access_token_valid(db: AsyncSession, jti: str) -> bool:
    """Check if an access token is valid (exists, not revoked, not expired)."""
    token = await get_access_token_by_jti(db, jti)

    if not token:
        return False

    if token.is_revoked:
        return False

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if token.expires_at <= now:
        return False

    return True


async def is_refresh_token_valid(db: AsyncSession, jti: str) -> bool:
    """Check if a refresh token is valid (exists, not revoked, not expired)."""
    token = await get_refresh_token_by_jti(db, jti)

    if not token:
        return False

    if token.is_revoked:
        return False

    # Check if token is expired
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if token.expires_at <= now:
        return False

    return True


async def revoke_access_token(db: AsyncSession, jti: str) -> bool:
    """Revoke an access token by JTI."""
    return await update_access_token_revoked_status(db, jti, True)


async def revoke_refresh_token(db: AsyncSession, jti: str) -> bool:
    """Revoke a refresh token by JTI."""
    return await update_refresh_token_revoked_status(db, jti, True)


async def update_access_token_last_used_timestamp(db: AsyncSession, jti: str) -> bool:
    """Update the last_used_at timestamp for an access token."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    return await update_access_token_last_used(db, jti, now)


async def cleanup_expired_tokens(db: AsyncSession) -> dict:
    """Clean up expired tokens from the database."""
    now = datetime.now(timezone.utc)
    now_naive = now.replace(tzinfo=None)

    access_deleted = await delete_expired_access_tokens(db, now_naive)
    refresh_deleted = await delete_expired_refresh_tokens(db, now_naive)

    return {
        "expired_access_tokens_deleted": access_deleted,
        "expired_refresh_tokens_deleted": refresh_deleted,
        "cleanup_time": now
    }


async def cleanup_old_revoked_tokens(
    db: AsyncSession,
    retention_days: Optional[int] = None
) -> dict:
    """Clean up old revoked tokens that are past retention period."""
    if retention_days is None:
        retention_days = settings.TOKEN_CLEANUP_RETENTION_DAYS

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
    cutoff_date_naive = cutoff_date.replace(tzinfo=None)

    access_deleted = await delete_old_revoked_access_tokens(db, cutoff_date_naive)
    refresh_deleted = await delete_old_revoked_refresh_tokens(db, cutoff_date_naive)

    return {
        "old_revoked_access_tokens_deleted": access_deleted,
        "old_revoked_refresh_tokens_deleted": refresh_deleted,
        "retention_days": retention_days,
        "cutoff_date": cutoff_date,
        "cleanup_time": datetime.now(timezone.utc)
    }


async def get_token_statistics(db: AsyncSession) -> dict:
    """Get token usage statistics."""
    now = datetime.now(timezone.utc)
    now_naive = now.replace(tzinfo=None)

    access_total = await count_access_tokens_total(db)
    access_active = await count_access_tokens_active(db, now_naive)
    access_revoked = await count_access_tokens_revoked(db)
    access_expired = await count_access_tokens_expired(db, now_naive)

    refresh_total = await count_refresh_tokens_total(db)
    refresh_active = await count_refresh_tokens_active(db, now_naive)
    refresh_revoked = await count_refresh_tokens_revoked(db)
    refresh_expired = await count_refresh_tokens_expired(db, now_naive)

    return {
        "access_tokens": {
            "total": access_total,
            "active": access_active,
            "revoked": access_revoked,
            "expired": access_expired
        },
        "refresh_tokens": {
            "total": refresh_total,
            "active": refresh_active,
            "revoked": refresh_revoked,
            "expired": refresh_expired
        },
        "generated_at": now
    }

from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID
from sqlalchemy import and_, select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.auth.models import AccessToken
from src.app.auth.models import RefreshToken
from src.app.auth.models import User
from src.core.config import settings


class TokenService:
    """Service for managing access and refresh tokens in the database."""

    @staticmethod
    async def create_access_token(
        db: AsyncSession,
        jti: str,
        user_id: UUID,
        expires_at: datetime
    ) -> AccessToken:
        """Create a new access token record."""
        # Convert timezone-aware datetime to naive for database storage
        if expires_at.tzinfo is not None:
            expires_at = expires_at.replace(tzinfo=None)

        # Create token with attributes instead of constructor params
        token = AccessToken()
        token.jti = jti
        token.user_id = user_id
        token.expires_at = expires_at
        token.is_revoked = False

        db.add(token)
        await db.commit()
        await db.refresh(token)
        return token

    @staticmethod
    async def create_refresh_token(
        db: AsyncSession,
        jti: str,
        user_id: UUID,
        expires_at: datetime
    ) -> RefreshToken:
        """Create a new refresh token record."""
        # Convert timezone-aware datetime to naive for database storage
        if expires_at.tzinfo is not None:
            expires_at = expires_at.replace(tzinfo=None)

        # Create token with attributes instead of constructor params
        token = RefreshToken()
        token.jti = jti
        token.user_id = user_id
        token.expires_at = expires_at
        token.is_revoked = False

        db.add(token)
        await db.commit()
        await db.refresh(token)
        return token

    @staticmethod
    async def get_access_token(db: AsyncSession, jti: str) -> Optional[AccessToken]:
        """Get an access token by JTI."""
        result = await db.execute(
            select(AccessToken).where(AccessToken.jti == jti)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_refresh_token(db: AsyncSession, jti: str) -> Optional[RefreshToken]:
        """Get a refresh token by JTI."""
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.jti == jti)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def is_access_token_valid(db: AsyncSession, jti: str) -> bool:
        """Check if an access token is valid (exists, not revoked, not expired)."""
        now = datetime.now(timezone.utc)
        # Convert to naive datetime for database comparison (database stores naive datetimes)
        now_naive = now.replace(tzinfo=None)
        result = await db.execute(
            select(AccessToken).where(
                and_(
                    AccessToken.jti == jti,
                    AccessToken.is_revoked == False,
                    AccessToken.expires_at > now_naive
                )
            )
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def is_refresh_token_valid(db: AsyncSession, jti: str) -> bool:
        """Check if a refresh token is valid (exists, not revoked, not expired)."""
        now = datetime.now(timezone.utc)
        # Convert to naive datetime for database comparison (database stores naive datetimes)
        now_naive = now.replace(tzinfo=None)
        result = await db.execute(
            select(RefreshToken).where(
                and_(
                    RefreshToken.jti == jti,
                    RefreshToken.is_revoked == False,
                    RefreshToken.expires_at > now_naive
                )
            )
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def revoke_access_token(db: AsyncSession, jti: str) -> bool:
        """Revoke an access token by JTI."""
        result = await db.execute(
            select(AccessToken).where(AccessToken.jti == jti)
        )
        token = result.scalar_one_or_none()
        if token:
            token.is_revoked = True  # type: ignore
            await db.commit()
            return True
        return False

    @staticmethod
    async def revoke_refresh_token(db: AsyncSession, jti: str) -> bool:
        """Revoke a refresh token by JTI."""
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.jti == jti)
        )
        token = result.scalar_one_or_none()
        if token:
            token.is_revoked = True  # type: ignore
            await db.commit()
            return True
        return False

    @staticmethod
    async def update_access_token_last_used(db: AsyncSession, jti: str) -> bool:
        """Update the last_used_at timestamp for an access token."""
        result = await db.execute(
            select(AccessToken).where(AccessToken.jti == jti)
        )
        token = result.scalar_one_or_none()
        if token:
            # Convert timezone-aware datetime to naive for database storage
            now = datetime.now(timezone.utc)
            token.last_used_at = now.replace(tzinfo=None)  # type: ignore
            await db.commit()
            return True
        return False

    @staticmethod
    async def update_refresh_token_last_used(db: AsyncSession, jti: str) -> bool:
        """Update the last_used_at timestamp for a refresh token."""
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.jti == jti)
        )
        token = result.scalar_one_or_none()
        if token:
            # Convert timezone-aware datetime to naive for database storage
            now = datetime.now(timezone.utc)
            token.last_used_at = now.replace(tzinfo=None)  # type: ignore
            await db.commit()
            return True
        return False

    @staticmethod
    async def revoke_all_user_tokens(db: AsyncSession, user_id: UUID) -> int:
        """Revoke all tokens for a specific user."""
        access_result = await db.execute(
            select(AccessToken).where(
                and_(
                    AccessToken.user_id == user_id,
                    AccessToken.is_revoked == False
                )
            )
        )
        refresh_result = await db.execute(
            select(RefreshToken).where(
                and_(
                    RefreshToken.user_id == user_id,
                    RefreshToken.is_revoked == False
                )
            )
        )

        access_tokens = access_result.scalars().all()
        refresh_tokens = refresh_result.scalars().all()

        revoked_count = 0
        for access_token in access_tokens:
            access_token.is_revoked = True  # type: ignore
            revoked_count += 1

        for refresh_token in refresh_tokens:
            refresh_token.is_revoked = True  # type: ignore
            revoked_count += 1

        await db.commit()
        return revoked_count

    @staticmethod
    async def get_user_active_tokens(
        db: AsyncSession,
        user_id: UUID,
        limit: int = 50
    ) -> tuple[List[AccessToken], List[RefreshToken]]:
        """Get active tokens for a user."""
        now = datetime.now(timezone.utc)
        # Convert to naive datetime for database comparison (database stores naive datetimes)
        now_naive = now.replace(tzinfo=None)

        access_result = await db.execute(
            select(AccessToken)
            .where(
                and_(
                    AccessToken.user_id == user_id,
                    AccessToken.is_revoked == False,
                    AccessToken.expires_at > now_naive
                )
            )
            .order_by(AccessToken.created_at.desc())
            .limit(limit)
        )

        refresh_result = await db.execute(
            select(RefreshToken)
            .where(
                and_(
                    RefreshToken.user_id == user_id,
                    RefreshToken.is_revoked == False,
                    RefreshToken.expires_at > now_naive
                )
            )
            .order_by(RefreshToken.created_at.desc())
            .limit(limit)
        )

        return list(access_result.scalars().all()), list(refresh_result.scalars().all())

    @staticmethod
    async def cleanup_expired_tokens(db: AsyncSession) -> dict:
        """Clean up expired tokens from the database."""
        now = datetime.now(timezone.utc)
        # Convert to naive datetime for database comparison (database stores naive datetimes)
        now_naive = now.replace(tzinfo=None)

        # Delete expired access tokens
        access_delete_result = await db.execute(
            delete(AccessToken).where(AccessToken.expires_at <= now_naive)
        )

        # Delete expired refresh tokens
        refresh_delete_result = await db.execute(
            delete(RefreshToken).where(RefreshToken.expires_at <= now_naive)
        )

        await db.commit()

        return {
            "expired_access_tokens_deleted": access_delete_result.rowcount,
            "expired_refresh_tokens_deleted": refresh_delete_result.rowcount,
            "cleanup_time": now
        }

    @staticmethod
    async def cleanup_old_revoked_tokens(
        db: AsyncSession,
        retention_days: Optional[int] = None
    ) -> dict:
        """Clean up old revoked tokens that are past retention period."""
        if retention_days is None:
            retention_days = settings.TOKEN_CLEANUP_RETENTION_DAYS

        cutoff_date = datetime.now(timezone.utc) - \
            timedelta(days=retention_days)
        # Convert to naive datetime for database comparison (database stores naive datetimes)
        cutoff_date_naive = cutoff_date.replace(tzinfo=None)

        # Delete old revoked access tokens
        access_delete_result = await db.execute(
            delete(AccessToken).where(
                and_(
                    AccessToken.is_revoked == True,
                    AccessToken.updated_at <= cutoff_date_naive
                )
            )
        )

        # Delete old revoked refresh tokens
        refresh_delete_result = await db.execute(
            delete(RefreshToken).where(
                and_(
                    RefreshToken.is_revoked == True,
                    RefreshToken.updated_at <= cutoff_date_naive
                )
            )
        )

        await db.commit()

        return {
            "old_revoked_access_tokens_deleted": access_delete_result.rowcount,
            "old_revoked_refresh_tokens_deleted": refresh_delete_result.rowcount,
            "retention_days": retention_days,
            "cutoff_date": cutoff_date,
            "cleanup_time": datetime.now(timezone.utc)
        }

    @staticmethod
    async def get_token_statistics(db: AsyncSession) -> dict:
        """Get token usage statistics."""
        now = datetime.now(timezone.utc)
        # Convert to naive datetime for database comparison (database stores naive datetimes)
        now_naive = now.replace(tzinfo=None)

        # Access token stats
        access_total = await db.execute(select(func.count(AccessToken.id)))
        access_active = await db.execute(
            select(func.count(AccessToken.id)).where(
                and_(
                    AccessToken.is_revoked == False,
                    AccessToken.expires_at > now_naive
                )
            )
        )
        access_revoked = await db.execute(
            select(func.count(AccessToken.id)).where(
                AccessToken.is_revoked == True)
        )
        access_expired = await db.execute(
            select(func.count(AccessToken.id)).where(
                and_(
                    AccessToken.is_revoked == False,
                    AccessToken.expires_at <= now_naive
                )
            )
        )

        # Refresh token stats
        refresh_total = await db.execute(select(func.count(RefreshToken.id)))
        refresh_active = await db.execute(
            select(func.count(RefreshToken.id)).where(
                and_(
                    RefreshToken.is_revoked == False,
                    RefreshToken.expires_at > now_naive
                )
            )
        )
        refresh_revoked = await db.execute(
            select(func.count(RefreshToken.id)).where(
                RefreshToken.is_revoked == True)
        )
        refresh_expired = await db.execute(
            select(func.count(RefreshToken.id)).where(
                and_(
                    RefreshToken.is_revoked == False,
                    RefreshToken.expires_at <= now_naive
                )
            )
        )

        return {
            "access_tokens": {
                "total": access_total.scalar(),
                "active": access_active.scalar(),
                "revoked": access_revoked.scalar(),
                "expired": access_expired.scalar()
            },
            "refresh_tokens": {
                "total": refresh_total.scalar(),
                "active": refresh_active.scalar(),
                "revoked": refresh_revoked.scalar(),
                "expired": refresh_expired.scalar()
            },
            "generated_at": now
        }

from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import logging

from src.services.token_service import TokenService
from src.core.config import settings
from src.core.database import async_session_maker

logger = logging.getLogger(__name__)


class TokenCleanupService:
    """Service for periodic cleanup of expired and old revoked tokens."""

    @staticmethod
    async def cleanup_expired_tokens() -> dict:
        """Remove expired tokens from the database."""
        async with async_session_maker() as db:
            try:
                result = await TokenService.cleanup_expired_tokens(db)
                logger.info(f"Token cleanup completed: {result}")
                return result
            except Exception as e:
                logger.error(f"Token cleanup failed: {e}")
                raise

    @staticmethod
    async def cleanup_old_revoked_tokens(retention_days: Optional[int] = None) -> dict:
        """Remove old revoked tokens from the database."""
        if retention_days is None:
            retention_days = settings.TOKEN_CLEANUP_RETENTION_DAYS

        async with async_session_maker() as db:
            try:
                result = await TokenService.cleanup_old_revoked_tokens(db, retention_days)
                logger.info(f"Old revoked token cleanup completed: {result}")
                return result
            except Exception as e:
                logger.error(f"Old revoked token cleanup failed: {e}")
                raise

    @staticmethod
    async def full_token_cleanup() -> dict:
        """Perform full token cleanup: expired and old revoked tokens."""
        try:
            expired_result = await TokenCleanupService.cleanup_expired_tokens()
            revoked_result = await TokenCleanupService.cleanup_old_revoked_tokens()

            return {
                "expired_cleanup": expired_result,
                "revoked_cleanup": revoked_result,
                "total_cleaned": (
                    expired_result.get("expired_access_tokens_deleted", 0) +
                    expired_result.get("expired_refresh_tokens_deleted", 0) +
                    revoked_result.get("old_revoked_access_tokens_deleted", 0) +
                    revoked_result.get("old_revoked_refresh_tokens_deleted", 0)
                ),
                "cleanup_time": datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Full token cleanup failed: {e}")
            raise

    @staticmethod
    async def get_cleanup_statistics() -> dict:
        """Get token statistics for monitoring."""
        async with async_session_maker() as db:
            try:
                stats = await TokenService.get_token_statistics(db)
                logger.info(f"Token statistics retrieved: {stats}")
                return stats
            except Exception as e:
                logger.error(f"Failed to get token statistics: {e}")
                raise

    @staticmethod
    async def scheduled_cleanup():
        """Run scheduled cleanup based on configuration."""
        if not settings.ENABLE_TOKEN_TRACKING:
            logger.info("Token tracking is disabled, skipping cleanup")
            return

        logger.info("Starting scheduled token cleanup")
        try:
            result = await TokenCleanupService.full_token_cleanup()
            logger.info(f"Scheduled cleanup completed successfully: {result}")
        except Exception as e:
            logger.error(f"Scheduled cleanup failed: {e}")
            raise

    @staticmethod
    async def start_periodic_cleanup():
        """Start periodic token cleanup task."""
        if not settings.ENABLE_TOKEN_TRACKING:
            logger.info(
                "Token tracking is disabled, not starting cleanup task")
            return

        interval_hours = settings.TOKEN_CLEANUP_INTERVAL_HOURS
        logger.info(
            f"Starting periodic token cleanup every {interval_hours} hours")

        while True:
            try:
                await TokenCleanupService.scheduled_cleanup()

                # Wait for the next cleanup interval
                # Convert hours to seconds
                await asyncio.sleep(interval_hours * 3600)

            except asyncio.CancelledError:
                logger.info("Token cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"Token cleanup error: {e}")
                # Wait a shorter time before retrying on error
                await asyncio.sleep(300)  # 5 minutes


# Utility function to run cleanup as a standalone script
async def run_token_cleanup():
    """Run token cleanup as a standalone operation."""
    cleanup_service = TokenCleanupService()
    result = await cleanup_service.full_token_cleanup()
    print(f"Cleanup completed: {result}")
    return result


# For running as a script
if __name__ == "__main__":
    asyncio.run(run_token_cleanup())

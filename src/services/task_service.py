"""Task service for managing background operations."""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from src.services.token_service import TokenService
from src.core.database import async_session_maker

logger = logging.getLogger(__name__)


class TokenCleanupService:
    """Service for handling token cleanup operations."""

    @staticmethod
    async def comprehensive_token_cleanup(
        retention_days: Optional[int] = None,
        batch_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive token cleanup including expired and old revoked tokens.

        Args:
            retention_days: Days to retain revoked tokens
            batch_size: Number of tokens to process in each batch

        Returns:
            Dictionary containing cleanup statistics
        """
        cleanup_stats = {
            "start_time": datetime.now(timezone.utc),
            "success": False,
            "error": None,
            "expired_cleanup": {},
            "revoked_cleanup": {},
            "total_deleted": 0
        }

        try:
            logger.info("Starting comprehensive token cleanup")

            async with async_session_maker() as db:
                # Clean up expired tokens
                logger.info("Cleaning up expired tokens")
                expired_stats = await TokenService.cleanup_expired_tokens(db)
                cleanup_stats["expired_cleanup"] = expired_stats

                # Clean up old revoked tokens
                logger.info("Cleaning up old revoked tokens")
                revoked_stats = await TokenService.cleanup_old_revoked_tokens(
                    db, retention_days
                )
                cleanup_stats["revoked_cleanup"] = revoked_stats

                # Calculate totals
                total_deleted = (
                    expired_stats.get("expired_access_tokens_deleted", 0) +
                    expired_stats.get("expired_refresh_tokens_deleted", 0) +
                    revoked_stats.get("old_revoked_access_tokens_deleted", 0) +
                    revoked_stats.get("old_revoked_refresh_tokens_deleted", 0)
                )
                cleanup_stats["total_deleted"] = total_deleted
                cleanup_stats["success"] = True

                logger.info(
                    f"Token cleanup completed successfully. "
                    f"Total tokens deleted: {total_deleted}"
                )

        except Exception as e:
            logger.error(f"Token cleanup failed: {str(e)}", exc_info=True)
            cleanup_stats["error"] = str(e)
            cleanup_stats["success"] = False

        finally:
            cleanup_stats["end_time"] = datetime.now(timezone.utc)
            cleanup_stats["duration"] = (
                cleanup_stats["end_time"] - cleanup_stats["start_time"]
            ).total_seconds()

        return cleanup_stats

    @staticmethod
    async def get_cleanup_statistics() -> Dict[str, Any]:
        """Get current token statistics for monitoring."""
        try:
            async with async_session_maker() as db:
                stats = await TokenService.get_token_statistics(db)
                return {
                    "success": True,
                    "statistics": stats,
                    "generated_at": datetime.now(timezone.utc)
                }
        except Exception as e:
            logger.error(
                f"Failed to get token statistics: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "generated_at": datetime.now(timezone.utc)
            }

    @staticmethod
    async def validate_cleanup_health() -> Dict[str, Any]:
        """Validate the health of the cleanup system."""
        health_status = {
            "healthy": True,
            "checks": {},
            "timestamp": datetime.now(timezone.utc)
        }

        try:
            # Check database connectivity
            async with async_session_maker() as db:
                stats = await TokenService.get_token_statistics(db)
                health_status["checks"]["database"] = {
                    "status": "healthy",
                    "message": "Database connection successful"
                }
                health_status["checks"]["token_stats"] = stats

        except Exception as e:
            health_status["healthy"] = False
            health_status["checks"]["database"] = {
                "status": "unhealthy",
                "message": f"Database connection failed: {str(e)}"
            }
            logger.error(f"Health check failed: {str(e)}", exc_info=True)

        return health_status

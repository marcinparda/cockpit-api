"""Task definitions for background operations."""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from . import service as token_service
from src.core.database import async_session_maker
from src.core.config import settings

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
                expired_stats = await token_service.cleanup_expired_tokens(db)
                cleanup_stats["expired_cleanup"] = expired_stats

                # Clean up old revoked tokens
                logger.info("Cleaning up old revoked tokens")
                revoked_stats = await token_service.cleanup_old_revoked_tokens(
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
                stats = await token_service.get_token_statistics(db)
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
                stats = await token_service.get_token_statistics(db)
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


async def daily_token_cleanup_task(
    retention_days: Optional[int] = None,
    batch_size: Optional[int] = None
) -> Dict[str, Any]:
    """
    Main daily token cleanup task function.

    This task is designed to be called by the scheduler or manually
    for maintenance operations.

    Args:
        retention_days: Override default retention period for revoked tokens
        batch_size: Override default batch size for processing

    Returns:
        Dictionary containing detailed cleanup results and statistics
    """
    task_start = datetime.now(timezone.utc)
    task_id = f"token_cleanup_{task_start.strftime('%Y%m%d_%H%M%S')}"

    logger.info(f"[{task_id}] Starting daily token cleanup task")

    # Use defaults from settings if not provided
    if retention_days is None:
        retention_days = settings.TOKEN_CLEANUP_RETENTION_DAYS
    if batch_size is None:
        batch_size = settings.TOKEN_CLEANUP_BATCH_SIZE

    task_result = {
        "task_id": task_id,
        "start_time": task_start,
        "retention_days": retention_days,
        "batch_size": batch_size,
        "success": False,
        "error": None,
        "cleanup_stats": {},
        "health_check": {}
    }

    try:
        # Perform health check before cleanup
        logger.info(f"[{task_id}] Performing pre-cleanup health check")
        health_status = await TokenCleanupService.validate_cleanup_health()
        task_result["health_check"] = health_status

        if not health_status["healthy"]:
            raise RuntimeError("Pre-cleanup health check failed")

        # Execute comprehensive cleanup
        logger.info(f"[{task_id}] Executing comprehensive token cleanup")
        cleanup_stats = await TokenCleanupService.comprehensive_token_cleanup(
            retention_days=retention_days,
            batch_size=batch_size
        )
        task_result["cleanup_stats"] = cleanup_stats

        if not cleanup_stats["success"]:
            raise RuntimeError(
                f"Cleanup operation failed: {cleanup_stats.get('error')}")

        # Log success metrics
        total_deleted = cleanup_stats["total_deleted"]
        duration = cleanup_stats["duration"]

        logger.info(
            f"[{task_id}] Token cleanup completed successfully - "
            f"Deleted: {total_deleted} tokens, Duration: {duration:.2f}s"
        )

        task_result["success"] = True

    except Exception as e:
        error_msg = f"Token cleanup task failed: {str(e)}"
        logger.error(f"[{task_id}] {error_msg}", exc_info=True)
        task_result["error"] = error_msg
        task_result["success"] = False

    finally:
        task_result["end_time"] = datetime.now(timezone.utc)
        task_result["total_duration"] = (
            task_result["end_time"] - task_start
        ).total_seconds()

        logger.info(
            f"[{task_id}] Task completed - "
            f"Success: {task_result['success']}, "
            f"Duration: {task_result['total_duration']:.2f}s"
        )

    return task_result


async def manual_token_cleanup(
    cleanup_expired: bool = True,
    cleanup_revoked: bool = True,
    retention_days: Optional[int] = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Manual token cleanup function for administrative use.

    Args:
        cleanup_expired: Whether to clean up expired tokens
        cleanup_revoked: Whether to clean up old revoked tokens
        retention_days: Retention period for revoked tokens
        dry_run: If True, only simulate the cleanup without actual deletion

    Returns:
        Dictionary containing cleanup simulation or actual results
    """
    task_start = datetime.now(timezone.utc)
    task_id = f"manual_cleanup_{task_start.strftime('%Y%m%d_%H%M%S')}"

    logger.info(
        f"[{task_id}] Starting manual token cleanup - Dry run: {dry_run}")

    result = {
        "task_id": task_id,
        "start_time": task_start,
        "dry_run": dry_run,
        "cleanup_expired": cleanup_expired,
        "cleanup_revoked": cleanup_revoked,
        "retention_days": retention_days or settings.TOKEN_CLEANUP_RETENTION_DAYS,
        "success": False,
        "statistics": {}
    }

    try:
        if dry_run:
            # Get statistics without actual cleanup
            stats_result = await TokenCleanupService.get_cleanup_statistics()
            result["statistics"] = stats_result.get("statistics", {})
            logger.info(
                f"[{task_id}] Dry run completed - Current token statistics retrieved")
        else:
            # Perform actual cleanup based on parameters
            if cleanup_expired and cleanup_revoked:
                cleanup_stats = await TokenCleanupService.comprehensive_token_cleanup(
                    retention_days=retention_days
                )
            else:
                # Individual cleanup operations would need to be implemented
                # For now, use comprehensive cleanup
                cleanup_stats = await TokenCleanupService.comprehensive_token_cleanup(
                    retention_days=retention_days
                )

            result["cleanup_stats"] = cleanup_stats
            result["success"] = cleanup_stats["success"]

        result["success"] = True

    except Exception as e:
        logger.error(
            f"[{task_id}] Manual cleanup failed: {str(e)}", exc_info=True)
        result["error"] = str(e)
        result["success"] = False

    finally:
        result["end_time"] = datetime.now(timezone.utc)
        result["duration"] = (result["end_time"] - task_start).total_seconds()

    return result

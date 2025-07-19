"""Background task scheduler for the FastAPI application."""

import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.core.config import settings
from src.services.task_service import TokenCleanupService

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Task scheduler for background operations."""

    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self._running = False

    async def start(self) -> None:
        """Start the task scheduler."""
        if self._running:
            logger.warning("Scheduler is already running")
            return

        try:
            logger.info("Starting task scheduler")
            self.scheduler = AsyncIOScheduler()

            # Register token cleanup task if enabled
            if settings.TOKEN_CLEANUP_ENABLED:
                await self._register_token_cleanup_task()

            self.scheduler.start()
            self._running = True
            logger.info("Task scheduler started successfully")

        except Exception as e:
            logger.error(f"Failed to start scheduler: {str(e)}", exc_info=True)
            raise

    async def stop(self) -> None:
        """Stop the task scheduler."""
        if not self._running or not self.scheduler:
            logger.info("Scheduler is not running")
            return

        try:
            logger.info("Stopping task scheduler")
            self.scheduler.shutdown(wait=True)
            self._running = False
            logger.info("Task scheduler stopped successfully")

        except Exception as e:
            logger.error(f"Error stopping scheduler: {str(e)}", exc_info=True)

    async def _register_token_cleanup_task(self) -> None:
        """Register the daily token cleanup task."""
        if not self.scheduler:
            raise RuntimeError("Scheduler not initialized")

        try:
            # Parse cron expression (default: "0 2 * * *" - daily at 2 AM UTC)
            cron_parts = settings.TOKEN_CLEANUP_SCHEDULE.split()
            if len(cron_parts) != 5:
                raise ValueError("Invalid cron expression format")

            trigger = CronTrigger(
                minute=int(cron_parts[0]),
                hour=int(cron_parts[1]),
                day=cron_parts[2] if cron_parts[2] != '*' else None,
                month=cron_parts[3] if cron_parts[3] != '*' else None,
                day_of_week=cron_parts[4] if cron_parts[4] != '*' else None,
                timezone='UTC'
            )

            self.scheduler.add_job(
                func=self._token_cleanup_job,
                trigger=trigger,
                id='daily_token_cleanup',
                name='Daily Token Cleanup',
                max_instances=1,  # Prevent concurrent executions
                coalesce=True,    # Combine missed executions
                misfire_grace_time=3600  # Allow 1 hour grace period for missed jobs
            )

            logger.info(
                f"Token cleanup task registered with schedule: {settings.TOKEN_CLEANUP_SCHEDULE}"
            )

        except Exception as e:
            logger.error(
                f"Failed to register token cleanup task: {str(e)}", exc_info=True)
            raise

    async def _token_cleanup_job(self) -> None:
        """Execute the token cleanup job."""
        logger.info("Starting scheduled token cleanup job")

        try:
            cleanup_stats = await TokenCleanupService.comprehensive_token_cleanup(
                retention_days=settings.TOKEN_CLEANUP_RETENTION_DAYS,
                batch_size=settings.TOKEN_CLEANUP_BATCH_SIZE
            )

            if cleanup_stats["success"]:
                logger.info(
                    f"Token cleanup job completed successfully. "
                    f"Duration: {cleanup_stats['duration']:.2f}s, "
                    f"Total deleted: {cleanup_stats['total_deleted']}"
                )
            else:
                logger.error(
                    f"Token cleanup job failed: {cleanup_stats.get('error', 'Unknown error')}"
                )

        except Exception as e:
            logger.error(
                f"Token cleanup job encountered an error: {str(e)}", exc_info=True)

    def is_running(self) -> bool:
        """Check if the scheduler is running."""
        return self._running

    def get_jobs(self) -> list:
        """Get list of scheduled jobs."""
        if not self.scheduler:
            return []
        return self.scheduler.get_jobs()


# Global scheduler instance
task_scheduler = TaskScheduler()


@asynccontextmanager
async def scheduler_lifespan():
    """Context manager for scheduler lifecycle."""
    try:
        await task_scheduler.start()
        yield
    finally:
        await task_scheduler.stop()

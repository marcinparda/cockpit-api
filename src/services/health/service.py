"""Health check service with business logic."""

from datetime import datetime, timezone

from src.services.authentication.tokens.token_cleanup_service import validate_cleanup_health
from src.core.scheduler import task_scheduler
from src.core.config import settings
from .schemas import (
    HealthCheckResponse,
    CleanupHealthResponse,
    SchedulerInfo,
    ConfigInfo,
    JobInfo
)


class HealthService:
    """Service for health checks and system monitoring."""

    @staticmethod
    async def get_basic_health() -> HealthCheckResponse:
        """Get basic health status."""
        return HealthCheckResponse(status="healthy")

    @staticmethod
    async def get_cleanup_health() -> CleanupHealthResponse:
        """
        Get detailed health status of the token cleanup system.

        Returns:
            CleanupHealthResponse: Comprehensive health information including
            database connectivity, scheduler status, token statistics, and configuration.

        Raises:
            Exception: If health check fails for any reason.
        """
        # Get health status from the cleanup service
        health_status = await validate_cleanup_health()

        # Build scheduler information
        scheduler_info = SchedulerInfo(
            running=task_scheduler.is_running(),
            jobs=[
                JobInfo(
                    id=job.id,
                    name=job.name,
                    next_run_time=job.next_run_time.isoformat() if job.next_run_time else None
                )
                for job in task_scheduler.get_jobs()
            ]
        )

        # Build configuration information
        config_info = ConfigInfo(
            cleanup_enabled=settings.TOKEN_CLEANUP_ENABLED,
            cleanup_schedule=settings.TOKEN_CLEANUP_SCHEDULE,
            retention_days=settings.TOKEN_CLEANUP_RETENTION_DAYS,
            batch_size=settings.TOKEN_CLEANUP_BATCH_SIZE
        )

        return CleanupHealthResponse(
            status="healthy" if health_status["healthy"] else "unhealthy",
            timestamp=datetime.now(timezone.utc).isoformat(),
            health_checks=health_status["checks"],
            scheduler=scheduler_info,
            configuration=config_info
        )

"""Health check and monitoring endpoints."""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime, timezone

from src.services.task_service import TokenCleanupService
from src.core.scheduler import task_scheduler
from src.core.config import settings

router = APIRouter()


@router.get("")
async def health_check():
    return {"status": "healthy"}


@router.get("/cleanup", response_model=Dict[str, Any])
async def cleanup_health_check():
    """
    Get the health status of the token cleanup system.

    Returns information about:
    - Database connectivity
    - Scheduler status  
    - Current token statistics
    - System configuration
    """
    try:
        # Get health status from the cleanup service
        health_status = await TokenCleanupService.validate_cleanup_health()

        # Add scheduler information
        scheduler_info = {
            "running": task_scheduler.is_running(),
            "jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None
                }
                for job in task_scheduler.get_jobs()
            ]
        }

        # Add configuration information
        config_info = {
            "cleanup_enabled": settings.TOKEN_CLEANUP_ENABLED,
            "cleanup_schedule": settings.TOKEN_CLEANUP_SCHEDULE,
            "retention_days": settings.TOKEN_CLEANUP_RETENTION_DAYS,
            "batch_size": settings.TOKEN_CLEANUP_BATCH_SIZE
        }

        return {
            "status": "healthy" if health_status["healthy"] else "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "health_checks": health_status["checks"],
            "scheduler": scheduler_info,
            "configuration": config_info
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get cleanup health status: {str(e)}"
        )
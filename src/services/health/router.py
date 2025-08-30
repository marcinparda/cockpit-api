"""Health check and monitoring endpoints."""

from fastapi import APIRouter, HTTPException

from .service import HealthService
from .schemas import HealthCheckResponse, CleanupHealthResponse

router = APIRouter()


@router.get("", response_model=HealthCheckResponse)
async def health_check():
    """Basic health check endpoint."""
    return await HealthService.get_basic_health()


@router.get("/cleanup", response_model=CleanupHealthResponse)
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
        return await HealthService.get_cleanup_health()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get cleanup health status: {str(e)}"
        )
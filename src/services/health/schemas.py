"""Health check response schemas."""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class HealthCheckResponse(BaseModel):
    """Basic health check response."""
    status: str


class JobInfo(BaseModel):
    """Information about a scheduled job."""
    id: str
    name: str
    next_run_time: Optional[str] = None


class SchedulerInfo(BaseModel):
    """Information about the scheduler."""
    running: bool
    jobs: List[JobInfo]


class ConfigInfo(BaseModel):
    """System configuration information."""
    cleanup_enabled: bool
    cleanup_schedule: str
    retention_days: int
    batch_size: int


class CleanupHealthResponse(BaseModel):
    """Detailed health check response for cleanup system."""
    status: str
    timestamp: str
    health_checks: Dict[str, Any]
    scheduler: SchedulerInfo
    configuration: ConfigInfo

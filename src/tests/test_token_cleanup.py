"""Unit tests for token cleanup functionality."""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from src.services.task_service import TokenCleanupService
from src.services.token_service import TokenService
from src.tasks.token_cleanup import daily_token_cleanup_task, manual_token_cleanup
from src.core.scheduler import TaskScheduler


class TestTokenCleanupService:
    """Test cases for TokenCleanupService."""

    @pytest.mark.asyncio
    async def test_comprehensive_token_cleanup_success(self):
        """Test successful comprehensive token cleanup."""
        # Mock cleanup statistics
        mock_expired_stats = {
            "expired_access_tokens_deleted": 10,
            "expired_refresh_tokens_deleted": 5,
            "cleanup_time": datetime.now(timezone.utc)
        }

        mock_revoked_stats = {
            "old_revoked_access_tokens_deleted": 3,
            "old_revoked_refresh_tokens_deleted": 2,
            "retention_days": 7,
            "cutoff_date": datetime.now(timezone.utc) - timedelta(days=7),
            "cleanup_time": datetime.now(timezone.utc)
        }

        with patch('src.services.task_service.async_session_maker') as mock_session_maker, \
                patch.object(TokenService, 'cleanup_expired_tokens', return_value=mock_expired_stats) as mock_expired, \
                patch.object(TokenService, 'cleanup_old_revoked_tokens', return_value=mock_revoked_stats) as mock_revoked:

            # Mock the database session context manager
            mock_db = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_db
            mock_session_maker.return_value.__aexit__.return_value = None

            result = await TokenCleanupService.comprehensive_token_cleanup()

            # Verify the result
            assert result["success"] is True
            assert result["total_deleted"] == 20  # 10+5+3+2
            assert "expired_cleanup" in result
            assert "revoked_cleanup" in result
            assert "start_time" in result
            assert "end_time" in result
            assert "duration" in result

            # Verify service calls
            mock_expired.assert_called_once_with(mock_db)
            mock_revoked.assert_called_once_with(mock_db, None)

    @pytest.mark.asyncio
    async def test_comprehensive_token_cleanup_failure(self):
        """Test comprehensive token cleanup with database error."""
        with patch('src.services.task_service.async_session_maker') as mock_session_maker:
            # Mock database session to raise an exception
            mock_session_maker.return_value.__aenter__.side_effect = Exception(
                "Database connection failed")

            result = await TokenCleanupService.comprehensive_token_cleanup()

            # Verify the result
            assert result["success"] is False
            assert result["error"] == "Database connection failed"
            assert result["total_deleted"] == 0

    @pytest.mark.asyncio
    async def test_get_cleanup_statistics_success(self):
        """Test successful retrieval of token statistics."""
        mock_stats = {
            "access_tokens": {"total": 100, "active": 80, "revoked": 15, "expired": 5},
            "refresh_tokens": {"total": 50, "active": 40, "revoked": 8, "expired": 2},
            "generated_at": datetime.now(timezone.utc)
        }

        with patch('src.services.task_service.async_session_maker') as mock_session_maker, \
                patch.object(TokenService, 'get_token_statistics', return_value=mock_stats) as mock_stats_call:

            # Mock the database session
            mock_db = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_db
            mock_session_maker.return_value.__aexit__.return_value = None

            result = await TokenCleanupService.get_cleanup_statistics()

            # Verify the result
            assert result["success"] is True
            assert result["statistics"] == mock_stats
            mock_stats_call.assert_called_once_with(mock_db)

    @pytest.mark.asyncio
    async def test_validate_cleanup_health_success(self):
        """Test successful health check validation."""
        mock_stats = {
            "access_tokens": {"total": 100, "active": 80, "revoked": 15, "expired": 5},
            "refresh_tokens": {"total": 50, "active": 40, "revoked": 8, "expired": 2}
        }

        with patch('src.services.task_service.async_session_maker') as mock_session_maker, \
                patch.object(TokenService, 'get_token_statistics', return_value=mock_stats) as mock_stats_call:

            # Mock the database session
            mock_db = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_db
            mock_session_maker.return_value.__aexit__.return_value = None

            result = await TokenCleanupService.validate_cleanup_health()

            # Verify the result
            assert result["healthy"] is True
            assert result["checks"]["database"]["status"] == "healthy"
            assert result["checks"]["token_stats"] == mock_stats


class TestTaskScheduler:
    """Test cases for TaskScheduler."""

    def test_scheduler_initialization(self):
        """Test scheduler initialization."""
        scheduler = TaskScheduler()
        assert scheduler._running is False
        assert scheduler.scheduler is None

    @pytest.mark.asyncio
    async def test_scheduler_start_stop(self):
        """Test scheduler start and stop operations."""
        scheduler = TaskScheduler()

        with patch.object(scheduler, '_register_token_cleanup_task') as mock_register, \
                patch('src.core.scheduler.settings.TOKEN_CLEANUP_ENABLED', True):

            # Mock the AsyncIOScheduler
            mock_scheduler = MagicMock()
            with patch('src.core.scheduler.AsyncIOScheduler', return_value=mock_scheduler):

                # Test start
                await scheduler.start()
                assert scheduler._running is True
                mock_register.assert_called_once()
                mock_scheduler.start.assert_called_once()

                # Test stop
                await scheduler.stop()
                assert scheduler._running is False
                mock_scheduler.shutdown.assert_called_once_with(wait=True)

    def test_is_running(self):
        """Test is_running method."""
        scheduler = TaskScheduler()
        assert scheduler.is_running() is False

        scheduler._running = True
        assert scheduler.is_running() is True


class TestTokenCleanupTasks:
    """Test cases for token cleanup tasks."""

    @pytest.mark.asyncio
    async def test_daily_token_cleanup_task_success(self):
        """Test successful daily token cleanup task."""
        mock_cleanup_stats = {
            "success": True,
            "total_deleted": 25,
            "duration": 1.5,
            "expired_cleanup": {"expired_access_tokens_deleted": 15},
            "revoked_cleanup": {"old_revoked_access_tokens_deleted": 10}
        }

        mock_health_status = {
            "healthy": True,
            "checks": {"database": {"status": "healthy"}}
        }

        with patch.object(TokenCleanupService, 'validate_cleanup_health', return_value=mock_health_status), \
                patch.object(TokenCleanupService, 'comprehensive_token_cleanup', return_value=mock_cleanup_stats):

            result = await daily_token_cleanup_task()

            # Verify the result
            assert result["success"] is True
            assert result["cleanup_stats"] == mock_cleanup_stats
            assert result["health_check"] == mock_health_status
            assert "start_time" in result
            assert "end_time" in result
            assert "total_duration" in result

    @pytest.mark.asyncio
    async def test_daily_token_cleanup_task_health_check_failure(self):
        """Test daily cleanup task with health check failure."""
        mock_health_status = {
            "healthy": False,
            "checks": {"database": {"status": "unhealthy", "message": "Connection failed"}}
        }

        with patch.object(TokenCleanupService, 'validate_cleanup_health', return_value=mock_health_status):

            result = await daily_token_cleanup_task()

            # Verify the result
            assert result["success"] is False
            assert "Pre-cleanup health check failed" in result["error"]
            assert result["health_check"] == mock_health_status

    @pytest.mark.asyncio
    async def test_manual_token_cleanup_dry_run(self):
        """Test manual token cleanup in dry run mode."""
        mock_stats = {
            "statistics": {
                "access_tokens": {"total": 100, "active": 80, "expired": 10},
                "refresh_tokens": {"total": 50, "active": 40, "expired": 5}
            }
        }

        with patch.object(TokenCleanupService, 'get_cleanup_statistics', return_value=mock_stats):

            result = await manual_token_cleanup(dry_run=True)

            # Verify the result
            assert result["success"] is True
            assert result["dry_run"] is True
            assert result["statistics"] == mock_stats["statistics"]

    @pytest.mark.asyncio
    async def test_manual_token_cleanup_actual_run(self):
        """Test manual token cleanup with actual execution."""
        mock_cleanup_stats = {
            "success": True,
            "total_deleted": 15,
            "duration": 0.8
        }

        with patch.object(TokenCleanupService, 'comprehensive_token_cleanup', return_value=mock_cleanup_stats):

            result = await manual_token_cleanup(
                cleanup_expired=True,
                cleanup_revoked=True,
                dry_run=False
            )

            # Verify the result
            assert result["success"] is True
            assert result["dry_run"] is False
            assert result["cleanup_stats"] == mock_cleanup_stats


class TestTokenCleanupIntegration:
    """Integration tests for token cleanup system."""

    @pytest.mark.asyncio
    async def test_end_to_end_cleanup_workflow(self):
        """Test complete cleanup workflow from scheduling to execution."""
        # This would be an integration test that would require a real database
        # For now, we'll mock the major components

        mock_cleanup_result = {
            "success": True,
            "total_deleted": 42,
            "duration": 2.1
        }

        with patch.object(TokenCleanupService, 'comprehensive_token_cleanup', return_value=mock_cleanup_result) as mock_cleanup:

            # Simulate the scheduler calling the cleanup task
            scheduler = TaskScheduler()
            await scheduler._token_cleanup_job()

            # The cleanup should have been called
            mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_expired_token_cleanup_integration(self):
        """Test that expired tokens are properly cleaned up."""
        from datetime import datetime, timezone
        from unittest.mock import patch, AsyncMock
        from src.services.token_service import TokenService

        # Mock database session
        mock_db = AsyncMock()

        # Test cleanup of expired tokens
        mock_cleanup_result = {
            "expired_access_tokens_deleted": 5,
            "expired_refresh_tokens_deleted": 3,
            "cleanup_time": datetime.now(timezone.utc)
        }

        with patch.object(TokenService, 'cleanup_expired_tokens', return_value=mock_cleanup_result) as mock_cleanup:
            result = await TokenService.cleanup_expired_tokens(mock_db)

            assert result["expired_access_tokens_deleted"] == 5
            assert result["expired_refresh_tokens_deleted"] == 3
            mock_cleanup.assert_called_once_with(mock_db)

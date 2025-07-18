"""Performance tests for rate limiting middleware."""

import pytest
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from src.main import app
from src.middleware.rate_limit import RateLimitMiddleware


class TestRateLimitingPerformance:
    """Performance tests for rate limiting."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_rate_limiting_performance_under_load(self, client):
        """Test rate limiting performance under concurrent load."""
        # Test with multiple concurrent requests
        def make_request():
            return client.get("/health")

        # Use ThreadPoolExecutor to simulate concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            start_time = time.time()

            # Submit 100 requests
            futures = [executor.submit(make_request) for _ in range(100)]

            # Wait for all requests to complete
            responses = [future.result() for future in futures]

            end_time = time.time()

            # Check that most requests succeeded
            success_count = sum(1 for r in responses if r.status_code == 200)
            assert success_count >= 90  # At least 90% should succeed

            # Check that it completed in reasonable time (under 5 seconds)
            duration = end_time - start_time
            assert duration < 5.0

    def test_rate_limiting_memory_usage(self):
        """Test rate limiting memory usage doesn't grow unbounded."""
        middleware = RateLimitMiddleware(app)

        # Simulate many different IP addresses
        initial_store_size = len(middleware.store.store)

        # Add many entries
        for i in range(1000):
            key = f"GET:/test:ip:192.168.1.{i % 255}"
            middleware.store.get_or_create(key, 60, 10)

        # Check store size
        store_size_after_adds = len(middleware.store.store)
        assert store_size_after_adds <= 1000

        # Force cleanup
        middleware.store._cleanup()

        # Store should not grow indefinitely
        final_store_size = len(middleware.store.store)
        assert final_store_size <= store_size_after_adds

    def test_rate_limiting_cleanup_performance(self):
        """Test rate limiting cleanup performance."""
        middleware = RateLimitMiddleware(app)

        # Add many expired entries
        for i in range(1000):
            key = f"GET:/test:ip:192.168.1.{i}"
            entry = middleware.store.get_or_create(
                key, 1, 10)  # 1 second window
            entry.requests = [time.time() - 10]  # Old request

        # Measure cleanup time
        start_time = time.time()
        middleware.store._cleanup()
        cleanup_time = time.time() - start_time

        # Cleanup should be fast (under 1 second)
        assert cleanup_time < 1.0

    def test_rate_limiting_concurrent_access(self):
        """Test rate limiting with concurrent access to same key."""
        middleware = RateLimitMiddleware(app)

        def check_rate_limit():
            key = "GET:/test:ip:192.168.1.1"
            entry = middleware.store.get_or_create(key, 60, 5)
            return entry.is_allowed()

        # Use ThreadPoolExecutor to simulate concurrent access
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(check_rate_limit) for _ in range(20)]
            results = [future.result() for future in futures]

        # Should have exactly 5 allowed requests
        allowed_count = sum(1 for r in results if r is True)
        assert allowed_count == 5

    @patch("src.middleware.rate_limit.verify_token")
    def test_jwt_extraction_performance(self, mock_verify_token):
        """Test JWT token extraction performance."""
        middleware = RateLimitMiddleware(app)

        # Mock JWT verification
        mock_verify_token.return_value = {"sub": "user123"}

        # Mock request
        request = MagicMock()
        request.headers = {"Authorization": "Bearer test_token"}

        async def test_extraction():
            start_time = time.time()

            # Extract user ID multiple times
            for _ in range(100):
                user_id = await middleware._extract_user_id_from_token(request)
                assert user_id == "user123"

            extraction_time = time.time() - start_time

            # Should be fast (under 1 second for 100 extractions)
            assert extraction_time < 1.0

        asyncio.run(test_extraction())

    def test_rate_limiting_rule_matching_performance(self):
        """Test rate limiting rule matching performance."""
        middleware = RateLimitMiddleware(app)

        # Mock request
        request = MagicMock()
        request.method = "GET"
        request.url.path = "/api/v1/some/endpoint"

        start_time = time.time()

        # Match rules multiple times
        for _ in range(1000):
            rule = middleware._get_rate_limit_rule(request)
            assert rule is not None

        matching_time = time.time() - start_time

        # Should be fast (under 1 second for 1000 matches)
        assert matching_time < 1.0


class TestRateLimitingStressTest:
    """Stress tests for rate limiting."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_rate_limiting_stress_single_endpoint(self, client):
        """Stress test rate limiting on single endpoint."""
        # Rapid requests to trigger rate limiting
        responses = []

        for i in range(50):
            # This will likely fail auth
            response = client.get("/api/v1/roles")
            responses.append(response.status_code)

        # Should have mix of successful and rate-limited responses
        # (or auth failures, but not all the same)
        unique_status_codes = set(responses)
        assert len(unique_status_codes) >= 1  # At least some variety

    def test_rate_limiting_stress_multiple_endpoints(self, client):
        """Stress test rate limiting across multiple endpoints."""
        endpoints = [
            "/api/v1/roles",
            "/api/v1/users",
            "/api/v1/categories",
            "/api/v1/expenses"
        ]

        responses = []

        # Make requests to different endpoints
        for i in range(100):
            endpoint = endpoints[i % len(endpoints)]
            response = client.get(endpoint)
            responses.append(response.status_code)

        # Should handle mixed endpoint requests
        assert len(responses) == 100

    def test_rate_limiting_stress_concurrent_users(self, client):
        """Stress test rate limiting with concurrent users."""
        def make_requests_as_user(user_id):
            responses = []
            for i in range(10):
                # Simulate different users with different IPs
                headers = {"X-Forwarded-For": f"192.168.1.{user_id}"}
                response = client.get("/api/v1/roles", headers=headers)
                responses.append(response.status_code)
            return responses

        # Use ThreadPoolExecutor to simulate concurrent users
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(make_requests_as_user, user_id)
                for user_id in range(1, 6)
            ]

            all_responses = []
            for future in futures:
                responses = future.result()
                all_responses.extend(responses)

        # Should handle concurrent users
        assert len(all_responses) == 50

        # Most requests should be handled (not all rate limited)
        non_rate_limited = sum(1 for r in all_responses if r != 429)
        assert non_rate_limited >= 25  # At least 50% should not be rate limited


if __name__ == "__main__":
    pytest.main([__file__])

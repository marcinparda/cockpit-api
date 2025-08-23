"""Rate limiting middleware for FastAPI applications."""

import time
from typing import Dict, Optional, Any
from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

# Import verify_token at module level to make it patchable in tests
try:
    from src.app.auth.jwt import verify_token
except ImportError:
    # Handle the case where jwt module is not available during testing
    async def verify_token(token: str, db: Optional[AsyncSession] = None) -> Dict[str, Any]:
        """Placeholder function when jwt module is not available."""
        return {}


class RateLimitEntry:
    """Single rate limit entry for tracking requests."""

    def __init__(self, window_seconds: int, max_requests: int):
        self.window_seconds = window_seconds
        self.max_requests = max_requests
        self.requests: list[float] = []
        self.reset_time = time.time() + window_seconds

    def is_allowed(self) -> bool:
        """Check if request is allowed under current rate limit."""
        current_time = time.time()

        # Remove old requests outside the window
        cutoff_time = current_time - self.window_seconds
        self.requests = [
            req_time for req_time in self.requests if req_time > cutoff_time]

        # Check if we're under the limit
        if len(self.requests) < self.max_requests:
            self.requests.append(current_time)
            return True

        return False

    def time_until_reset(self) -> int:
        """Get seconds until rate limit resets."""
        if not self.requests:
            return 0

        oldest_request = min(self.requests)
        reset_time = oldest_request + self.window_seconds
        return max(0, int(reset_time - time.time()))


class RateLimitStore:
    """In-memory store for rate limit tracking."""

    def __init__(self):
        self.store: Dict[str, RateLimitEntry] = {}
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()

    def get_or_create(self, key: str, window_seconds: int, max_requests: int) -> RateLimitEntry:
        """Get or create rate limit entry for key."""
        # Always create the entry if it doesn't exist, don't just check
        if key not in self.store:
            self.store[key] = RateLimitEntry(window_seconds, max_requests)

        # Periodic cleanup
        current_time = time.time()
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup()
            self.last_cleanup = current_time

        # Ensure the key still exists after cleanup
        if key not in self.store:
            self.store[key] = RateLimitEntry(window_seconds, max_requests)

        return self.store[key]

    def _cleanup(self):
        """Remove expired entries."""
        current_time = time.time()
        expired_keys = []

        for key, entry in self.store.items():
            if not entry.requests:
                expired_keys.append(key)
            else:
                last_request = max(entry.requests)
                if current_time - last_request > entry.window_seconds * 2:
                    expired_keys.append(key)

        for key in expired_keys:
            del self.store[key]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with configurable rules."""

    def __init__(self, app, rate_limit_rules: Optional[Dict[str, Dict[str, int]]] = None):
        super().__init__(app)
        self.store = RateLimitStore()
        self.rate_limit_rules = rate_limit_rules or self._get_default_rules()

    def _get_default_rules(self) -> Dict[str, Dict[str, int]]:
        """Get default rate limiting rules."""
        return {
            # Authentication endpoints
            # 5 per minute per IP
            "POST:/api/v1/auth/login": {"window": 60, "max_requests": 5},
            # 3 per minute per user
            "POST:/api/v1/auth/change-password": {"window": 60, "max_requests": 3},
            # 10 per minute per user
            "POST:/api/v1/auth/refresh": {"window": 60, "max_requests": 10},

            # User management endpoints
            # 10 per minute for admins
            "POST:/api/v1/users": {"window": 60, "max_requests": 10},
            # 5 per minute for admins
            "PUT:/api/v1/users": {"window": 60, "max_requests": 5},
            # 5 per minute for admins
            "DELETE:/api/v1/users": {"window": 60, "max_requests": 5},

            # Password reset endpoints
            # 3 per minute for admins
            "POST:/api/v1/users/*/reset-password": {"window": 60, "max_requests": 3},

            # General API endpoints
            # 100 per minute per IP
            "GET:*": {"window": 60, "max_requests": 100},
            # 100 per minute per IP
            "POST:*": {"window": 60, "max_requests": 100},
            # 100 per minute per IP
            "PUT:*": {"window": 60, "max_requests": 100},
            # 100 per minute per IP
            "DELETE:*": {"window": 60, "max_requests": 100},
        }

    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        # Skip rate limiting for health checks and documentation
        path = request.url.path
        if path in ["/health", "/health/", "/", "/api/docs", "/openapi.json"]:
            return await call_next(request)

        # Get rate limit rule for this endpoint
        rule = self._get_rate_limit_rule(request)
        if not rule:
            return await call_next(request)

        # Generate rate limit key
        rate_limit_key = await self._generate_rate_limit_key(request, rule)

        # Check rate limit
        entry = self.store.get_or_create(
            rate_limit_key,
            rule["window"],
            rule["max_requests"]
        )

        if not entry.is_allowed():
            # Rate limit exceeded
            retry_after = entry.time_until_reset()
            return Response(
                content=f'{{"detail": "Rate limit exceeded. Try again in {retry_after} seconds."}}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={
                    "Content-Type": "application/json",
                    "X-RateLimit-Limit": str(rule["max_requests"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + retry_after),
                    "Retry-After": str(retry_after)
                }
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        remaining = rule["max_requests"] - len(entry.requests)
        response.headers["X-RateLimit-Limit"] = str(rule["max_requests"])
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(
            int(time.time()) + rule["window"])

        return response

    def _get_rate_limit_rule(self, request: Request) -> Optional[Dict[str, int]]:
        """Get rate limit rule for request."""
        method = request.method
        path = request.url.path

        # Try exact match first
        exact_key = f"{method}:{path}"
        if exact_key in self.rate_limit_rules:
            return self.rate_limit_rules[exact_key]

        # Try pattern matching for user ID endpoints
        if "/users/" in path and path.count("/") >= 4:
            pattern_key = f"{method}:/api/v1/users/*/reset-password"
            if pattern_key in self.rate_limit_rules and "reset-password" in path:
                return self.rate_limit_rules[pattern_key]

        # Try wildcard match
        wildcard_key = f"{method}:*"
        if wildcard_key in self.rate_limit_rules:
            return self.rate_limit_rules[wildcard_key]

        return None

    async def _generate_rate_limit_key(self, request: Request, rule: Dict[str, int]) -> str:
        """Generate unique rate limit key based on request."""
        method = request.method
        path = request.url.path

        # For user-specific endpoints, use user ID if available
        user_specific_endpoints = [
            "/api/v1/auth/change-password",
            "/api/v1/auth/refresh"
        ]

        if any(endpoint in path for endpoint in user_specific_endpoints):
            # Try to extract user ID from JWT token
            user_id = await self._extract_user_id_from_token(request)
            if user_id:
                return f"{method}:{path}:user:{user_id}"

        # For admin endpoints, use user ID if available
        admin_endpoints = [
            "/api/v1/users"
        ]

        if any(endpoint in path for endpoint in admin_endpoints):
            user_id = await self._extract_user_id_from_token(request)
            if user_id:
                return f"{method}:{path}:admin:{user_id}"

        # Default to IP-based rate limiting
        client_ip = self._get_client_ip(request)
        return f"{method}:{path}:ip:{client_ip}"

    async def _extract_user_id_from_token(self, request: Request) -> Optional[str]:
        """Extract user ID from JWT token."""
        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return None

            token = auth_header.split(" ")[1]

            # Use the module-level import (now async)
            if verify_token is None:
                return None

            payload = await verify_token(token)
            return payload.get("sub")
        except Exception:
            return None

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct client IP
        return request.client.host if request.client else "unknown"

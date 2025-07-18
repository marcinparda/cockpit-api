"""JWT token validation middleware."""

from typing import Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.auth.jwt import extract_token_id
from src.auth.jwt_blacklist import is_token_blacklisted


class JWTValidationMiddleware(BaseHTTPMiddleware):
    """Middleware to validate JWT tokens and check blacklist."""

    def __init__(self, app, exclude_paths: Optional[list[str]] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/",
            "/api/docs",
            "/openapi.json",
            "/api/v1/auth/login",
            "/api/v1/auth/refresh",
            "/docs",
            "/redoc"
        ]

    async def dispatch(self, request: Request, call_next):
        """Process request with JWT validation."""
        # Skip validation for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Skip validation for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Get authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            # Let the endpoint handle missing auth if needed
            return await call_next(request)

        if not auth_header.startswith("Bearer "):
            # Let the endpoint handle invalid auth format if needed
            return await call_next(request)

        token = auth_header.split(" ")[1]

        # Quick blacklist check without full verification
        token_id = extract_token_id(token)
        if token_id and is_token_blacklisted(token_id):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Token has been invalidated"},
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Continue with request
        return await call_next(request)

"""JWT token validation middleware."""

from typing import Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.auth.jwt import extract_token_id
from src.services.token_service import TokenService
from src.core.database import async_session_maker


class JWTValidationMiddleware(BaseHTTPMiddleware):
    """Middleware to validate JWT tokens using database token tracking."""

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
            "/api/v1/health/cleanup",
            "/api/v1/health/tokens/statistics",
            "/api/v1/health/cleanup/manual",
            "/api/v1/health/cleanup/dry-run"
        ]

    async def dispatch(self, request: Request, call_next):
        """Process request with JWT validation using database token tracking."""
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

        # Validate token using database
        token_id = extract_token_id(token)
        if token_id:
            try:
                async with async_session_maker() as db:
                    is_valid = await TokenService.is_access_token_valid(db, token_id)
                    if not is_valid:
                        return JSONResponse(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            content={
                                "detail": "Token has been invalidated or expired"},
                            headers={"WWW-Authenticate": "Bearer"}
                        )

                    # Update token last used timestamp
                    await TokenService.update_access_token_last_used(db, token_id)

            except Exception as e:
                # Log the error but don't block the request
                # Let the endpoint handle token validation if needed
                import logging
                logging.getLogger(__name__).warning(
                    f"Token validation error in middleware: {str(e)}"
                )

        # Continue with request
        return await call_next(request)

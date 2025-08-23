"""JWT token validation middleware."""

from typing import Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError as DatabaseError
from jose import JWTError

from src.app.auth.jwt import extract_token_id
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

        # Get token from Authorization header or cookies
        token = None

        # Try Authorization header first
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        else:
            # Try cookie if no Bearer token
            token = request.cookies.get("access_token")

        if not token:
            # Let the endpoint handle missing auth if needed
            return await call_next(request)

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

            except DatabaseError as db_error:
                # Log database-related errors but don't block the request
                import logging
                logging.getLogger(__name__).error(
                    f"Database error during token validation: {str(db_error)}"
                )
            except JWTError as jwt_error:
                # Log JWT-related errors but don't block the request
                import logging
                logging.getLogger(__name__).warning(
                    f"JWT error during token validation: {str(jwt_error)}"
                )

        # Continue with request
        return await call_next(request)

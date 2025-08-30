"""JWT token validation middleware."""

from typing import List
from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError as DatabaseError
from jose import JWTError

from src.services.authentication.tokens.service import extract_token_id
from src.services.authentication.tokens.service import is_access_token_valid, update_access_token_last_used_timestamp
from src.core.database import async_session_maker
import logging


class JWTValidationMiddleware(BaseHTTPMiddleware):
    """Middleware to validate JWT tokens using database token tracking."""

    def __init__(self, app, exclude_paths: List[str] = []):
        super().__init__(app)
        self.exclude_paths = (
            [
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
            if len(exclude_paths) == 0 else exclude_paths
        )

    async def dispatch(self, request: Request, call_next):
        """Process request with JWT validation using database token tracking."""
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        if request.method == "OPTIONS":
            return await call_next(request)

        token = request.cookies.get("access_token")

        if not token:
            return await call_next(request)

        token_id = extract_token_id(token)
        if token_id:
            try:
                async with async_session_maker() as db:
                    is_valid = await is_access_token_valid(db, token_id)
                    if not is_valid:
                        return JSONResponse(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            content={
                                "detail": "Token has been invalidated or expired"},
                            headers={"WWW-Authenticate": "Bearer"}
                        )

                    await update_access_token_last_used_timestamp(db, token_id)

            except DatabaseError as db_error:
                logging.getLogger(__name__).error(
                    f"Database error during token validation: {str(db_error)}"
                )
            except JWTError as jwt_error:
                logging.getLogger(__name__).warning(
                    f"JWT error during token validation: {str(jwt_error)}"
                )

        return await call_next(request)

import logging
from datetime import datetime, timezone

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from src.core.config import settings

logger = logging.getLogger(__name__)


class MCPAPIKeyMiddleware:
    def __init__(self, app: ASGIApp, api_key: str) -> None:
        self.app = app
        self.api_key = api_key

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        auth = headers.get(b"authorization", b"").decode()

        if not auth.startswith("Bearer "):
            await self._send_401(scope, receive, send)
            return

        token = auth[len("Bearer "):]

        if self.api_key and token == self.api_key:
            await self.app(scope, receive, send)
            return

        if await self._validate_oauth_token(token):
            await self.app(scope, receive, send)
            return

        await self._send_401(scope, receive, send)

    async def _validate_oauth_token(self, token: str) -> bool:
        try:
            from src.services.oauth.repository import (
                get_oauth_access_token,
                update_oauth_access_token_last_used,
            )
            from src.core.database import async_session_maker

            async with async_session_maker() as db:
                record = await get_oauth_access_token(db, token)
                if record is None:
                    return False
                if record.is_revoked:
                    return False
                now = datetime.now(timezone.utc).replace(tzinfo=None)
                if record.expires_at <= now:
                    return False
                await update_oauth_access_token_last_used(db, token)
                return True
        except Exception:
            logger.exception("Error validating OAuth token")
            return False

    async def _send_401(self, scope: Scope, receive: Receive, send: Send) -> None:
        base = settings.OAUTH_SERVER_URL.rstrip("/")
        resource_metadata_url = f"{base}/.well-known/oauth-protected-resource"
        response = JSONResponse(
            {"detail": "Unauthorized"},
            status_code=401,
            headers={"WWW-Authenticate": f'Bearer resource_metadata="{resource_metadata_url}"'},
        )
        await response(scope, receive, send)

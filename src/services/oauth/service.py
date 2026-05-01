import base64
import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.services.oauth import repository
from src.services.oauth.models import OAuthClient
from src.services.oauth.schemas import ClientRegistrationRequest, ClientRegistrationResponse, TokenResponse


def _verify_pkce(code_verifier: str, code_challenge: str, method: str = "S256") -> bool:
    if method != "S256":
        return False
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    computed = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return secrets.compare_digest(computed, code_challenge)


def _now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def register_client(
    db: AsyncSession, request: ClientRegistrationRequest
) -> ClientRegistrationResponse:
    client_id = str(uuid4())
    redirect_uris_json = json.dumps(request.redirect_uris)
    await repository.create_oauth_client(
        db=db,
        client_id=client_id,
        client_name=request.client_name,
        redirect_uris_json=redirect_uris_json,
        grant_types=",".join(request.grant_types),
        response_types=",".join(request.response_types),
        token_endpoint_auth_method=request.token_endpoint_auth_method,
    )
    return ClientRegistrationResponse(
        client_id=client_id,
        client_name=request.client_name,
        redirect_uris=request.redirect_uris,
        grant_types=request.grant_types,
        response_types=request.response_types,
        token_endpoint_auth_method=request.token_endpoint_auth_method,
    )


async def validate_authorize_request(
    db: AsyncSession,
    client_id: str,
    redirect_uri: str,
    response_type: str,
    code_challenge: str,
    code_challenge_method: str,
) -> OAuthClient:
    if response_type != "code":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="unsupported_response_type")

    if code_challenge_method != "S256":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="unsupported code_challenge_method — only S256 supported")

    if not code_challenge:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="code_challenge required")

    client = await repository.get_oauth_client_by_client_id(db, client_id)
    if not client or not client.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="invalid_client")

    allowed_uris = json.loads(client.redirect_uris)
    if redirect_uri not in allowed_uris:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="redirect_uri not registered for this client")

    return client


async def create_auth_code(
    db: AsyncSession,
    client: OAuthClient,
    user_id: UUID,
    redirect_uri: str,
    scope: Optional[str],
    code_challenge: str,
    code_challenge_method: str,
) -> str:
    code = secrets.token_urlsafe(32)
    expires_at = (_now_naive() + timedelta(minutes=settings.OAUTH_AUTH_CODE_EXPIRE_MINUTES))
    await repository.create_authorization_code(
        db=db,
        code=code,
        client_id=str(client.client_id),
        user_id=user_id,
        redirect_uri=redirect_uri,
        scope=scope,
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method,
        expires_at=expires_at,
    )
    return code


async def exchange_code_for_token(
    db: AsyncSession,
    code: str,
    redirect_uri: str,
    client_id: str,
    code_verifier: str,
) -> TokenResponse:
    auth_code = await repository.get_authorization_code(db, code)

    if not auth_code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_grant")

    now = _now_naive()

    if auth_code.is_used:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_grant")

    if auth_code.expires_at <= now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_grant")

    if auth_code.client_id != client_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_grant")

    if auth_code.redirect_uri != redirect_uri:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_grant")

    if not _verify_pkce(code_verifier, str(auth_code.code_challenge),
                         str(auth_code.code_challenge_method)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_grant")

    await repository.mark_authorization_code_used(db, code)

    return await _issue_token_pair(
        db=db,
        client_id=client_id,
        user_id=UUID(str(auth_code.user_id)),
        scope=auth_code.scope,
    )


async def refresh_oauth_token(db: AsyncSession, refresh_token: str) -> TokenResponse:
    record = await repository.get_oauth_access_token_by_refresh_token(db, refresh_token)

    if not record:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_grant")

    now = _now_naive()

    if record.refresh_token_is_revoked:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_grant")

    if record.refresh_token_expires_at is None or record.refresh_token_expires_at <= now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_grant")

    await repository.revoke_oauth_access_token_and_refresh(db, str(record.token))

    return await _issue_token_pair(
        db=db,
        client_id=str(record.client_id),
        user_id=UUID(str(record.user_id)),
        scope=record.scope,
    )


async def _issue_token_pair(
    db: AsyncSession,
    client_id: str,
    user_id: UUID,
    scope: Optional[str],
) -> TokenResponse:
    now = _now_naive()
    access_token = secrets.token_urlsafe(48)
    refresh_token = secrets.token_urlsafe(48)
    expires_at = now + timedelta(hours=settings.OAUTH_ACCESS_TOKEN_EXPIRE_HOURS)
    refresh_expires_at = now + timedelta(days=settings.OAUTH_REFRESH_TOKEN_EXPIRE_DAYS)

    await repository.create_oauth_access_token(
        db=db,
        token=access_token,
        client_id=client_id,
        user_id=user_id,
        scope=scope,
        expires_at=expires_at,
        refresh_token=refresh_token,
        refresh_token_expires_at=refresh_expires_at,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="Bearer",
        expires_in=settings.OAUTH_ACCESS_TOKEN_EXPIRE_HOURS * 3600,
        refresh_token=refresh_token,
        scope=scope,
    )

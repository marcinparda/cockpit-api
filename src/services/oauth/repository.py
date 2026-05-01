from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.oauth.models import OAuthAccessToken, OAuthAuthorizationCode, OAuthClient


async def create_oauth_client(
    db: AsyncSession,
    client_id: str,
    client_name: str,
    redirect_uris_json: str,
    grant_types: str = "authorization_code",
    response_types: str = "code",
    token_endpoint_auth_method: str = "none",
) -> OAuthClient:
    client = OAuthClient()
    client.client_id = client_id
    client.client_name = client_name
    client.redirect_uris = redirect_uris_json
    client.grant_types = grant_types
    client.response_types = response_types
    client.token_endpoint_auth_method = token_endpoint_auth_method
    client.is_active = True
    db.add(client)
    await db.commit()
    await db.refresh(client)
    return client


async def get_oauth_client_by_client_id(db: AsyncSession, client_id: str) -> Optional[OAuthClient]:
    result = await db.execute(
        select(OAuthClient).where(OAuthClient.client_id == client_id)
    )
    return result.scalar_one_or_none()


async def create_authorization_code(
    db: AsyncSession,
    code: str,
    client_id: str,
    user_id: UUID,
    redirect_uri: str,
    scope: Optional[str],
    code_challenge: str,
    code_challenge_method: str,
    expires_at: datetime,
) -> OAuthAuthorizationCode:
    auth_code = OAuthAuthorizationCode()
    auth_code.code = code
    auth_code.client_id = client_id
    auth_code.user_id = user_id
    auth_code.redirect_uri = redirect_uri
    auth_code.scope = scope
    auth_code.code_challenge = code_challenge
    auth_code.code_challenge_method = code_challenge_method
    auth_code.expires_at = expires_at
    auth_code.is_used = False
    db.add(auth_code)
    await db.commit()
    await db.refresh(auth_code)
    return auth_code


async def get_authorization_code(db: AsyncSession, code: str) -> Optional[OAuthAuthorizationCode]:
    result = await db.execute(
        select(OAuthAuthorizationCode).where(OAuthAuthorizationCode.code == code)
    )
    return result.scalar_one_or_none()


async def mark_authorization_code_used(db: AsyncSession, code: str) -> bool:
    result = await db.execute(
        update(OAuthAuthorizationCode)
        .where(OAuthAuthorizationCode.code == code)
        .values(is_used=True)
    )
    await db.commit()
    return result.rowcount > 0


async def create_oauth_access_token(
    db: AsyncSession,
    token: str,
    client_id: str,
    user_id: UUID,
    scope: Optional[str],
    expires_at: datetime,
    refresh_token: Optional[str],
    refresh_token_expires_at: Optional[datetime],
) -> OAuthAccessToken:
    record = OAuthAccessToken()
    record.token = token
    record.client_id = client_id
    record.user_id = user_id
    record.scope = scope
    record.expires_at = expires_at
    record.is_revoked = False
    record.last_used_at = None
    record.refresh_token = refresh_token
    record.refresh_token_expires_at = refresh_token_expires_at
    record.refresh_token_is_revoked = False
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def get_oauth_access_token(db: AsyncSession, token: str) -> Optional[OAuthAccessToken]:
    result = await db.execute(
        select(OAuthAccessToken).where(OAuthAccessToken.token == token)
    )
    return result.scalar_one_or_none()


async def get_oauth_access_token_by_refresh_token(
    db: AsyncSession, refresh_token: str
) -> Optional[OAuthAccessToken]:
    result = await db.execute(
        select(OAuthAccessToken).where(OAuthAccessToken.refresh_token == refresh_token)
    )
    return result.scalar_one_or_none()


async def revoke_oauth_access_token_and_refresh(db: AsyncSession, token: str) -> bool:
    result = await db.execute(
        update(OAuthAccessToken)
        .where(OAuthAccessToken.token == token)
        .values(is_revoked=True, refresh_token_is_revoked=True)
    )
    await db.commit()
    return result.rowcount > 0


async def update_oauth_access_token_last_used(db: AsyncSession, token: str) -> bool:
    result = await db.execute(
        update(OAuthAccessToken)
        .where(OAuthAccessToken.token == token)
        .values(last_used_at=datetime.utcnow())
    )
    await db.commit()
    return result.rowcount > 0

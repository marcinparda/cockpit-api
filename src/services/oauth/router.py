from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_db
from src.services.authentication.sessions.service import authenticate_user
from src.services.oauth import service as oauth_service
from src.services.oauth.schemas import (
    ClientRegistrationRequest,
    ClientRegistrationResponse,
    OAuthServerMetadata,
    ProtectedResourceMetadata,
    TokenResponse,
)

router = APIRouter()


def _login_form_html(
    client_id: str,
    redirect_uri: str,
    response_type: str,
    code_challenge: str,
    code_challenge_method: str,
    scope: str,
    state: str,
    error: str = "",
) -> str:
    error_html = f'<p class="error">{error}</p>' if error else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cockpit — Sign In</title>
    <style>
        *, *::before, *::after {{ box-sizing: border-box; }}
        body {{ font-family: system-ui, -apple-system, sans-serif; display: flex;
               justify-content: center; align-items: center; min-height: 100vh;
               margin: 0; background: #f3f4f6; }}
        .card {{ background: #fff; padding: 2rem; border-radius: 10px;
                 box-shadow: 0 4px 16px rgba(0,0,0,.08); width: 100%; max-width: 360px; }}
        h2 {{ margin: 0 0 1.5rem; font-size: 1.25rem; color: #111; }}
        label {{ display: block; margin-bottom: .25rem; font-size: .875rem;
                 font-weight: 500; color: #374151; }}
        input[type=email], input[type=password] {{
            width: 100%; padding: .5rem .75rem; border: 1px solid #d1d5db;
            border-radius: 6px; font-size: 1rem; margin-bottom: 1rem;
            transition: border-color .15s; outline: none; }}
        input:focus {{ border-color: #6366f1; box-shadow: 0 0 0 2px rgba(99,102,241,.2); }}
        button {{ width: 100%; padding: .625rem; background: #111827; color: #fff;
                  border: none; border-radius: 6px; font-size: 1rem; cursor: pointer;
                  transition: background .15s; }}
        button:hover {{ background: #374151; }}
        .error {{ color: #dc2626; font-size: .875rem; margin-bottom: 1rem;
                  padding: .5rem .75rem; background: #fef2f2; border-radius: 6px; }}
    </style>
</head>
<body>
<div class="card">
    <h2>Sign in to Cockpit</h2>
    {error_html}
    <form method="POST" action="/oauth/authorize">
        <input type="hidden" name="client_id" value="{client_id}">
        <input type="hidden" name="redirect_uri" value="{redirect_uri}">
        <input type="hidden" name="response_type" value="{response_type}">
        <input type="hidden" name="code_challenge" value="{code_challenge}">
        <input type="hidden" name="code_challenge_method" value="{code_challenge_method}">
        <input type="hidden" name="scope" value="{scope}">
        <input type="hidden" name="state" value="{state}">
        <label for="email">Email</label>
        <input type="email" id="email" name="email" required autocomplete="email">
        <label for="password">Password</label>
        <input type="password" id="password" name="password" required autocomplete="current-password">
        <button type="submit">Sign In</button>
    </form>
</div>
</body>
</html>"""


@router.get("/.well-known/oauth-authorization-server", response_model=OAuthServerMetadata)
async def oauth_server_metadata() -> OAuthServerMetadata:
    base = settings.OAUTH_SERVER_URL.rstrip("/")
    return OAuthServerMetadata(
        issuer=base,
        authorization_endpoint=f"{base}/oauth/authorize",
        token_endpoint=f"{base}/oauth/token",
        registration_endpoint=f"{base}/oauth/clients",
    )


@router.get("/.well-known/oauth-protected-resource", response_model=ProtectedResourceMetadata)
async def oauth_protected_resource_metadata() -> ProtectedResourceMetadata:
    base = settings.OAUTH_SERVER_URL.rstrip("/")
    return ProtectedResourceMetadata(
        resource=f"{base}/mcp/mcp",
        authorization_servers=[base],
    )


@router.post("/oauth/clients", response_model=ClientRegistrationResponse, status_code=201)
async def register_client(
    request: ClientRegistrationRequest,
    db: AsyncSession = Depends(get_db),
) -> ClientRegistrationResponse:
    return await oauth_service.register_client(db, request)


@router.get("/oauth/authorize", response_class=HTMLResponse)
async def authorize_get(
    client_id: str,
    redirect_uri: str,
    response_type: str,
    code_challenge: str,
    code_challenge_method: str = "S256",
    scope: Optional[str] = None,
    state: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    try:
        await oauth_service.validate_authorize_request(
            db=db,
            client_id=client_id,
            redirect_uri=redirect_uri,
            response_type=response_type,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
        )
    except HTTPException as exc:
        return HTMLResponse(
            content=f"<h2>OAuth Error</h2><p>{exc.detail}</p>",
            status_code=exc.status_code,
        )

    return HTMLResponse(content=_login_form_html(
        client_id=client_id,
        redirect_uri=redirect_uri,
        response_type=response_type,
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method,
        scope=scope or "",
        state=state or "",
    ))


@router.post("/oauth/authorize")
async def authorize_post(
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    response_type: str = Form(...),
    code_challenge: str = Form(...),
    code_challenge_method: str = Form("S256"),
    scope: Optional[str] = Form(None),
    state: Optional[str] = Form(None),
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        client = await oauth_service.validate_authorize_request(
            db=db,
            client_id=client_id,
            redirect_uri=redirect_uri,
            response_type=response_type,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
        )
    except HTTPException as exc:
        return HTMLResponse(
            content=f"<h2>OAuth Error</h2><p>{exc.detail}</p>",
            status_code=exc.status_code,
        )

    user = await authenticate_user(db, email, password)
    if not user:
        return HTMLResponse(content=_login_form_html(
            client_id=client_id,
            redirect_uri=redirect_uri,
            response_type=response_type,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            scope=scope or "",
            state=state or "",
            error="Invalid email or password.",
        ))

    from uuid import UUID as _UUID
    code = await oauth_service.create_auth_code(
        db=db,
        client=client,
        user_id=_UUID(str(user.id)),
        redirect_uri=redirect_uri,
        scope=scope,
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method,
    )

    callback = f"{redirect_uri}?code={code}"
    if state:
        callback += f"&state={state}"

    return RedirectResponse(url=callback, status_code=302)


@router.post("/oauth/token", response_model=TokenResponse)
async def token_endpoint(
    grant_type: str = Form(...),
    code: Optional[str] = Form(None),
    redirect_uri: Optional[str] = Form(None),
    client_id: Optional[str] = Form(None),
    code_verifier: Optional[str] = Form(None),
    refresh_token: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    if grant_type == "authorization_code":
        if not code or not redirect_uri or not client_id or not code_verifier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="invalid_request: code, redirect_uri, client_id, code_verifier required",
            )
        return await oauth_service.exchange_code_for_token(
            db=db,
            code=code,
            redirect_uri=redirect_uri,
            client_id=client_id,
            code_verifier=code_verifier,
        )

    if grant_type == "refresh_token":
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="invalid_request: refresh_token required",
            )
        return await oauth_service.refresh_oauth_token(db=db, refresh_token=refresh_token)

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="unsupported_grant_type",
    )

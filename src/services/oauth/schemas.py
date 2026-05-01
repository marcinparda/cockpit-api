from typing import List, Optional
from pydantic import BaseModel


class ClientRegistrationRequest(BaseModel):
    client_name: str
    redirect_uris: List[str]
    grant_types: List[str] = ["authorization_code"]
    response_types: List[str] = ["code"]
    token_endpoint_auth_method: str = "none"


class ClientRegistrationResponse(BaseModel):
    client_id: str
    client_name: str
    redirect_uris: List[str]
    grant_types: List[str]
    response_types: List[str]
    token_endpoint_auth_method: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    scope: Optional[str] = None

    model_config = {"populate_by_name": True}


class OAuthServerMetadata(BaseModel):
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    registration_endpoint: str
    response_types_supported: List[str] = ["code"]
    grant_types_supported: List[str] = ["authorization_code", "refresh_token"]
    code_challenge_methods_supported: List[str] = ["S256"]
    token_endpoint_auth_methods_supported: List[str] = ["none"]


class ProtectedResourceMetadata(BaseModel):
    resource: str
    authorization_servers: List[str]
    bearer_methods_supported: List[str] = ["header"]

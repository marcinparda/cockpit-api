from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.core.database import get_db
from src.models.api_key import APIKey
from src.auth.enums.actions import Actions
from src.auth.enums.features import Features
from src.auth.permissions import check_api_key_permissions

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)


async def get_api_key(
    api_key: str = Security(api_key_header),
    db: AsyncSession = Depends(get_db)
) -> APIKey:
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is missing"
        )

    result = await db.execute(select(APIKey).where(APIKey.key == api_key, APIKey.is_active == True))
    api_key_obj = result.scalars().first()

    if not api_key_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key"
        )

    return api_key_obj


async def require_permissions(
    feature: Features,
    action: Actions,
    api_key: APIKey = Depends(get_api_key),
    db: AsyncSession = Depends(get_db)
) -> APIKey:
    """Dependency to check if the API key has the required permission."""
    has_permission = await check_api_key_permissions(db, api_key.id.hex, feature, action)

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"API key does not have permission to {action.value} {feature.value}"
        )

    return api_key

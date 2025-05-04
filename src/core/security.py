from fastapi.security import APIKeyHeader
from fastapi import HTTPException, Depends
from src.core.database import get_db
from src.models.api_key import APIKey
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def validate_api_key(
    api_key: str = Depends(api_key_header),
    db: AsyncSession = Depends(get_db)
):
    if not api_key:
        raise HTTPException(401, "API key required")

    result = await db.execute(
        select(APIKey).where(
            APIKey.key == api_key,
            APIKey.is_active == True
        )
    )
    db_key = result.scalar_one_or_none()
    if not db_key:
        raise HTTPException(403, "Invalid API key")
    return db_key

from fastapi import HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.core.database import get_db
from src.models.api_key import APIKey
from src.permissions import Resources, Actions


class PermissionChecker:
    def __init__(self, resource: Resources, action: Actions):
        self.resource = resource
        self.action = action

    async def __call__(
        self,
        request: Request,
        db: AsyncSession = Depends(get_db)
    ) -> None:
        api_key = request.headers.get("X-API-KEY")
        if not api_key:
            raise HTTPException(status_code=401, detail="API key required")

        # Query for API key where key field matches the provided api_key
        query = select(APIKey).where(APIKey.key == api_key)
        result = await db.execute(query)
        db_key = result.scalar_one_or_none()

        if not db_key:
            raise HTTPException(status_code=403, detail="Invalid API key")

        allowed_actions = db_key.permissions.get(self.resource.value, [])
        if self.action.value not in allowed_actions:
            raise HTTPException(
                status_code=403,
                detail=f"Missing {self.action.value} permission for {self.resource.value}"
            )

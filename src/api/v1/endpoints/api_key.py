import secrets
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.api_key import APIKey
from src.core.database import get_db
from src.schemas.api_key import APIKeyCreate
from fastapi import status
from src.permissions import Resources, Actions
from src.api.v1.deps import PermissionChecker

router = APIRouter()


@router.post(
    "/",
    response_model=APIKeyCreate,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new API key",
    responses={
        201: {"description": "API key created successfully"},
        403: {"description": "Permission denied"},
        409: {"description": "API key conflict"}
    }
)
async def create_api_key(
    key_data: APIKeyCreate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(PermissionChecker(Resources.API_KEYS, Actions.CREATE)),
):
    """
    Create a new API key with specified permissions.

    - Generates a cryptographically secure random key
    - Validates permission structure
    - Stores key in database with hashed value
    """
    # Generate secure random key (64 characters)
    raw_key = secrets.token_hex(32)

    try:
        # Validate permissions structure
        APIKey.validate_permissions(key_data.permissions)

        # Create database entry
        db_key = APIKey(
            key=raw_key,
            permissions=key_data.permissions
        )

        db.add(db_key)
        await db.commit()
        await db.refresh(db_key)

        return {
            "key": raw_key,  # Return raw key only once!
            "permissions": db_key.permissions
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        if "unique constraint" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="API key collision, please try again"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating API key"
        )

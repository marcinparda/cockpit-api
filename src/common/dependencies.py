from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.core.database import get_db
from .exceptions import ValidationError
from typing import AsyncGenerator


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency."""
    async for session in get_db():
        yield session


def validate_pagination(
    page: Optional[int] = None,
    limit: Optional[int] = None,
    max_limit: int = 100
) -> tuple[int, int]:
    """Validate and normalize pagination parameters."""
    if page is not None and page < 1:
        raise ValidationError("Page must be greater than 0")

    if limit is not None and (limit < 1 or limit > max_limit):
        raise ValidationError(f"Limit must be between 1 and {max_limit}")

    normalized_page = page or 1
    normalized_limit = limit or 20

    return normalized_page, normalized_limit


def validate_uuid_param(param_value: Optional[str], param_name: str = "id") -> str:
    """Validate that a parameter is a valid UUID."""
    if not param_value:
        raise ValidationError(f"{param_name} is required")

    try:
        # This will raise ValueError if not a valid UUID
        import uuid
        uuid.UUID(param_value)
        return param_value
    except ValueError:
        raise ValidationError(f"Invalid {param_name} format")

from datetime import datetime
from typing import Optional
import uuid


def generate_uuid() -> str:
    """Generate a new UUID string."""
    return str(uuid.uuid4())


def format_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Format datetime to ISO string."""
    if dt is None:
        return None
    return dt.isoformat()


def parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """Parse ISO datetime string to datetime object."""
    if not dt_str:
        return None
    return datetime.fromisoformat(dt_str)


def normalize_email(email: str) -> str:
    """Normalize email address to lowercase."""
    return email.lower().strip()


def safe_str_compare(a: Optional[str], b: Optional[str]) -> bool:
    """Safely compare two strings, handling None values."""
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    return a == b
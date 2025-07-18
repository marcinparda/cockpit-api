"""JWT blacklist functionality for token invalidation."""

import time
from typing import Set, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio


class JWTBlacklistEntry:
    """Single blacklist entry for a JWT token."""

    def __init__(self, token_id: str, expires_at: float):
        self.token_id = token_id
        self.expires_at = expires_at

    def is_expired(self) -> bool:
        """Check if this blacklist entry has expired."""
        return time.time() > self.expires_at


class JWTBlacklist:
    """JWT token blacklist manager."""

    def __init__(self):
        self.blacklisted_tokens: Set[str] = set()
        self.token_expiry: dict[str, float] = {}
        self.cleanup_interval = 3600  # 1 hour
        self.last_cleanup = time.time()

    def add_token(self, token_id: str, expires_at: Optional[float] = None) -> None:
        """Add a token to the blacklist."""
        if expires_at is None:
            # Default expiry: 24 hours from now
            expires_at = time.time() + (24 * 3600)

        self.blacklisted_tokens.add(token_id)
        self.token_expiry[token_id] = expires_at

        # Periodic cleanup
        if time.time() - self.last_cleanup > self.cleanup_interval:
            self._cleanup_expired()
            self.last_cleanup = time.time()

    def is_blacklisted(self, token_id: str) -> bool:
        """Check if a token is blacklisted."""
        if token_id not in self.blacklisted_tokens:
            return False

        # Check if the blacklist entry has expired
        expires_at = self.token_expiry.get(token_id)
        if expires_at and time.time() > expires_at:
            # Remove expired entry
            self.blacklisted_tokens.discard(token_id)
            self.token_expiry.pop(token_id, None)
            return False

        return True

    def remove_token(self, token_id: str) -> None:
        """Remove a token from the blacklist."""
        self.blacklisted_tokens.discard(token_id)
        self.token_expiry.pop(token_id, None)

    def _cleanup_expired(self) -> None:
        """Clean up expired blacklist entries."""
        current_time = time.time()
        expired_tokens = []

        for token_id, expires_at in self.token_expiry.items():
            if current_time > expires_at:
                expired_tokens.append(token_id)

        for token_id in expired_tokens:
            self.blacklisted_tokens.discard(token_id)
            self.token_expiry.pop(token_id, None)

    def get_stats(self) -> dict:
        """Get blacklist statistics."""
        return {
            "total_blacklisted": len(self.blacklisted_tokens),
            "last_cleanup": self.last_cleanup
        }


# Global blacklist instance
jwt_blacklist = JWTBlacklist()


def blacklist_token(token_id: str, expires_at: Optional[float] = None) -> None:
    """Add a token to the global blacklist."""
    jwt_blacklist.add_token(token_id, expires_at)


def is_token_blacklisted(token_id: str) -> bool:
    """Check if a token is in the global blacklist."""
    return jwt_blacklist.is_blacklisted(token_id)


def remove_token_from_blacklist(token_id: str) -> None:
    """Remove a token from the global blacklist."""
    jwt_blacklist.remove_token(token_id)


def get_blacklist_stats() -> dict:
    """Get global blacklist statistics."""
    return jwt_blacklist.get_stats()

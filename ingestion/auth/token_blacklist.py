"""Token revocation/blacklist management for JWT tokens."""
import os
from datetime import datetime, timedelta, timezone
from typing import Set

# In-memory token blacklist (for production, use Redis or database)
# This should be replaced with a persistent storage solution in production
_token_blacklist: Set[str] = set()
_blacklist_cleanup_time = datetime.now(timezone.utc)


def revoke_token(token: str) -> None:
    """
    Add a token to the blacklist (revoke it).
    
    In production, this should use Redis or a database for persistence
    across server restarts and load-balanced deployments.
    """
    _token_blacklist.add(token)
    _cleanup_expired_tokens()


def is_token_revoked(token: str) -> bool:
    """Check if a token has been revoked."""
    return token in _token_blacklist


def _cleanup_expired_tokens():
    """Remove expired tokens from blacklist periodically."""
    global _blacklist_cleanup_time
    now = datetime.now(timezone.utc)
    
    # Cleanup every hour
    if (now - _blacklist_cleanup_time).total_seconds() > 3600:
        _token_blacklist.clear()
        _blacklist_cleanup_time = now


def clear_blacklist() -> None:
    """Clear all revoked tokens (use with caution)."""
    _token_blacklist.clear()

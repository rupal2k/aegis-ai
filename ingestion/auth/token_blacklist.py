"""Token revocation/blacklist management for JWT tokens."""
from datetime import datetime, timezone
from typing import Dict

# In-memory token blacklist: token → UTC revocation timestamp
# (production: replace with Redis or DB for persistence across restarts)
_token_blacklist: Dict[str, datetime] = {}

# JWT tokens expire after 8 hours — safe to prune revocations older than that.
_TOKEN_TTL_SECONDS = 8 * 3600


def revoke_token(token: str) -> None:
    _token_blacklist[token] = datetime.now(timezone.utc)
    _cleanup_expired_tokens()


def is_token_revoked(token: str) -> bool:
    return token in _token_blacklist


def _cleanup_expired_tokens() -> None:
    """Remove only entries whose underlying JWT has already expired."""
    now = datetime.now(timezone.utc)
    expired = [
        tok for tok, revoked_at in _token_blacklist.items()
        if (now - revoked_at).total_seconds() > _TOKEN_TTL_SECONDS
    ]
    for tok in expired:
        del _token_blacklist[tok]


def clear_blacklist() -> None:
    """Clear all revoked tokens (use with caution — testing only)."""
    _token_blacklist.clear()

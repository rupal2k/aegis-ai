"""Shared rate limiting primitives for the FastAPI app."""
from starlette.requests import Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded


def _get_real_ip(request: Request) -> str:
    # Render routes through Cloudflare; CF-Connecting-IP carries the real client IP.
    # X-Forwarded-For is a fallback (leftmost entry = original client).
    cf_ip = request.headers.get("CF-Connecting-IP")
    if cf_ip:
        return cf_ip
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host


limiter = Limiter(key_func=_get_real_ip)

__all__ = ["limiter", "RateLimitExceeded", "_rate_limit_exceeded_handler"]

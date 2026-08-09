"""Simple in-memory rate limiter for auth endpoints."""

import time
from collections import defaultdict
from threading import Lock

from fastapi import HTTPException, Request, status

_lock = Lock()
_attempts: dict[str, list[float]] = defaultdict(list)


def _client_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def check_rate_limit(request: Request, *, max_attempts: int, window_seconds: int, scope: str) -> None:
    key = f"{scope}:{_client_key(request)}"
    now = time.monotonic()
    cutoff = now - window_seconds

    with _lock:
        _attempts[key] = [t for t in _attempts[key] if t > cutoff]
        if len(_attempts[key]) >= max_attempts:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many attempts. Please try again later.",
            )
        _attempts[key].append(now)


def reset_rate_limit(request: Request, scope: str) -> None:
    """Clear rate-limit counter after successful auth."""
    key = f"{scope}:{_client_key(request)}"
    with _lock:
        _attempts.pop(key, None)

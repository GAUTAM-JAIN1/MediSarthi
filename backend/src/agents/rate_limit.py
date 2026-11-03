import time
import threading
from typing import Dict, Tuple

from agents.config import trust_proxy_headers


def get_client_ip(req) -> str:
    """
    Extracts the client IP from the request.
    If TRUST_PROXY_HEADERS is explicitly "true", reads X-Forwarded-For.
    The rightmost entry is used because it is appended by the nearest trusted
    reverse proxy; the leftmost entry can be spoofed by a client setting their own header.
    Otherwise falls back to req.client.host if available, else "unknown".
    """
    if trust_proxy_headers():
        headers = getattr(req, "headers", None)
        if headers is not None:
            # Handles starlette Headers or standard dict
            forwarded = headers.get("x-forwarded-for") or headers.get("X-Forwarded-For")
            if forwarded:
                parts = [p.strip() for p in forwarded.split(",") if p.strip()]
                if parts:
                    return parts[-1]
    if hasattr(req, "client") and req.client and hasattr(req.client, "host") and req.client.host:
        return req.client.host
    return "unknown"


class RateLimiter:
    """
    In-memory fixed-window rate limiter guarded by a lock with periodic pruning.
    """

    def __init__(self, max_requests: int, window_seconds: int, prune_interval_seconds: int = None):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.prune_interval_seconds = (
            prune_interval_seconds if prune_interval_seconds is not None else window_seconds
        )
        self.lock = threading.RLock()
        self.last_prune = time.time()
        # key -> (window_start_timestamp, request_count)
        self.requests: Dict[str, Tuple[float, int]] = {}

    def prune_expired(self) -> int:
        """
        Removes keys whose (now - start_time) >= window_seconds.
        Returns the number of keys pruned.
        """
        with self.lock:
            now = time.time()
            expired = [
                k for k, (start, _) in self.requests.items()
                if (now - start) >= self.window_seconds
            ]
            for k in expired:
                del self.requests[k]
            return len(expired)

    def check(self, key: str) -> bool:
        """
        Checks whether a request with `key` is allowed under the rate limit.
        Returns True if allowed, False if the limit is exceeded.
        """
        now = time.time()
        with self.lock:
            if (now - self.last_prune) >= self.prune_interval_seconds:
                self.prune_expired()
                self.last_prune = now

            if key not in self.requests:
                self.requests[key] = (now, 1)
                return True

            start_time, count = self.requests[key]
            if now - start_time >= self.window_seconds:
                # Window expired, start a new window
                self.requests[key] = (now, 1)
                return True

            if count < self.max_requests:
                self.requests[key] = (start_time, count + 1)
                return True

            # Limit exceeded for this window
            return False

    def reset(self) -> None:
        """Clears all stored rate limit history. Used in test fixtures."""
        with self.lock:
            self.requests.clear()
            self.last_prune = time.time()


# Module-level limiters per requirement 2d:
LOGIN_LIMITER = RateLimiter(max_requests=10, window_seconds=60)
SIGNUP_LIMITER = RateLimiter(max_requests=10, window_seconds=60)
COMPARE_LIMITER = RateLimiter(max_requests=5, window_seconds=60)

"""
Simple in-memory rate limiter for registration attempts.
"""
import time
from collections import deque
from threading import Lock

from ..config import settings


class RateLimiter:
    """Thread-safe rate limiter using timestamp queues."""

    def __init__(self, max_attempts: int, window_seconds: int):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.storage: dict[str, deque[float]] = {}
        self.lock = Lock()

    def allow_request(self, key: str) -> tuple[bool, int]:
        """
        Determine if a request is allowed for the given key.

        Args:
            key: Unique identifier (e.g., IP address)

        Returns:
            (True, 0) if allowed, otherwise (False, seconds until reset)
        """
        now = time.monotonic()
        with self.lock:
            queue = self.storage.setdefault(key, deque())
            while queue and queue[0] <= now - self.window_seconds:
                queue.popleft()
            if len(queue) >= self.max_attempts:
                retry_after = int(self.window_seconds - (now - queue[0])) or 1
                return False, retry_after
            queue.append(now)
            return True, 0


registration_rate_limiter = RateLimiter(
    max_attempts=settings.REGISTRATION_MAX_ATTEMPTS_PER_HOUR,
    window_seconds=settings.REGISTRATION_WINDOW_SECONDS,
)

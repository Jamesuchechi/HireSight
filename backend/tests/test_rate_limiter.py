import pytest

from app.utils.ratelimit import RateLimiter


def test_rate_limiter_blocks_after_limit():
    limiter = RateLimiter(max_attempts=2, window_seconds=60)
    allowed, retry = limiter.allow_request("test-ip")
    assert allowed
    allowed, retry = limiter.allow_request("test-ip")
    assert allowed
    blocked, retry = limiter.allow_request("test-ip")
    assert not blocked
    assert retry > 0


def test_rate_limiter_resets_after_window(monkeypatch):
    limiter = RateLimiter(max_attempts=1, window_seconds=1)
    allowed, _ = limiter.allow_request("key")
    assert allowed

    # Advance time beyond window
    monkeypatch.setattr('app.utils.ratelimit.time.monotonic', lambda: 100)
    allowed, _ = limiter.allow_request("key")
    assert allowed

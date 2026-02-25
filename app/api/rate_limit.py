"""In-memory per-user rate limiter (single-instance friendly)."""

from __future__ import annotations

import time
from collections import defaultdict

from fastapi import HTTPException


class RateLimiter:
    def __init__(self):
        self._windows: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str, max_calls: int, window_seconds: int):
        now = time.time()
        entries = self._windows[key]
        # Prune expired
        self._windows[key] = [t for t in entries if now - t < window_seconds]
        if len(self._windows[key]) >= max_calls:
            raise HTTPException(status_code=429, detail="Rate limit exceeded, please try later")
        self._windows[key].append(now)


_limiter = RateLimiter()

"""Redis-backed sliding-window rate limiter.

Usage:
    from stackhealth.ratelimit import allow
    if not allow(f"ip:{ip}", limit=5, window_seconds=3600):
        raise HTTPException(429, "rate_limited")
"""

import time
from functools import lru_cache

from redis import Redis

from stackhealth.config import settings


@lru_cache
def _redis() -> Redis:
    return Redis.from_url(settings.redis_url, decode_responses=True)


def allow(key: str, *, limit: int, window_seconds: int) -> bool:
    """Sliding-window via Redis sorted set.

    Returns True if the request is allowed; False if the limit is hit.
    """
    r = _redis()
    now = time.time()
    cutoff = now - window_seconds
    redis_key = f"rl:{key}"

    pipe = r.pipeline()
    pipe.zremrangebyscore(redis_key, 0, cutoff)
    pipe.zcard(redis_key)
    pipe.zadd(redis_key, {str(now): now})
    pipe.expire(redis_key, window_seconds + 60)
    _, count, _, _ = pipe.execute()

    return int(count) < limit

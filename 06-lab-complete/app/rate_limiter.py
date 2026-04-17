import time
import asyncio
from collections import defaultdict, deque
from fastapi import HTTPException
from app.config import settings

# In-memory storage fallback
_rate_windows: dict[str, deque] = defaultdict(deque)
_rate_locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

async def check_rate_limit(user_id: str, get_redis_func=None) -> None:
    """Sliding window rate limiter."""
    r = get_redis_func() if get_redis_func else None
    now = time.time()
    limit = settings.rate_limit_per_minute

    if r:
        key = f"rate:{user_id}"
        pipe = r.pipeline()
        pipe.zremrangebyscore(key, 0, now - 60)
        pipe.zcard(key)
        pipe.expire(key, 120)
        _, count, *_ = pipe.execute()
        if count >= limit:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {limit} req/min",
                headers={"Retry-After": "60"},
            )
        r.zadd(key, {str(now): now})
    else:
        async with _rate_locks[user_id]:
            window = _rate_windows[user_id]
            while window and window[0] < now - 60:
                window.popleft()
            if len(window) >= limit:
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded: {limit} req/min",
                    headers={"Retry-After": "60"},
                )
            window.append(now)

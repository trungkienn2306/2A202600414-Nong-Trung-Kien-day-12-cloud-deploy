import asyncio
from datetime import datetime
from collections import defaultdict
from fastapi import HTTPException
from app.config import settings

_monthly_cost: dict[str, float] = defaultdict(float)
_cost_locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    return (input_tokens / 1000) * 0.00015 + (output_tokens / 1000) * 0.0006

async def check_and_record_cost(user_id: str, cost: float, get_redis_func=None) -> None:
    """Check budget and record cost."""
    r = get_redis_func() if get_redis_func else None
    budget = settings.monthly_budget_usd
    month_key = datetime.now().strftime("%Y-%m")

    if r:
        redis_key = f"cost:{user_id}:{month_key}"
        lua_script = """
            local current = tonumber(redis.call('GET', KEYS[1])) or 0
            if current + tonumber(ARGV[1]) > tonumber(ARGV[2]) then
                return 0
            end
            redis.call('INCRBYFLOAT', KEYS[1], ARGV[1])
            redis.call('EXPIRE', KEYS[1], ARGV[3])
            return 1
        """
        result = r.eval(lua_script, 1, redis_key, cost, budget, 32 * 24 * 3600)
        if not result:
            raise HTTPException(
                status_code=402,
                detail=f"Monthly budget ${budget} exceeded. Resets next month.",
            )
    else:
        async with _cost_locks[user_id]:
            current = _monthly_cost[user_id]
            if current + cost > budget:
                raise HTTPException(
                    status_code=402,
                    detail=f"Monthly budget ${budget} exceeded. Resets next month.",
                )
            _monthly_cost[user_id] += cost

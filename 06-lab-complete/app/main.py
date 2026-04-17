"""
Production AI Agent — Kết hợp tất cả Day 12 concepts

Checklist:
  ✅ Config từ environment (12-factor)
  ✅ Structured JSON logging
  ✅ API Key authentication
  ✅ Rate limiting (per-user, sliding window)
  ✅ Cost guard (per-user, monthly budget)
  ✅ Input validation (Pydantic)
  ✅ Health check + Readiness probe
  ✅ Graceful shutdown (SIGTERM)
  ✅ Security headers
  ✅ CORS
  ✅ Error handling
  ✅ Conversation history (Redis stateless)
  ✅ Streaming responses (SSE bonus)
  ✅ Metrics endpoint
"""
import os
import time
import signal
import logging
import json
import asyncio
from datetime import datetime, timezone
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Security, Depends, Request, Response
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from app.config import settings

# Mock LLM (thay bằng OpenAI/Anthropic khi có API key)
from utils.mock_llm import ask as llm_ask, ask_stream as llm_stream

# ─────────────────────────────────────────────────────────
# Logging — JSON structured
# ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='{"ts":"%(asctime)s","lvl":"%(levelname)s","msg":"%(message)s"}',
)
logger = logging.getLogger(__name__)

START_TIME = time.time()
_is_ready = False
_request_count = 0
_error_count = 0

# ─────────────────────────────────────────────────────────
# Redis client (optional — fallback to in-memory)
# ─────────────────────────────────────────────────────────
_redis_client = None

def get_redis():
    """Get Redis client, returns None if not configured."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    if not settings.redis_url:
        return None
    try:
        import redis
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        _redis_client.ping()
        logger.info(json.dumps({"event": "redis_connected", "url": settings.redis_url}))
        return _redis_client
    except Exception as e:
        logger.warning(json.dumps({"event": "redis_unavailable", "error": str(e)}))
        return None

# ─────────────────────────────────────────────────────────
# In-memory Rate Limiter (fallback khi không có Redis)
# ─────────────────────────────────────────────────────────
_rate_windows: dict[str, deque] = defaultdict(deque)
_rate_locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)


async def check_rate_limit(user_id: str) -> None:
    """Sliding window rate limiter — per user. Thread-safe."""
    r = get_redis()
    now = time.time()
    limit = settings.rate_limit_per_minute

    if r:
        # Redis-based sliding window (atomic pipeline — production-grade)
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
        # Only add after confirming not exceeded
        r.zadd(key, {str(now): now})
    else:
        # In-memory fallback — use per-user lock for thread safety
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


# ─────────────────────────────────────────────────────────
# Cost Guard — per-user, monthly budget
# ─────────────────────────────────────────────────────────
_monthly_cost: dict[str, float] = defaultdict(float)
_cost_locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)


def _estimate_cost(input_tokens: int, output_tokens: int) -> float:
    return (input_tokens / 1000) * 0.00015 + (output_tokens / 1000) * 0.0006


async def check_and_record_cost(user_id: str, cost: float) -> None:
    """Check budget and record cost atomically. Raises 402 when monthly budget exceeded."""
    r = get_redis()
    budget = settings.monthly_budget_usd
    month_key = datetime.now().strftime("%Y-%m")

    if r:
        redis_key = f"cost:{user_id}:{month_key}"
        # Use Lua script for atomic check-and-increment
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
        # In-memory fallback — use lock for thread safety
        async with _cost_locks[user_id]:
            current = _monthly_cost[user_id]
            if current + cost > budget:
                raise HTTPException(
                    status_code=402,
                    detail=f"Monthly budget ${budget} exceeded. Resets next month.",
                )
            _monthly_cost[user_id] += cost


# ─────────────────────────────────────────────────────────
# Conversation History — Redis stateless design
# ─────────────────────────────────────────────────────────
_in_memory_history: dict[str, list] = defaultdict(list)
MAX_HISTORY = 10  # Giữ tối đa 10 turns


def get_history(user_id: str) -> list[dict]:
    """Lấy lịch sử hội thoại từ Redis (hoặc in-memory fallback)."""
    r = get_redis()
    if r:
        raw = r.lrange(f"history:{user_id}", 0, MAX_HISTORY * 2 - 1)
        return [json.loads(item) for item in raw]
    return list(_in_memory_history[user_id][-MAX_HISTORY:])


def save_history(user_id: str, role: str, content: str) -> None:
    """Lưu một turn vào lịch sử hội thoại."""
    r = get_redis()
    entry = json.dumps({"role": role, "content": content})
    if r:
        key = f"history:{user_id}"
        r.rpush(key, entry)
        r.ltrim(key, -MAX_HISTORY * 2, -1)  # giữ MAX_HISTORY turns (user+assistant)
        r.expire(key, 7 * 24 * 3600)  # TTL 7 ngày
    else:
        _in_memory_history[user_id].append({"role": role, "content": content})
        if len(_in_memory_history[user_id]) > MAX_HISTORY * 2:
            _in_memory_history[user_id] = _in_memory_history[user_id][-MAX_HISTORY * 2:]


def clear_history(user_id: str) -> None:
    """Xóa lịch sử hội thoại của user."""
    r = get_redis()
    if r:
        r.delete(f"history:{user_id}")
    else:
        _in_memory_history[user_id] = []


# ─────────────────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────────────────
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    if not api_key or api_key != settings.agent_api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key. Include header: X-API-Key: <key>",
        )
    return api_key


# ─────────────────────────────────────────────────────────
# Lifespan
# ─────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _is_ready
    logger.info(json.dumps({
        "event": "startup",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }))
    # Khởi tạo Redis connection
    get_redis()
    time.sleep(0.1)  # simulate init
    _is_ready = True
    logger.info(json.dumps({"event": "ready"}))

    yield

    _is_ready = False
    logger.info(json.dumps({"event": "shutdown"}))


# ─────────────────────────────────────────────────────────
# App
# ─────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    global _request_count, _error_count
    start = time.time()
    _request_count += 1
    try:
        response: Response = await call_next(request)
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        if "server" in response.headers:
            del response.headers["server"]
        duration = round((time.time() - start) * 1000, 1)
        logger.info(json.dumps({
            "event": "request",
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "ms": duration,
        }))
        return response
    except Exception as e:
        _error_count += 1
        raise


# ─────────────────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────────────────
class AskRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=100,
                         description="Unique user identifier")
    question: str = Field(..., min_length=1, max_length=2000,
                          description="Your question for the agent")


class AskResponse(BaseModel):
    user_id: str
    question: str
    answer: str
    model: str
    history_length: int
    timestamp: str


class HistoryResponse(BaseModel):
    user_id: str
    history: list[dict]
    count: int


# ─────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────

@app.get("/", tags=["Info"])
def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "endpoints": {
            "ask": "POST /ask (requires X-API-Key)",
            "ask_stream": "POST /ask/stream (streaming SSE)",
            "history": "GET /history/{user_id}",
            "clear_history": "DELETE /history/{user_id}",
            "health": "GET /health",
            "ready": "GET /ready",
            "metrics": "GET /metrics (requires X-API-Key)",
        },
    }


@app.post("/ask", response_model=AskResponse, tags=["Agent"])
async def ask_agent(
    body: AskRequest,
    request: Request,
    _key: str = Depends(verify_api_key),
):
    """
    Send a question to the AI agent. Conversation history is maintained per user_id.

    **Authentication:** Include header `X-API-Key: <your-key>`
    """
    # Rate limit per user
    await check_rate_limit(body.user_id)

    logger.info(json.dumps({
        "event": "agent_call",
        "user_id": body.user_id,
        "q_len": len(body.question),
        "client": str(request.client.host) if request.client else "unknown",
    }))

    # Save user message to history
    save_history(body.user_id, "user", body.question)

    # Get full history for context
    history = get_history(body.user_id)

    # Build context-aware question
    context_question = body.question
    if len(history) > 1:
        ctx_lines = []
        for turn in history[:-1][-6:]:  # last 3 exchanges
            ctx_lines.append(f"{turn['role'].upper()}: {turn['content']}")
        context_question = "\n".join(ctx_lines) + f"\nUSER: {body.question}"

    answer = llm_ask(context_question)

    # Save assistant response
    save_history(body.user_id, "assistant", answer)

    # Record cost AFTER successful LLM call (no double-charge on error)
    input_tokens = len(body.question.split()) * 2
    output_tokens = len(answer.split()) * 2
    total_cost = _estimate_cost(input_tokens, output_tokens)
    await check_and_record_cost(body.user_id, total_cost)

    current_history = get_history(body.user_id)

    return AskResponse(
        user_id=body.user_id,
        question=body.question,
        answer=answer,
        model=settings.llm_model,
        history_length=len(current_history),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.post("/ask/stream", tags=["Agent"])
async def ask_agent_stream(
    body: AskRequest,
    request: Request,
    _key: str = Depends(verify_api_key),
):
    """
    Streaming response using Server-Sent Events (SSE).

    **BONUS FEATURE:** Returns response token-by-token as SSE stream.

    **Authentication:** Include header `X-API-Key: <your-key>`

    **Usage:**
    ```bash
    curl -N -H "X-API-Key: <key>" -X POST http://localhost:8000/ask/stream \\
      -H "Content-Type: application/json" \\
      -d '{"user_id":"alice","question":"Tell me about Docker"}'
    ```
    """
    # Rate limit per user
    await check_rate_limit(body.user_id)

    logger.info(json.dumps({
        "event": "agent_stream_call",
        "user_id": body.user_id,
        "q_len": len(body.question),
    }))

    # Save user message
    save_history(body.user_id, "user", body.question)

    async def event_generator() -> AsyncGenerator[str, None]:
        full_answer = []
        try:
            for token in llm_stream(body.question):
                full_answer.append(token)
                data = json.dumps({"token": token, "done": False})
                yield f"data: {data}\n\n"

            answer = "".join(full_answer)
            save_history(body.user_id, "assistant", answer)

            # Record cost after successful completion
            input_tokens = len(body.question.split()) * 2
            output_tokens = len(answer.split()) * 2
            total_cost = _estimate_cost(input_tokens, output_tokens)
            await check_and_record_cost(body.user_id, total_cost)

            done_data = json.dumps({
                "token": "",
                "done": True,
                "answer": answer,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            yield f"data: {done_data}\n\n"
        except HTTPException as e:
            error_data = json.dumps({"error": e.detail, "done": True})
            yield f"data: {error_data}\n\n"
        except Exception as e:
            error_data = json.dumps({"error": "Internal server error", "done": True})
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/history/{user_id}", response_model=HistoryResponse, tags=["Agent"])
def get_conversation_history(
    user_id: str,
    _key: str = Depends(verify_api_key),
):
    """
    Get conversation history for a specific user.

    Note: In this lab setup, user_id is caller-supplied.
    In production, derive user_id from the authenticated session/JWT.
    """
    history = get_history(user_id)
    return HistoryResponse(
        user_id=user_id,
        history=history,
        count=len(history),
    )


@app.delete("/history/{user_id}", tags=["Agent"])
def delete_conversation_history(
    user_id: str,
    _key: str = Depends(verify_api_key),
):
    """
    Clear conversation history for a specific user.

    Note: In this lab setup, user_id is caller-supplied.
    In production, derive user_id from the authenticated session/JWT.
    """
    clear_history(user_id)
    logger.info(json.dumps({"event": "history_cleared", "user_id": user_id}))
    return {"message": f"History cleared for user: {user_id}"}


@app.get("/health", tags=["Operations"])
def health():
    """Liveness probe. Platform restarts container if this fails."""
    r = get_redis()
    redis_status = "connected" if r else "unavailable"
    return {
        "status": "ok",
        "version": settings.app_version,
        "environment": settings.environment,
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "total_requests": _request_count,
        "checks": {
            "llm": "mock" if not settings.openai_api_key else "openai",
            "redis": redis_status,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/ready", tags=["Operations"])
def ready():
    """Readiness probe. Load balancer stops routing here if not ready."""
    if not _is_ready:
        raise HTTPException(503, "Not ready")
    return {"ready": True, "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/metrics", tags=["Operations"])
def metrics(_key: str = Depends(verify_api_key)):
    """Basic metrics (protected)."""
    r = get_redis()
    redis_info = {}
    if r:
        try:
            info = r.info("memory")
            redis_info = {
                "used_memory_human": info.get("used_memory_human"),
                "connected_clients": r.info("clients").get("connected_clients"),
            }
        except Exception:
            pass

    return {
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "total_requests": _request_count,
        "error_count": _error_count,
        "monthly_budget_usd": settings.monthly_budget_usd,
        "rate_limit_per_minute": settings.rate_limit_per_minute,
        "redis": redis_info,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ─────────────────────────────────────────────────────────
# Graceful Shutdown
# ─────────────────────────────────────────────────────────
def _handle_signal(signum, _frame):
    logger.info(json.dumps({
        "event": "graceful_shutdown",
        "signum": signum,
        "message": "SIGTERM received, finishing requests and shutting down...",
    }))
    # uvicorn handles graceful shutdown via timeout_graceful_shutdown
    # This handler ensures we log it properly


signal.signal(signal.SIGTERM, _handle_signal)


if __name__ == "__main__":
    logger.info(f"Starting {settings.app_name} on {settings.host}:{settings.port}")
    logger.info(f"API Key: {settings.agent_api_key[:4]}****")
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        timeout_graceful_shutdown=30,
    )

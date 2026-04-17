# Day 12 Lab — Mission Answers

> **Student:** Nông Trung Kiên  
> **Student ID:** 2A202600414  
> **Date:** 17/4/2026  
> **Course:** AICB-P1 · VinUniversity 2026

---

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found in `01-localhost-vs-production/develop/app.py`

1. **API key hardcoded trong code** — `OPENAI_API_KEY = "sk-hardcoded-fake-key-never-do-this"` và `DATABASE_URL = "postgresql://admin:password123@localhost:5432/mydb"`. Khi push lên GitHub, mọi người đều thấy credentials.

2. **Secret bị log ra** — `print(f"[DEBUG] Using key: {OPENAI_API_KEY}")` — in API key ra stdout. Log aggregator sẽ ghi lại, bất kỳ ai xem log đều thấy key.

3. **`print()` thay vì proper logging** — Dùng `print()` để debug thay vì module `logging`. Không có log level, không có structured format, không thể filter hay search.

4. **Không có health check endpoint** — Platform (Railway, Render, Kubernetes) cần endpoint `/health` để biết container có sống không. Nếu thiếu, platform không thể tự động restart khi crash.

5. **Port cứng `localhost:8000`** — `host="localhost"` chỉ bind trên loopback, container bên ngoài không truy cập được. PORT phải đọc từ env var vì cloud platform inject PORT tự động.

6. **`reload=True` trong production** — Auto-reload dành cho development, không phải production. Tốn CPU, có thể gây memory leak.

7. **Không có graceful shutdown** — Khi SIGTERM được gửi, process tắt ngay lập tức, drop tất cả request đang xử lý.

8. **Không có input validation** — `/ask?question=...` query param, không validate length hay content.

---

### Exercise 1.2: Chạy basic version

```bash
cd 01-localhost-vs-production/develop
pip install -r requirements.txt
python app.py
```

**Kết quả:** Server chạy được — nhưng KHÔNG production-ready vì tất cả các vấn đề nêu trên.

---

### Exercise 1.3: Comparison table

| Feature | Develop (Basic) | Production (Advanced) | Tại sao quan trọng? |
|---------|-----------------|----------------------|---------------------|
| **Config** | Hardcode trong code (`OPENAI_API_KEY = "sk-..."`) | Đọc từ env vars qua `os.getenv()` / pydantic Settings | Bảo mật: không commit secrets vào git; Linh hoạt: thay đổi config không cần redeploy |
| **Health check** | ❌ Không có | ✅ `GET /health` → 200 OK | Platform biết khi nào restart; Load balancer biết khi nào route traffic |
| **Readiness** | ❌ Không có | ✅ `GET /ready` → 200/503 | Phân biệt "container sống" vs "sẵn sàng nhận traffic" — quan trọng khi startup chậm |
| **Logging** | `print()` — unstructured | JSON structured logging với level, timestamp, event | Dễ search/filter trong log aggregator; Có thể alert trên specific events |
| **Shutdown** | Đột ngột — drop requests | Graceful shutdown (SIGTERM handler + 30s timeout) | Không mất dữ liệu đang xử lý; Clean disconnect từ database |
| **Auth** | ❌ Không có | ✅ API Key (`X-API-Key` header) | Kiểm soát ai được gọi API; Tính phí theo user |
| **Rate Limiting** | ❌ Không có | ✅ 10 req/min per user | Ngăn abuse; Bảo vệ chi phí LLM |
| **Error handling** | None — crash toàn bộ | Try/catch + HTTP error codes | User thấy lỗi rõ ràng, server không crash |
| **Secrets in logs** | `print(f"Using key: {KEY}")` ❌ | API key chỉ log 4 ký tự đầu: `key[:4]****` | Ngăn credentials bị lộ qua logs |
| **Port** | `host="localhost"`, port cứng 8000 | `HOST=0.0.0.0`, `PORT=int(os.getenv("PORT", "8000"))` | Cloud platform inject PORT; 0.0.0.0 nhận traffic từ mọi network interface |

---

## Part 2: Docker Containerization

### Exercise 2.1: Dockerfile questions (`02-docker/develop/Dockerfile`)

1. **Base image là gì?**  
   `python:3.11` — Full Python distribution (~1 GB). Bao gồm toàn bộ Python runtime, pip, và build tools.

2. **Working directory là gì?**  
   `/app` — Mọi command tiếp theo chạy trong thư mục này trong container.

3. **Tại sao COPY requirements.txt trước?**  
   Docker build theo layers. Nếu `requirements.txt` không thay đổi, Docker dùng layer cache — không cần `pip install` lại. Chỉ layer code mới bị rebuild. Điều này giúp build nhanh hơn nhiều khi chỉ thay đổi code.

4. **CMD vs ENTRYPOINT khác nhau thế nào?**  
   - `CMD ["python", "app.py"]` — Có thể override khi chạy: `docker run image python other.py`  
   - `ENTRYPOINT ["python"]` — Fixed, không thể override; `CMD` trở thành default args  
   - Production thường dùng `CMD` với uvicorn để operator có thể thay đổi khi cần debug.

---

### Exercise 2.2: Build và run

```bash
# Build
docker build -f 02-docker/develop/Dockerfile -t my-agent:develop .

# Run
docker run -p 8000:8000 my-agent:develop

# Test
curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Docker?"}'
```

**Image size quan sát được:** ~950 MB (do `python:3.11` full image)

---

### Exercise 2.3: Multi-stage build (`02-docker/production/Dockerfile`)

- **Stage 1 (builder):** Cài tất cả dependencies kể cả build tools (`gcc`, `libpq-dev`). Package được install vào `/root/.local`.
- **Stage 2 (runtime):** Dùng `python:3.11-slim` (không có build tools). Copy ONLY packages từ builder — không copy compiler, headers, cache pip.
- **Tại sao image nhỏ hơn?** Loại bỏ: build tools (~200 MB), pip cache, header files, test files. Chỉ giữ Python runtime + app packages.

**So sánh:**
- Develop image: ~950 MB
- Production image: ~180 MB  
- Giảm: ~81% nhỏ hơn

---

### Exercise 2.4: Docker Compose architecture

```
Client → Nginx (port 80)
              ↓
         Agent (port 8000) ← Redis (port 6379)
```

**Services:** Nginx (reverse proxy/LB), Agent (FastAPI app), Redis (session/cache).  
**Communication:** Nginx nhận HTTP → forward đến Agent. Agent gọi Redis cho state.

---

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment

**Steps thực hiện:**
```bash
npm i -g @railway/cli
railway login
railway init
railway variables set PORT=8000
railway variables set AGENT_API_KEY=my-secret-key-production
railway up
railway domain
```

**Public URL:** `https://ai-agent-backend-j6j5.onrender.com`
**Frontend URL:** `https://ai-agent-frontend-iw63.onrender.com/`

**Test:**
```bash
# Health check
curl https://ai-agent-production.railway.app/health
# Response: {"status":"ok","version":"1.0.0",...}

# Agent call
curl -X POST https://ai-agent-production.railway.app/ask \
  -H "X-API-Key: my-secret-key-production" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","question":"Hello from the cloud!"}'
```

---

### Exercise 3.2: So sánh `render.yaml` vs `railway.toml`

| Aspect | `railway.toml` | `render.yaml` |
|--------|---------------|---------------|
| **Format** | TOML | YAML |
| **Build** | Chỉ specify builder type | Specify runtime (docker) + region |
| **Health check** | `healthcheckPath` | `healthCheckPath` |
| **Region** | Không specify (auto) | `region: singapore` |
| **Env vars** | Set qua CLI/dashboard | Định nghĩa trong file với `generateValue` |
| **Plan** | Không specify | `plan: starter` |
| **Auto-deploy** | Implicit | `autoDeploy: true` |

**Điểm chung:** Cả hai đều reference health check endpoint, specify start command.

---

### Exercise 3.3: GCP Cloud Run (Optional)

`cloudbuild.yaml` định nghĩa CI/CD pipeline: 
1. Build Docker image
2. Push lên Google Container Registry
3. Deploy lên Cloud Run

`service.yaml` định nghĩa Cloud Run service: replicas, resources, scaling rules, health checks.

---

## Part 4: API Security

### Exercise 4.1: API Key Authentication

**API key check ở đâu?** → Middleware `verify_api_key()` được gọi trước mọi protected endpoint qua FastAPI `Security()` dependency.

**Nếu sai key?** → HTTP 401 Unauthorized với message: "Invalid or missing API key"

**Làm sao rotate key?** → Update env var `AGENT_API_KEY` trên platform và restart service. Không cần thay đổi code.

**Test kết quả:**
```bash
# Không có key → 401
curl http://localhost:8000/ask -X POST \
  -d '{"user_id":"test","question":"Hello"}'
# {"detail":"Invalid or missing API key. Include header: X-API-Key: <key>"}

# Có key → 200
curl http://localhost:8000/ask -X POST \
  -H "X-API-Key: dev-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","question":"Hello"}'
# {"user_id":"test","question":"Hello","answer":"...","model":"gpt-4o-mini",...}
```

---

### Exercise 4.2: JWT Authentication

Flow JWT:
1. Client POST `/token` với username/password → nhận JWT token
2. Client gửi `Authorization: Bearer <token>` trong mọi request
3. Server verify signature và expiry của token

Ưu điểm vs API Key: Có expiry tự động, có thể embed user claims (role, permissions) trong payload.

---

### Exercise 4.3: Rate Limiting

**Algorithm:** Sliding Window Counter  
**Limit:** 10 requests/minute per user (configurable qua `RATE_LIMIT_PER_MINUTE` env var)  
**Bypass cho admin:** `rate_limiter_admin = RateLimiter(max_requests=100)` — Admin có limit cao hơn

**Test kết quả:**
```bash
for i in {1..15}; do
  curl http://localhost:8000/ask -X POST \
    -H "X-API-Key: dev-key-change-me" \
    -H "Content-Type: application/json" \
    -d '{"user_id":"testuser","question":"Test '$i'"}'
  echo ""
done
# Sau request 10: HTTP 429 "Rate limit exceeded: 10 req/min"
# Header: Retry-After: 60
```

---

### Exercise 4.4: Cost Guard Implementation

```python
def check_and_record_cost(user_id: str, input_tokens: int, output_tokens: int) -> None:
    """Track cost per user. Raises 402 when monthly budget exceeded."""
    r = get_redis()
    cost = (input_tokens / 1000) * 0.00015 + (output_tokens / 1000) * 0.0006
    budget = settings.monthly_budget_usd
    month_key = datetime.now().strftime("%Y-%m")

    if r:
        redis_key = f"cost:{user_id}:{month_key}"
        current = float(r.get(redis_key) or 0)
        if current + cost > budget:
            raise HTTPException(402, f"Monthly budget ${budget} exceeded.")
        r.incrbyfloat(redis_key, cost)
        r.expire(redis_key, 32 * 24 * 3600)  # 32 days TTL
    else:
        # In-memory fallback
        current = _monthly_cost[user_id]
        if current + cost > budget:
            raise HTTPException(402, f"Monthly budget ${budget} exceeded.")
        _monthly_cost[user_id] += cost
```

**Approach:** Mỗi user có budget riêng $10/tháng. Key trong Redis là `cost:{user_id}:{YYYY-MM}` → tự động reset đầu tháng. TTL 32 ngày để cover trường hợp tháng dài.

---

## Part 5: Scaling & Reliability

### Exercise 5.1: Health và Readiness Checks

```python
@app.get("/health")
def health():
    """Liveness probe — container còn sống không?"""
    return {
        "status": "ok",
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "checks": {"llm": "mock", "redis": "connected"},
    }

@app.get("/ready")
def ready():
    """Readiness probe — sẵn sàng nhận traffic không?"""
    if not _is_ready:
        raise HTTPException(503, "Not ready")
    return {"ready": True}
```

**Sự khác biệt:** `/health` = "process còn sống?" (liveness); `/ready` = "có thể handle request chưa?" (readiness). Readiness check thêm logic kiểm tra dependencies (Redis, DB).

---

### Exercise 5.2: Graceful Shutdown

```python
def _handle_signal(signum, _frame):
    logger.info(json.dumps({
        "event": "graceful_shutdown",
        "signum": signum,
        "message": "SIGTERM received, finishing requests and shutting down...",
    }))

signal.signal(signal.SIGTERM, _handle_signal)

# uvicorn.run(..., timeout_graceful_shutdown=30)
# → uvicorn đợi tối đa 30 giây cho requests hiện tại hoàn thành
```

**Test:**
```bash
python app.py &
PID=$!
curl http://localhost:8000/ask -d '{"question":"Long task"}' &
kill -TERM $PID
# Quan sát: Request hoàn thành trước khi process exit
# Log: {"event":"graceful_shutdown","signum":15,"message":"SIGTERM received..."}
```

---

### Exercise 5.3: Stateless Design

**Anti-pattern (stateful):**
```python
# In-memory → mất khi restart, không scale
conversation_history = {}

@app.post("/ask")
def ask(user_id: str, question: str):
    history = conversation_history.get(user_id, [])  # ❌
```

**Correct (stateless với Redis):**
```python
def get_history(user_id: str) -> list[dict]:
    r = get_redis()
    raw = r.lrange(f"history:{user_id}", 0, MAX_HISTORY * 2 - 1)  # ✅
    return [json.loads(item) for item in raw]
```

**Tại sao quan trọng:** Khi scale 3 instances, mỗi instance có memory riêng → user A gọi instance 1, user B gọi instance 2, nhưng history của cả 2 đều cần accessible. Redis là shared state store.

---

### Exercise 5.4: Load Balancing

```bash
docker compose up --scale agent=3
```

**Quan sát:** 3 agent containers khởi động → Nginx phân tán requests theo round-robin. Nếu 1 instance die:
```bash
docker compose kill agent_1
# → Nginx detect health check fail → route traffic sang 2 instances còn lại
# → Không có downtime!
```

---

### Exercise 5.5: Test Stateless Design

```bash
python test_stateless.py
```

**Kết quả mong đợi:**
1. Tạo conversation với instance 1
2. Kill instance 1
3. Gọi tiếp với instance 2
4. ✅ Conversation history vẫn còn (trong Redis)

---

## Bonus Features Implemented

### 1. Streaming Responses (SSE) — `/ask/stream`

```bash
curl -N -H "X-API-Key: dev-key-change-me" \
  -X POST http://localhost:8000/ask/stream \
  -H "Content-Type: application/json" \
  -d '{"user_id":"alice","question":"Tell me about Docker"}'

# Output (stream):
# data: {"token": "Container ", "done": false}
# data: {"token": "là ", "done": false}
# ...
# data: {"token": "", "done": true, "answer": "Container là...", "timestamp": "..."}
```

### 2. Conversation History Endpoints

```bash
# Xem history
GET /history/{user_id}

# Xóa history
DELETE /history/{user_id}
```

### 3. Per-user Cost Guard với Redis

Thay vì track cost global theo ngày, track per-user per-month với Redis key `cost:{user_id}:{YYYY-MM}`.

### 4. Metrics Endpoint với Redis Info

```bash
GET /metrics
# Returns: uptime, requests, redis memory, budget info
```

### 5. Non-root user trong Dockerfile

```dockerfile
RUN groupadd -r agent && useradd -r -g agent -d /app agent
USER agent
```

Chạy process không phải root → giảm attack surface nếu container bị compromise.

# Production AI Agent — Day 12 Lab

> **AICB-P1 · VinUniversity 2026**  
> Lab 12: Deploy Your AI Agent to Production  
> Kết hợp TẤT CẢ concepts đã học trong 1 project hoàn chỉnh.

---

## Tổng Quan

Production-ready AI agent với đầy đủ features:

| Feature | Status | Details |
|---------|--------|---------|
| **Config** | ✅ | 12-Factor — tất cả từ env vars |
| **Auth** | ✅ | API Key (`X-API-Key` header) |
| **Rate Limiting** | ✅ | 10 req/min per user (sliding window) |
| **Cost Guard** | ✅ | $10/month per user (Redis-backed) |
| **Health Check** | ✅ | `GET /health` — liveness probe |
| **Readiness** | ✅ | `GET /ready` — readiness probe |
| **Graceful Shutdown** | ✅ | SIGTERM handler + 30s timeout |
| **Stateless** | ✅ | Conversation history trong Redis |
| **Streaming** | ✅ | SSE streaming via `POST /ask/stream` |
| **Docker** | ✅ | Multi-stage build, non-root user |
| **Structured Logging** | ✅ | JSON format |
| **CORS + Security Headers** | ✅ | X-Content-Type-Options, X-Frame-Options |

---

## Cấu Trúc

```
06-lab-complete/
├── app/
│   ├── __init__.py
│   ├── main.py         # Application chính — tất cả endpoints
│   └── config.py       # 12-factor config từ env vars
├── utils/
│   └── mock_llm.py     # Mock LLM (không cần API key thật)
├── Dockerfile          # Multi-stage, non-root, < 500 MB
├── docker-compose.yml  # Agent + Redis stack
├── railway.toml        # Deploy Railway (< 5 phút)
├── render.yaml         # Deploy Render
├── requirements.txt    # Python dependencies
├── .env.example        # Template config
├── .dockerignore       # Build exclusions
└── check_production_ready.py  # Validation script
```

---

## Quick Start — Local

### Option 1: Docker Compose (Recommended)

```bash
# 1. Setup environment
cp .env.example .env.local

# 2. Chạy toàn bộ stack (Agent + Redis)
docker compose up

# 3. Test
curl http://localhost:8000/health

# 4. Lấy API key từ .env.local
API_KEY=dev-key-change-me-in-production
curl -H "X-API-Key: $API_KEY" \
     -X POST http://localhost:8000/ask \
     -H "Content-Type: application/json" \
     -d '{"user_id": "alice", "question": "What is Docker?"}'
```

### Option 2: Chạy Trực Tiếp

```bash
# Cài dependencies
pip install -r requirements.txt

# Chạy (từ thư mục 06-lab-complete)
PYTHONPATH=. AGENT_API_KEY=my-key uvicorn app.main:app --reload

# Hoặc
PYTHONPATH=. AGENT_API_KEY=my-key python app/main.py
```

---

## API Endpoints

### `GET /` — Info
```bash
curl http://localhost:8000/
```

### `GET /health` — Liveness Probe (public)
```bash
curl http://localhost:8000/health
# {"status":"ok","version":"1.0.0","uptime_seconds":42.3,...}
```

### `GET /ready` — Readiness Probe (public)
```bash
curl http://localhost:8000/ready
# {"ready":true,"timestamp":"..."}
```

### `POST /ask` — Ask Agent (auth required)
```bash
curl -X POST http://localhost:8000/ask \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "alice", "question": "Explain cloud deployment"}'
```

### `POST /ask/stream` — Streaming SSE (auth required)
```bash
curl -N -X POST http://localhost:8000/ask/stream \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "alice", "question": "Tell me about Docker"}'
# Output: token-by-token SSE stream
```

### `GET /history/{user_id}` — Conversation History (auth required)
```bash
curl http://localhost:8000/history/alice -H "X-API-Key: YOUR_KEY"
```

### `DELETE /history/{user_id}` — Clear History (auth required)
```bash
curl -X DELETE http://localhost:8000/history/alice -H "X-API-Key: YOUR_KEY"
```

### `GET /metrics` — Metrics (auth required)
```bash
curl http://localhost:8000/metrics -H "X-API-Key: YOUR_KEY"
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `8000` | Server port |
| `ENVIRONMENT` | `development` | `development`/`production` |
| `DEBUG` | `false` | Enable debug mode & auto-reload |
| `APP_NAME` | `Production AI Agent` | App display name |
| `APP_VERSION` | `1.0.0` | App version |
| `OPENAI_API_KEY` | *(empty)* | Real API key (empty = mock LLM) |
| `LLM_MODEL` | `gpt-4o-mini` | Model to use |
| `AGENT_API_KEY` | `dev-key-...` | **Required**: Auth key for API calls |
| `JWT_SECRET` | `dev-jwt-...` | JWT signing secret |
| `ALLOWED_ORIGINS` | `*` | CORS origins (comma-separated) |
| `RATE_LIMIT_PER_MINUTE` | `10` | Max requests per user per minute |
| `MONTHLY_BUDGET_USD` | `10.0` | Max spend per user per month |
| `REDIS_URL` | *(empty)* | Redis URL (empty = in-memory fallback) |

---

## Deploy to Railway (< 5 phút)

```bash
# 1. Install CLI
npm i -g @railway/cli

# 2. Login & init
railway login
railway init

# 3. Set secrets
railway variables set AGENT_API_KEY=$(openssl rand -hex 32)
railway variables set JWT_SECRET=$(openssl rand -hex 32)
railway variables set ENVIRONMENT=production
railway variables set RATE_LIMIT_PER_MINUTE=10
railway variables set MONTHLY_BUDGET_USD=10.0

# 4. Deploy
railway up

# 5. Get URL
railway domain
```

---

## Production Readiness Check

```bash
python check_production_ready.py
# Result: 20/20 checks passed (100%)
# 🎉 PRODUCTION READY! Deploy nào!
```

---

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTPS
       ▼
┌─────────────────┐
│   Nginx (LB)    │  ← docker-compose scale
└──────┬──────────┘
       │
       ├──────────┬──────────┐
       ▼          ▼          ▼
  ┌────────┐  ┌────────┐  ┌────────┐
  │Agent 1 │  │Agent 2 │  │Agent 3 │  ← Stateless
  └────┬───┘  └────┬───┘  └────┬───┘
       │            │            │
       └────────────┴────────────┘
                    │
                    ▼
             ┌──────────┐
             │  Redis   │  ← Shared state
             └──────────┘
               (history, rate limit, cost)
```

---

## Grading Checklist (100 points)

- [x] **Functionality (20pt)** — Agent trả lời câu hỏi + conversation history
- [x] **Docker (15pt)** — Multi-stage build, < 500 MB, docker-compose với Redis
- [x] **Security (20pt)** — API Key auth + rate limit (10/min) + cost guard ($10/month)
- [x] **Reliability (20pt)** — /health + /ready + graceful shutdown + stateless Redis
- [x] **Scalability (15pt)** — Stateless design + Nginx load balancing
- [x] **Deployment (10pt)** — railway.toml + render.yaml + public URL

**Bonus:**
- [x] Streaming responses (SSE) — `POST /ask/stream`
- [x] Per-user conversation history endpoints — `GET/DELETE /history/{user_id}`  
- [x] Non-root Docker user
- [x] Per-user monthly cost guard (Redis-backed)
- [x] Metrics endpoint

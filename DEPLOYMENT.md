# Deployment Information

## Public URL

> ⚠️ Điền URL thật sau khi deploy (Railway hoặc Render)

```
https://your-agent.railway.app
```

## Platform

**Railway** (recommended — deploy < 5 phút)

Alternative: Render, GCP Cloud Run

---

## Quick Deploy

### Railway (< 5 phút)

```bash
# 1. Install Railway CLI
npm i -g @railway/cli

# 2. Login
railway login

# 3. Init project
railway init

# 4. Set environment variables
railway variables set AGENT_API_KEY=your-secret-api-key-here
railway variables set JWT_SECRET=your-jwt-secret-here
railway variables set ENVIRONMENT=production
railway variables set RATE_LIMIT_PER_MINUTE=10
railway variables set MONTHLY_BUDGET_USD=10.0

# 5. Deploy
railway up

# 6. Get public URL
railway domain
```

### Render

1. Push repo lên GitHub
2. Render Dashboard → **New** → **Blueprint**
3. Connect GitHub repo → Render tự động đọc `render.yaml`
4. Set secrets trong dashboard:
   - `OPENAI_API_KEY` (nếu dùng OpenAI thật)
   - `AGENT_API_KEY`
   - `JWT_SECRET`
5. Deploy → Nhận URL!

---

## Test Commands

### Health Check

```bash
curl https://your-agent.railway.app/health
# Expected:
# {
#   "status": "ok",
#   "version": "1.0.0",
#   "environment": "production",
#   "uptime_seconds": 42.3,
#   "checks": {"llm": "mock", "redis": "unavailable"},
#   "timestamp": "2026-04-17T10:00:00+00:00"
# }
```

### Readiness Check

```bash
curl https://your-agent.railway.app/ready
# Expected: {"ready": true, "timestamp": "..."}
```

### Authentication Test (without key → 401)

```bash
curl -X POST https://your-agent.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "question": "Hello"}'
# Expected: HTTP 401
# {"detail": "Invalid or missing API key. Include header: X-API-Key: <key>"}
```

### API Test (with authentication)

```bash
curl -X POST https://your-agent.railway.app/ask \
  -H "X-API-Key: YOUR_AGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "question": "Hello, what is Docker?"}'
# Expected: HTTP 200
# {
#   "user_id": "test",
#   "question": "Hello, what is Docker?",
#   "answer": "Container là cách đóng gói app...",
#   "model": "gpt-4o-mini",
#   "history_length": 2,
#   "timestamp": "2026-04-17T10:00:00+00:00"
# }
```

### Conversation History

```bash
# Gửi 2 tin nhắn liên tiếp
curl -X POST https://your-agent.railway.app/ask \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "alice", "question": "My name is Alice"}'

curl -X POST https://your-agent.railway.app/ask \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "alice", "question": "What is my name?"}'
# Agent nhớ context từ turn trước

# Xem history
curl -H "X-API-Key: YOUR_KEY" \
  https://your-agent.railway.app/history/alice
```

### Streaming Response (Bonus Feature)

```bash
curl -N -X POST https://your-agent.railway.app/ask/stream \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "question": "Tell me about cloud deployment"}'
# Output stream:
# data: {"token": "Deployment ", "done": false}
# data: {"token": "là ", "done": false}
# ...
# data: {"token": "", "done": true, "answer": "...", "timestamp": "..."}
```

### Rate Limiting Test (should hit 429 after 10 requests)

```bash
for i in {1..15}; do
  echo -n "Request $i: "
  curl -s -o /dev/null -w "%{http_code}" \
    -X POST https://your-agent.railway.app/ask \
    -H "X-API-Key: YOUR_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"user_id\":\"ratelimit_test\",\"question\":\"Test $i\"}"
  echo ""
done
# Requests 1-10: 200
# Requests 11+: 429 (Too Many Requests)
```

---

## Environment Variables Set on Platform

| Variable | Value | Notes |
|----------|-------|-------|
| `PORT` | `8000` | Auto-set by Railway |
| `ENVIRONMENT` | `production` | Disables /docs |
| `AGENT_API_KEY` | `<secret>` | Generate strong key |
| `JWT_SECRET` | `<secret>` | Generate strong secret |
| `RATE_LIMIT_PER_MINUTE` | `10` | Requests per user per minute |
| `MONTHLY_BUDGET_USD` | `10.0` | Per-user monthly budget |
| `REDIS_URL` | `<railway redis url>` | Optional: add Redis service |
| `OPENAI_API_KEY` | `<key or empty>` | Empty = use mock LLM |

---

## Local Development

```bash
# Clone repo
cd 06-lab-complete

# Setup environment
cp .env.example .env.local
# Edit .env.local với values thật

# Run với Docker Compose (recommended)
docker compose up

# Hoặc chạy trực tiếp
pip install -r requirements.txt
AGENT_API_KEY=dev-key uvicorn app.main:app --reload

# Test
curl http://localhost:8000/health
```

---

## Screenshots

- [Deployment dashboard](screenshots/dashboard.png)
- [Service running](screenshots/running.png)
- [Health check test](screenshots/health.png)
- [API test](screenshots/api_test.png)

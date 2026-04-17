# 🚀 Hướng Dẫn Deploy Chi Tiết — Day 12 Lab

> **Thời gian:** ~30 phút (local) | ~10 phút (cloud)  
> **Môi trường:** Windows 10/11, Python 3.12, Docker 29, Node 22

---

## 📦 Bước 0: Kiểm Tra & Cài Thư Viện

### 0.1 Kiểm tra môi trường

Mở **PowerShell / Git Bash** và chạy:

```bash
python --version          # cần >= 3.11
pip --version
docker --version          # cần >= 24
docker compose version    # cần >= 2
node --version            # cần >= 18 (cho Railway CLI)
npm --version
```

**Kết quả mong đợi của máy này:**
```
Python 3.12.0
Docker version 29.2.0
Docker Compose version v5.0.2
v22.13.0 (Node)
```

---

### 0.2 Cài thư viện Python (đã thực hiện ✅)

```bash
cd e:\LabAIThucChien\day12_ha-tang-cloud_va_deployment\06-lab-complete

pip install fastapi==0.115.0 "uvicorn[standard]==0.30.0" pydantic==2.9.0 \
    pydantic-settings==2.5.0 pyjwt==2.9.0 python-dotenv==1.0.1 \
    redis==5.1.0 psutil==6.0.0
```

**Hoặc dùng requirements.txt:**
```bash
pip install -r requirements.txt
```

**Verify tất cả đã cài:**
```bash
python -c "import fastapi, uvicorn, pydantic, pydantic_settings, jwt, dotenv, redis, psutil; print('ALL OK')"
```

---

### 0.3 Cài Railway CLI (đã thực hiện ✅)

```bash
npm install -g @railway/cli

# Verify
railway --version    # phải ra: railway 4.x.x
```

---

## 🏠 Phần 1: Chạy Local (không cần Docker)

### 1.1 Setup môi trường

```bash
cd e:\LabAIThucChien\day12_ha-tang-cloud_va_deployment\06-lab-complete

# Copy file cấu hình
copy .env.example .env.local
```

Mở `.env.local` bằng VS Code và chỉnh sửa:

```env
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development
DEBUG=true
APP_NAME=Production AI Agent
APP_VERSION=1.0.0

# Để trống = dùng mock LLM (không cần API key thật)
OPENAI_API_KEY=

# BẮT BUỘC đặt giá trị này
AGENT_API_KEY=my-local-test-key-2026
JWT_SECRET=my-local-jwt-secret-2026

RATE_LIMIT_PER_MINUTE=10
MONTHLY_BUDGET_USD=10.0

# Để trống nếu chưa cài Redis
REDIS_URL=
ALLOWED_ORIGINS=*
```

---

### 1.2 Khởi động server

```bash
# Cách 1: Dùng python trực tiếp
cd e:\LabAIThucChien\day12_ha-tang-cloud_va_deployment\06-lab-complete
set PYTHONPATH=.
set AGENT_API_KEY=my-local-test-key-2026
python -m uvicorn app.main:app --reload --port 8000
```

```bash
# Cách 2: Dùng biến môi trường từ file .env.local (Windows PowerShell)
cd e:\LabAIThucChien\day12_ha-tang-cloud_va_deployment\06-lab-complete
$env:PYTHONPATH = "."
$env:AGENT_API_KEY = "my-local-test-key-2026"
python -m uvicorn app.main:app --reload --port 8000
```

**Kết quả thành công:**
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

### 1.3 Test API (mở terminal mới)

```bash
# ✅ Health check (public)
curl http://localhost:8000/health

# ✅ Root info
curl http://localhost:8000/

# ❌ Không có key → 401
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"alice\",\"question\":\"Hello\"}"

# ✅ Có key → 200
curl -X POST http://localhost:8000/ask \
  -H "X-API-Key: my-local-test-key-2026" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"alice\",\"question\":\"What is Docker?\"}"

# ✅ Xem docs (chỉ ở development)
start http://localhost:8000/docs
```

**Trên PowerShell Windows** (curl khác syntax):
```powershell
# Health check
Invoke-WebRequest -Uri "http://localhost:8000/health" | Select-Object -Expand Content

# Ask với API key
$body = '{"user_id":"alice","question":"What is Docker?"}'
$headers = @{"X-API-Key"="my-local-test-key-2026"; "Content-Type"="application/json"}
Invoke-WebRequest -Uri "http://localhost:8000/ask" -Method POST -Headers $headers -Body $body | Select-Object -Expand Content
```

---

## 🐳 Phần 2: Chạy với Docker

### 2.1 Build Docker image

```bash
cd e:\LabAIThucChien\day12_ha-tang-cloud_va_deployment\06-lab-complete

# Build image
docker build -t my-ai-agent:latest .

# Xem image đã build (phải < 500 MB)
docker images my-ai-agent
```

---

### 2.2 Tạo file .env.local

```bash
copy .env.example .env.local
```

Chỉnh sửa `.env.local`:
```env
AGENT_API_KEY=my-docker-test-key-2026
JWT_SECRET=my-docker-jwt-secret-2026
REDIS_URL=redis://redis:6379/0
ENVIRONMENT=staging
```

---

### 2.3 Chạy Docker Compose (Agent + Redis)

```bash
# Khởi động toàn bộ stack
docker compose up

# Chạy nền (background)
docker compose up -d

# Xem logs
docker compose logs -f agent

# Dừng
docker compose down
```

**Verify đang chạy:**
```bash
docker compose ps
# phải thấy: agent (healthy), redis (healthy)
```

---

### 2.4 Test Docker stack

```bash
# Health (qua port 8000 trực tiếp)
curl http://localhost:8000/health

# Ask qua Docker
curl -X POST http://localhost:8000/ask \
  -H "X-API-Key: my-docker-test-key-2026" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"bob\",\"question\":\"What is Redis?\"}"

# Test conversation history (turn 1)
curl -X POST http://localhost:8000/ask \
  -H "X-API-Key: my-docker-test-key-2026" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"carol\",\"question\":\"My name is Carol\"}"

# Test conversation history (turn 2 - phải nhớ Carol)
curl -X POST http://localhost:8000/ask \
  -H "X-API-Key: my-docker-test-key-2026" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"carol\",\"question\":\"What is my name?\"}"

# Xem history
curl http://localhost:8000/history/carol \
  -H "X-API-Key: my-docker-test-key-2026"
```

---

### 2.5 Test rate limiting

```bash
# Gửi 11 requests (request 11 phải bị 429)
for i in {1..11}; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST http://localhost:8000/ask \
    -H "X-API-Key: my-docker-test-key-2026" \
    -H "Content-Type: application/json" \
    -d "{\"user_id\":\"ratetest\",\"question\":\"test $i\"}")
  echo "Request $i: HTTP $CODE"
done
```

---

### 2.6 Scale ra 3 instances (load balancing)

> Yêu cầu: Thêm nginx vào docker-compose hoặc dùng production stack từ `05-scaling-reliability`

```bash
# Scale agent lên 3 instances
docker compose up --scale agent=3

# Xem 3 containers
docker compose ps

# Test - requests sẽ được phân tán
for i in {1..6}; do
  curl -s http://localhost:8000/health | python -c "import sys,json; d=json.load(sys.stdin); print(f'req $i → uptime: {d[\"uptime_seconds\"]}s')"
done
```

---

## ☁️ Phần 3: Deploy lên Railway (Cloud)

### 3.1 Tạo tài khoản Railway

1. Vào **[railway.app](https://railway.app)**
2. Click **"Login with GitHub"**
3. Authorize Railway
4. Railway cấp **$5 free credit** (đủ cho lab)

---

### 3.2 Push code lên GitHub

> ⚠️ Bắt buộc trước khi deploy Railway!

```bash
cd e:\LabAIThucChien\day12_ha-tang-cloud_va_deployment

# Khởi tạo git (nếu chưa có)
git init

# Thêm .gitignore
# Đảm bảo .env.local và .env KHÔNG bị commit
cat .gitignore | grep ".env"   # phải thấy dòng .env*

# Stage và commit
git add .
git commit -m "feat: production-ready AI agent day12 lab"

# Tạo repo trên GitHub rồi push
git remote add origin https://github.com/YOUR_USERNAME/day12-agent.git
git branch -M main
git push -u origin main
```

---

### 3.3 Deploy Railway từ CLI

```bash
cd e:\LabAIThucChien\day12_ha-tang-cloud_va_deployment\06-lab-complete

# Bước 1: Login Railway
railway login
# → Trình duyệt mở, login bằng GitHub

# Bước 2: Tạo project mới
railway init
# → Nhập tên project: day12-ai-agent
# → Chọn: "Empty Project"

# Bước 3: Set environment variables (BẮT BUỘC)
railway variables set AGENT_API_KEY=production-secret-key-2026-change-this
railway variables set JWT_SECRET=production-jwt-secret-2026-change-this
railway variables set ENVIRONMENT=production
railway variables set RATE_LIMIT_PER_MINUTE=10
railway variables set MONTHLY_BUDGET_USD=10.0
railway variables set APP_VERSION=1.0.0

# (Optional) Nếu có OpenAI API key thật
# railway variables set OPENAI_API_KEY=sk-your-real-key

# Bước 4: Deploy
railway up

# Bước 5: Lấy public URL
railway domain

# Xem logs real-time
railway logs
```

**Output mong đợi sau `railway up`:**
```
✔ Build successful
✔ Deploy successful
https://day12-ai-agent-production.railway.app
```

---

### 3.4 Thêm Redis vào Railway

```bash
# Thêm Redis service vào cùng project
railway add --service redis

# Railway tự động set REDIS_URL vào app
# Verify biến đã được set
railway variables
```

---

### 3.5 Test Railway URL

```bash
# Lưu URL vào biến
RAILWAY_URL=https://day12-ai-agent-production.railway.app

# Test health
curl $RAILWAY_URL/health

# Test auth (phải 401)
curl -X POST $RAILWAY_URL/ask \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"test\",\"question\":\"Hello\"}"

# Test với key
curl -X POST $RAILWAY_URL/ask \
  -H "X-API-Key: production-secret-key-2026-change-this" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"alice\",\"question\":\"What is cloud deployment?\"}"

# Test rate limiting (chạy 11 lần)
for i in {1..11}; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST $RAILWAY_URL/ask \
    -H "X-API-Key: production-secret-key-2026-change-this" \
    -H "Content-Type: application/json" \
    -d "{\"user_id\":\"ratetest\",\"question\":\"test $i\"}")
  echo "Request $i: HTTP $CODE"
done
```

---

## 🌐 Phần 4: Deploy lên Render (Alternative)

### 4.1 Tạo tài khoản Render

1. Vào **[render.com](https://render.com)**
2. Click **"Get Started for Free"**
3. Sign up bằng GitHub
4. Free tier: **750 giờ/tháng** (đủ cho 1 service 24/7)

---

### 4.2 Deploy từ GitHub

1. **Dashboard** → **New** → **Blueprint**
2. **Connect Repository** → Chọn repo của bạn
3. Render tự đọc file `render.yaml`
4. **Apply** → Điền secrets:
   - `OPENAI_API_KEY`: (để trống nếu dùng mock)
   - `AGENT_API_KEY`: `your-strong-secret-key`
   - `JWT_SECRET`: `your-strong-jwt-secret`
5. Click **Apply** → Deploy bắt đầu

---

### 4.3 Thêm Redis trên Render

1. **Dashboard** → **New** → **Redis**
2. Chọn **Free plan**
3. Tên: `day12-redis`
4. Sau khi tạo, copy **Internal Redis URL**
5. Vào service **day12-ai-agent** → **Environment** → Thêm:
   - `REDIS_URL` = URL vừa copy

---

### 4.4 Test Render URL

```bash
RENDER_URL=https://day12-ai-agent.onrender.com

curl $RENDER_URL/health
curl -X POST $RENDER_URL/ask \
  -H "X-API-Key: your-strong-secret-key" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"test\",\"question\":\"Hello from Render!\"}"
```

---

## ✅ Phần 5: Chạy Production Readiness Check

```bash
cd e:\LabAIThucChien\day12_ha-tang-cloud_va_deployment\06-lab-complete

python check_production_ready.py
```

**Kết quả mong đợi:**
```
=======================================================
  Production Readiness Check — Day 12 Lab
=======================================================

📁 Required Files
  ✅ Dockerfile exists
  ✅ docker-compose.yml exists
  ✅ .dockerignore exists
  ✅ .env.example exists
  ✅ requirements.txt exists
  ✅ railway.toml or render.yaml exists

🔒 Security
  ✅ .env in .gitignore
  ✅ No hardcoded secrets in code

🌐 API Endpoints (code check)
  ✅ /health endpoint defined
  ✅ /ready endpoint defined
  ✅ Authentication implemented
  ✅ Rate limiting implemented
  ✅ Graceful shutdown (SIGTERM)
  ✅ Structured logging (JSON)

🐳 Docker
  ✅ Multi-stage build
  ✅ Non-root user
  ✅ HEALTHCHECK instruction
  ✅ Slim base image
  ✅ .dockerignore covers .env
  ✅ .dockerignore covers __pycache__

=======================================================
  Result: 20/20 checks passed (100%)
  🎉 PRODUCTION READY! Deploy nào!
=======================================================
```

---

## 🎁 Phần 6: Test Bonus Features

### 6.1 Streaming SSE (bonus endpoint)

```bash
# Git Bash / Linux / Mac
curl -N -X POST http://localhost:8000/ask/stream \
  -H "X-API-Key: my-local-test-key-2026" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"stream_test\",\"question\":\"Tell me about Docker\"}"

# Kết quả (stream từng token):
# data: {"token": "Container ", "done": false}
# data: {"token": "là ", "done": false}
# data: {"token": "cách ", "done": false}
# ...
# data: {"token": "", "done": true, "answer": "Container là...", "timestamp": "..."}
```

**Trên PowerShell:**
```powershell
$headers = @{"X-API-Key"="my-local-test-key-2026"; "Content-Type"="application/json"}
$body = '{"user_id":"stream_test","question":"Tell me about Docker"}'
Invoke-RestMethod -Uri "http://localhost:8000/ask/stream" -Method POST -Headers $headers -Body $body
```

---

### 6.2 Conversation History

```bash
API_KEY=my-local-test-key-2026

# Turn 1 - giới thiệu
curl -X POST http://localhost:8000/ask \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"dave\",\"question\":\"I am interested in cloud deployment\"}"

# Turn 2 - follow-up
curl -X POST http://localhost:8000/ask \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"dave\",\"question\":\"What did I say I was interested in?\"}"

# Xem toàn bộ lịch sử
curl http://localhost:8000/history/dave -H "X-API-Key: $API_KEY"

# Xóa lịch sử
curl -X DELETE http://localhost:8000/history/dave -H "X-API-Key: $API_KEY"
```

---

### 6.3 Metrics endpoint

```bash
curl http://localhost:8000/metrics -H "X-API-Key: my-local-test-key-2026"
# Kết quả:
# {
#   "uptime_seconds": 120.5,
#   "total_requests": 15,
#   "error_count": 0,
#   "monthly_budget_usd": 10.0,
#   "rate_limit_per_minute": 10,
#   "timestamp": "..."
# }
```

---

## 🐛 Xử Lý Lỗi Thường Gặp

### Lỗi: `ModuleNotFoundError: No module named 'utils'`

```bash
# Fix: Thêm PYTHONPATH
set PYTHONPATH=.
python -m uvicorn app.main:app --reload
```

### Lỗi: `AGENT_API_KEY not set`

```bash
# Fix: Set env var trước khi chạy
set AGENT_API_KEY=any-test-key
python -m uvicorn app.main:app
```

### Lỗi Docker: `port is already allocated`

```bash
# Kill process đang dùng port 8000
# Windows
netstat -ano | findstr :8000
taskkill /PID <pid_number> /F

# Linux/Mac
lsof -i :8000
kill -9 <pid>
```

### Lỗi: `docker compose: 'compose' is not a docker command`

```bash
# Dùng docker-compose thay thế (version cũ)
docker-compose up
```

### Lỗi Railway: `railway: command not found`

```bash
# Cài lại Railway CLI
npm install -g @railway/cli

# Nếu vẫn không tìm thấy, dùng npx
npx @railway/cli login
npx @railway/cli up
```

### Lỗi: Container unhealthy

```bash
# Xem logs chi tiết
docker compose logs agent

# Inspect health check
docker inspect <container_id> | grep -A 10 "Health"

# Vào container debug
docker exec -it <container_id> sh
```

---

## 📋 Tóm Tắt Nhanh

| Mục tiêu | Lệnh chính |
|-----------|------------|
| Cài thư viện | `pip install -r requirements.txt` |
| Chạy local | `PYTHONPATH=. AGENT_API_KEY=testkey python -m uvicorn app.main:app` |
| Build Docker | `docker build -t my-ai-agent .` |
| Chạy stack | `docker compose up` |
| Scale 3x | `docker compose up --scale agent=3` |
| Deploy Railway | `railway up` |
| Lấy Railway URL | `railway domain` |
| Production check | `python check_production_ready.py` |
| Health check | `curl http://localhost:8000/health` |
| Test auth | `curl -H "X-API-Key: KEY" -X POST .../ask -d '{"user_id":"u","question":"q"}'` |

---

## 📦 Thư Viện Đã Cài (Trạng Thái Hiện Tại)

| Package | Version | Mục đích |
|---------|---------|----------|
| `fastapi` | 0.115.0 | Web framework |
| `uvicorn[standard]` | 0.30.0 | ASGI server |
| `pydantic` | 2.9.0 | Data validation |
| `pydantic-settings` | 2.5.0 | Config management |
| `pyjwt` | 2.9.0 | JWT authentication |
| `python-dotenv` | 1.0.1 | .env file loading |
| `redis` | 5.1.0 | Redis client (stateless) |
| `psutil` | 6.0.0 | System monitoring |
| `railway CLI` | 4.38.0 | Deploy to Railway |

**Tất cả đã được cài trên máy này ✅**

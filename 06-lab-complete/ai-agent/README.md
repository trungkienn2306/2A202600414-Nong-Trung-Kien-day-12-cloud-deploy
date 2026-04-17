# Smart Travel Assistant

Backend core logic is in `src/` and the active frontend is `frontend/` (React + Vite).

`frontend1/` is deprecated and kept only for reference.

## 1) Setup

1. Create and fill `.env` in project root (or copy from `.env.example`).
2. Install backend dependencies:

```bash
pip install -r requirements.txt
```

3. Install frontend dependencies:

```bash
cd frontend
npm install
```

## 2) Run Backend (core)

Run from project root:

```bash
python -m uvicorn src.api_main:app --host 0.0.0.0 --port 8000 --reload
```

Core endpoints:

- `GET /health`
- `POST /chat`

`POST /chat` contract:

- Request: `{ "message": "text", "thread_id": "optional-id" }`
- Response: `{ "response": "text", "thread_id": "id", "status": "success|need_input|error", "question": "optional" }`

## 3) Run Frontend (React/Vite)

From `frontend/`:

```bash
npm run dev
```

Default Vite port is `5174`.

Frontend env:

- `frontend/.env`
- `VITE_API_BASE_URL=http://localhost:8000`

## 4) Env mapping

- Root `.env`: backend provider keys and runtime config.
- `frontend/.env`: frontend API base URL only.

## 5) Quick integration check

1. Open frontend (usually `http://localhost:5174`).
2. Confirm backend status is online.
3. Send a message and verify response.
4. Verify follow-up for `need_input` flow works in same chat thread.

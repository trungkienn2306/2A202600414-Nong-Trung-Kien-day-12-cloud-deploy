# Du lịch AI — Frontend (React + Vite)

Frontend active của dự án nằm ở thư mục `frontend/`.

Backend chuẩn nằm ở `src/` của repo root.

## API contract đang dùng

Frontend gọi backend qua:

- `GET /health`
- `POST /chat`

`POST /chat` payload:

```json
{
  "message": "Xin chào",
  "thread_id": "optional-thread-id"
}
```

Response:

```json
{
  "response": "text",
  "thread_id": "id",
  "status": "success | need_input | error",
  "question": "optional"
}
```

## Cấu hình môi trường

File: `frontend/.env`

```env
VITE_API_BASE_URL=http://localhost:8000
```

Nếu không có biến trên, frontend fallback về `http://localhost:8000`.

## Chạy local

```bash
cd frontend
npm install
npm run dev
```

Vite chạy trên port `5174` (xem `vite.config.ts`).

## Ghi chú

- `frontend1/` là legacy UI, không còn dùng làm frontend chính.
- Mọi logic agent/tool nằm ở backend `src/`, frontend chỉ render + gửi request API.

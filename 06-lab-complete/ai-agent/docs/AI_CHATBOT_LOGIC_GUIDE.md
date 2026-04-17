# Tài liệu giải thích logic AI Chatbot (cho người mới)

Tài liệu này giải thích hệ thống chatbot hiện tại trong `src/` theo cách dễ hiểu cho người mới bắt đầu học AI Agent, LangGraph và cơ chế gọi công cụ "tool calling".

## 1) Tổng quan hệ thống

Hệ thống gồm 3 lớp chính:

1. Lớp API "API layer" (FastAPI): nhận yêu cầu từ giao diện người dùng "frontend", trả kết quả JSON.
2. Lớp điều phối "Agent layer" (LangGraph + LLM): quyết định trả lời trực tiếp hay gọi công cụ.
3. Lớp công cụ "Tool layer": các hàm lấy dữ liệu bên ngoài (thời tiết, tỷ giá, tìm kiếm, tính toán, chuyến bay, khách sạn).

Mục tiêu: khi người dùng hỏi về du lịch, agent có thể:

- trả lời trực tiếp nếu đủ thông tin;
- tự gọi công cụ để lấy dữ liệu thực;
- hỏi ngược lại người dùng khi còn thiếu thông tin quan trọng.

## 2) Giải thích thuật ngữ AI cơ bản

### "LLM" là gì

"LLM" (mô hình ngôn ngữ lớn) là mô hình có khả năng hiểu ngữ cảnh và sinh văn bản. Trong dự án này, model chính đang dùng là Gemini thông qua `ChatGoogleGenerativeAI`.

### "Agent" là gì

"Agent" là lớp điều phối để mô hình không chỉ "nói", mà còn "hành động". Hành động ở đây là gọi công cụ "tool".

### "Tool calling" là gì

"Tool calling" là cơ chế để model yêu cầu hệ thống chạy một hàm cụ thể, ví dụ:

- lấy thời tiết;
- tính toán chi phí;
- tìm chuyến bay.

Model tạo lệnh gọi công cụ, hệ thống chạy hàm tương ứng, rồi trả kết quả lại cho model để tổng hợp câu trả lời.

### "LangGraph" là gì

"LangGraph" là thư viện xây dựng luồng xử lý dạng đồ thị "graph":

- node `agent`: gọi model;
- node `tools`: chạy công cụ;
- edge có điều kiện: quyết định bước tiếp theo.

Nó giúp chatbot chạy vòng lặp: suy nghĩ -> gọi công cụ -> nhận kết quả -> suy nghĩ tiếp.

### "Checkpointer" là gì

"Checkpointer" lưu trạng thái hội thoại theo `thread_id`. Dự án dùng SQLite (`checkpoints.sqlite`) để:

- nhớ ngữ cảnh giữa các lần gọi API;
- tiếp tục hội thoại khi đang ở chế độ hỏi người dùng "human-in-the-loop".

### "Human-in-the-loop" là gì

Khi thiếu thông tin quan trọng, agent gọi `request_user(question)`. Backend trả `status = need_input` để giao diện hiển thị câu hỏi cho người dùng. Sau đó, hệ thống tiếp tục chạy đúng điểm đang chờ.

## 3) Luồng xử lý từ giao diện tới backend

1. Giao diện gọi `POST /chat` với:
   - `message`;
   - `thread_id` (có thể rỗng ở lần đầu).
2. Backend (`src/api_main.py`) xác định:
   - đây là lượt chat mới; hoặc
   - đây là lượt trả lời tiếp sau câu hỏi của agent.
3. Backend gọi `agent_app.invoke(...)` từ LangGraph.
4. Nếu graph cần hỏi thêm người dùng:
   - trả `status = need_input`, kèm `question`.
5. Nếu graph đã có trả lời cuối:
   - trả `status = success`, kèm `response` và `thread_id`.

## 4) Giải thích từng tệp quan trọng trong `src/`

### `src/api_main.py` (cửa vào HTTP của hệ thống)

Chức năng:

- Khởi tạo ứng dụng FastAPI.
- Cấu hình CORS theo `CORS_ORIGINS` từ `.env`.
- Định nghĩa API:
  - `GET /health`
  - `POST /chat`

Hàm chính:

- `health_check()`:
  - kiểm tra mức sẵn sàng cơ bản của agent;
  - trả JSON gồm `status`, `core_agent`, `missing_keys`.

- `chat_endpoint(request: ChatRequest)`:
  - tạo hoặc dùng lại `thread_id`;
  - đọc trạng thái graph hiện tại;
  - nếu đang chờ câu trả lời người dùng thì cập nhật state;
  - nếu không thì đưa `HumanMessage` vào graph;
  - lấy kết quả cuối để trả về giao diện;
  - có xử lý lỗi bằng `try/except`.

### `src/agent/graph.py` (luồng xử lý của agent)

Chức năng:

- Khai báo graph và các node:
  - `agent` (gọi model),
  - `tools` (chạy công cụ),
  - `human_review` (điểm chờ thông tin từ người dùng).
- Định nghĩa điều hướng:
  - `should_continue`: nếu model có tool call thì sang `tools`, ngược lại kết thúc.
  - `route_after_tools`: nếu tool trả chuỗi yêu cầu người dùng thì sang `human_review`, ngược lại quay lại `agent`.
- Cấu hình checkpointer SQLite để lưu trạng thái.

### `src/agent/nodes.py` (logic node gọi model)

Chức năng:

- Khởi tạo model Gemini.
- Khai báo `SYSTEM_PROMPT` định hướng hành vi trả lời.
- Hàm `call_model(state)`:
  - thêm system prompt nếu cần;
  - "bind" công cụ khi `USE_TOOLS = True`;
  - gọi model và trả message mới cho graph.
- `tool_node = ToolNode(tools)` dùng node dựng sẵn để chạy tool call.

### `src/agent/tools.py` (bộ công cụ của agent)

Các công cụ đang có:

- `get_weather(location)`: lấy thời tiết hiện tại và dự báo;
- `get_exchange_rate(from_currency, to_currency)`: lấy tỷ giá;
- `web_search(query, source, max_results)`: tìm kiếm DuckDuckGo hoặc Wikipedia;
- `calculator(expression)`: tính biểu thức an toàn bằng AST;
- `search_flights_serpapi(...)`: tìm chuyến bay qua SerpApi;
- `search_hotels(...)`: tìm khách sạn qua SerpApi;
- `request_user(question)`: yêu cầu người dùng bổ sung thông tin.

Điểm cần nhớ:

- mỗi công cụ nên trả dữ liệu có cấu trúc rõ ràng;
- công cụ có thể lỗi do thiếu khóa API, timeout, hoặc thay đổi cấu trúc dữ liệu;
- file này lưu kết quả trung gian vào thư mục `tool result/` để hỗ trợ gỡ lỗi.

### `src/agent/state.py` (kiểu dữ liệu trạng thái)

`AgentState` chứa danh sách `messages`. Bộ giảm "reducer" `add_messages` sẽ nối các message mới vào trạng thái hiện có.

### `src/app.py` (chạy chat bằng dòng lệnh)

Chức năng:

- chạy chatbot trực tiếp trên terminal;
- chuẩn hóa đầu ra model bằng `format_ai_response()`;
- mô phỏng đầy đủ luồng có hỏi lại người dùng.

### `src/core/config.py` (cấu hình hệ thống)

Đọc biến môi trường và đưa vào `settings`, ví dụ:

- `GEMINI_API_KEY`
- `MODEL_NAME`
- `TEMPERATURE`
- `USE_TOOLS`

### `src/telemetry/logger.py` và `src/telemetry/metrics.py`

- `IndustryLogger`: ghi log có cấu trúc JSON;
- `PerformanceTracker`: theo dõi token, độ trễ, chi phí ước lượng.

Mục đích là giúp theo dõi và gỡ lỗi dễ hơn khi vận hành.

## 5) Logic hỏi lại người dùng "human-in-the-loop"

Khi agent cần hỏi thêm:

1. Model gọi tool `request_user("...")`.
2. Tool trả chuỗi `REQUESTED_USER_INPUT: ...`.
3. `route_after_tools()` phát hiện chuỗi này và điều hướng sang `human_review`.
4. Backend thấy graph đang chờ thì trả `status = need_input` cho giao diện.
5. Giao diện gửi lại câu trả lời với cùng `thread_id`.
6. Backend gọi `update_state(...)` để ghi câu trả lời vào đúng `tool_call_id`.
7. Graph chạy tiếp từ điểm đang dở.

Ý nghĩa:

- agent biết hỏi để tránh đoán mò;
- giảm nguy cơ trả lời sai do thiếu dữ liệu.

## 6) Vì sao cần `thread_id`

`thread_id` là khóa phiên hội thoại.

Nếu không có `thread_id`:

- graph không biết đang tiếp tục cuộc hội thoại nào;
- dễ mất ngữ cảnh và trả lời lệch.

Với `thread_id`, checkpointer khôi phục đúng trạng thái từng phiên.

## 7) Nhóm lỗi thường gặp và cách gỡ lỗi

Nhóm lỗi phổ biến:

1. Lỗi cấu hình:
   - thiếu `GEMINI_API_KEY`, `SERPAPI_KEY`, `OPENWEATHER_API_KEY`.
2. Lỗi mạng:
   - timeout khi gọi API bên thứ ba.
3. Lỗi dữ liệu:
   - dữ liệu trả về thay đổi cấu trúc.
4. Lỗi luồng graph:
   - trạng thái không như kỳ vọng khi đang chờ người dùng.

Cách gỡ lỗi nhanh:

- gọi `GET /health` trước để kiểm tra trạng thái;
- xem log backend và tệp JSON trong `tool result/`;
- kiểm tra `.env` và cấu hình CORS;
- xác nhận giao diện gửi đúng `thread_id` khi tiếp tục hội thoại.

## 8) Lộ trình học nhanh cho người mới

Nên đọc theo thứ tự:

1. `src/api_main.py` để nắm hợp đồng API "API contract";
2. `src/agent/graph.py` để hiểu luồng node và điều hướng;
3. `src/agent/nodes.py` để hiểu cách model gắn công cụ;
4. `src/agent/tools.py` để biết agent làm được gì;
5. chạy thử:
   - `GET /health`
   - `POST /chat` với câu đơn giản
   - một tình huống cần hỏi lại "need_input".

## 9) Từ điển nhanh thuật ngữ

- "Prompt": chỉ dẫn gửi vào model.
- "System prompt": chỉ dẫn cấp hệ thống, ưu tiên cao.
- "Tool": hàm để lấy dữ liệu hoặc thực thi tác vụ ngoài model.
- "Tool call": yêu cầu model gửi ra để hệ thống gọi công cụ.
- "State": trạng thái hiện tại của graph.
- "Node": một bước xử lý trong graph.
- "Edge": đường chuyển giữa các node.
- "Interrupt": điểm tạm dừng graph để chờ sự kiện ngoài.
- "Checkpoint": điểm lưu trạng thái để chạy tiếp.
- "Hallucination": model trả lời có vẻ tự tin nhưng sai thực tế.

---

Nếu bạn muốn, bước tiếp theo mình có thể bổ sung sơ đồ tuần tự "sequence" bằng Mermaid cho toàn bộ luồng: giao diện -> API -> graph -> tools -> phản hồi.

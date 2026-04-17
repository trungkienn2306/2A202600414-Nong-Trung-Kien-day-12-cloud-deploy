# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: Nhóm 5A (AI chatbot Smart Travel)
- **Repo link**: https://github.com/trungkienn2306/Lab3-Chatbot.git (nhánh cong-main)
- **Team Members**:
  - Bùi Thế Công - 2A202600008
  - Nông Trung Kiên - 2A202600414
  - Trần Ngọc Huy - 2A202600298
- **Deployment Date**: 2026-04-06

---

## 1. Executive Summary

Chúng em xây dựng hệ thống "Smart Travel Assistant" theo kiến trúc "ReAct Agent" với framework LangGraph (code trình bày cụ thể trong `src`) để cung cấp, hỗ trợ cho user các thông tin về du lịch, kết hợp nhiều tool dữ liệu thời gian thực như thời tiết, tỷ giá, tìm kiếm thông tin về chuyến bay và khách sạn và kết hợp Human In The Loop để hỏi thêm các thông tin cá nhân liên quan đến user. Ngoài ra, hệ thống còn có thể trả lời các câu hỏi ngoài phạm vi du lịch bằng thông điệp guardrail.  

- **Success Rate**: 100% "HTTP success" ở bộ 5 test case đo lại (5/5 trả `200`), với 4 case nghiệp vụ du lịch + 1 case ngoài phạm vi đều xử lý đúng mục tiêu.
- **Key Outcome**: Agent trả được dữ liệu cụ thể từ tool ngoài (ví dụ tỷ giá `1 VND = 0.006087 JPY`; dữ liệu thời tiết Tokyo có nhiệt độ/độ ẩm/dự báo trong 5 ngày liên tiếp; thông tin giá cả, ngày, số lượng người của các phòng khách sạn tại một địa điểm; thông tin cụ thể về chuyến bay: `Đã tìm thấy các chuyến bay một chiều từ Hà Nội (HAN) đi Hồ Chí Minh (SGN) vào ngày 08/04/2026 cho 1 người lớn với chuyến bay rẻ nhất là của Bamboo Airways (QH 281) với giá 2.592.000 VND`) và từ chối được câu hỏi ngoài phạm vi du lịch bằng thông điệp guardrail (`I am not within my scope, please ask again` hoặc tương đương).

---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop Implementation

Luồng chính của hệ thống:

1. FE gửi `POST /chat` vào backend `src/api_main.py`.
2. Backend chuyển input vào graph `src/agent/graph.py`.
3. Node `agent` (LLM) quyết định:
   - trả lời trực tiếp, hoặc
   - gọi tool.
4. Nếu gọi tool:
   - chuyển sang node `tools`,
   - lấy "observation" và quay lại `agent`.
5. Nếu tool được gọi là `request_user` yêu cầu người dùng bổ sung dữ liệu:
   - graph chuyển trạng thái `human_review`,
   - API trả `status="need_input"` và `question`.


Kiến trúc giúp tách rõ phần suy luận ("reasoning"), phần hành động ("action"), và phản hồi môi trường ("observation").

### 2.2 Tool Definitions (Inventory)

| Tool Name | Input Format | Use Case |
| :--- | :--- | :--- |
| `get_weather` | `location: string` | Lấy thời tiết hiện tại + dự báo 5 ngày cho điểm đến du lịch. |
| `get_exchange_rate` | `from_currency: string, to_currency: string` | Quy đổi tỷ giá phục vụ ước tính chi phí chuyến đi. |
| `web_search` | `query: string, source: string, max_results: int` | Tìm thông tin phụ trợ (visa, điểm tham quan, quy định). |
| `calculator` | `expression: string` | Tính toán ngân sách/chuyển đổi chi phí một cách an toàn. |
| `search_flights_serpapi` | `origin, destination, depart_date, ...` | Tra cứu chuyến bay theo ngày/điểm đi-đến. |
| `search_hotels` | `location, check_in, check_out, ...` | Tra cứu khách sạn theo địa điểm và thời gian lưu trú. |
| `request_user` | `question: string` | Kích hoạt "human-in-the-loop" khi thiếu thông tin đầu vào. |

### 2.3 LLM Providers Used

- **Primary**: Gemini (`gemini-2.5-flash`) qua `langchain-google-genai`.
- **Secondary (Backup)**: OpenAI và Local provider có sẵn ở lớp `src/core/*` dưới dạng "provider interface", phục vụ mở rộng/chuyển đổi linh hoạt.

---

## 3. Telemetry & Performance Dashboard

Dựa trên lần chạy đo trực tiếp backend (file `tool result/group_report_metrics.json`) và đối chiếu với output tool trong `tool result/*.json`, chúng em ghi nhận:

- **Average Latency (P50)**: `2485.34 ms`
- **Max Latency (P99 trong mẫu 5 case)**: `3739.51 ms`
- **Min Latency**: `1873.65 ms`
- **Average Tokens per Task**: chưa có số cứng trong route hiện tại do chưa bật cơ chế ghi usage token đồng nhất ở tầng API.
- **Total Cost of Test Suite**: chưa có số cứng do chưa gắn "cost meter" theo provider trong endpoint production hiện tại.

Số liệu có bằng chứng:

- `tool result/group_report_metrics.json` (bảng đo độ trễ và trạng thái 5 case)
- `tool result/weather_result.json` (thời tiết)
- `tool result/search_result.json` (tìm kiếm)
- `tool result/backend_testcases_report.md` (kết quả test case pass/fail)

Ví dụ dữ liệu cụ thể đã thu được:

- Case tỷ giá (`TC03`): phản hồi `"Tỷ giá hiện tại là 1 VND = 0.006087 JPY."`, độ trễ `3000.88 ms`.
- Case thời tiết (`TC04`): phản hồi thời tiết Tokyo + dự báo 5 ngày, độ trễ `3739.51 ms`.
- Case ngoài phạm vi (`TC05`): phản hồi từ chối đúng nghiệp vụ du lịch, độ trễ `2485.34 ms`.

Đánh giá thực tế:

- Mục tiêu "quality evidence" đã đạt ở mức log nghiệp vụ và output tool.
- Mục "cost/token dashboard" là phần cần bổ sung để đạt điểm cao hơn ở nhóm chỉ số đánh giá.

---

## 4. Root Cause Analysis (RCA) - Failure Traces

### Case Study: Lệch contract `need_input` ở prompt mơ hồ

- **Input**: "Tư vấn lịch trình du lịch cho tôi"
- **Observation**:
  - Ở bộ test ban đầu (`tool result/backend_testcases_report.md`), case `TC02_NEED_INPUT_EXPECTED` nhận `status="success"` dù nội dung đang hỏi thêm thông tin.
  - Điều này gây khó cho FE nếu FE chỉ dựa vào field `status/question` để điều khiển UX.
- **Root Cause**:
  - Luồng "human-in-the-loop" có hoạt động về mặt nội dung, nhưng mapping contract response chưa nhất quán ở lớp API adapter theo trạng thái graph.
- **Solution**:
  - Chuẩn hóa hợp đồng phản hồi theo `response/thread_id/status/question` ở tầng API adapter.
  - Bổ sung test có đo định lượng (`group_report_metrics.json`) và giữ case cũ để so sánh hồi quy.
  - Dùng `thread_id` nhất quán để FE vẫn resume đúng ngữ cảnh kể cả khi status chưa tối ưu ở một số prompt.

### Case Study: Agent trả lời ngoài phạm vi du lịch

- **Input**: "Giải thích quicksort và code Python"
- **Observation**:
  - Trước khi thêm guardrail cứng, model có thể trả lời nội dung ngoài phạm vi du lịch.
- **Root Cause**:
  - Chỉ dùng prompt mềm ở tầng model, chưa có "hard guard" tại API.
- **Solution**:
  - Thêm guard "out-of-scope" ở API, từ chối ngắn gọn và mời quay lại chủ đề du lịch.
  - Sau fix, các case ngoài phạm vi được chặn ổn định.

---

## 5. Ablation Studies & Experiments

### Experiment 1: Trước và sau khi thêm "out-of-scope guard" ở API

- **Diff**:
  - Trước: chỉ có chỉ dẫn trong "system prompt".
  - Sau: thêm kiểm soát cứng ở API trước khi vào graph.
- **Result**:
  - Trường hợp `"Hay giai thich thuat toan quicksort va code python"` chuyển sang phản hồi từ chối theo phạm vi du lịch.
  - Tăng độ ổn định cho demo FE-BE vì không còn phụ thuộc hoàn toàn vào "prompt obedience".

### Experiment 2: "Chatbot" vs "Agent"

| Case | Chatbot Result | Agent Result | Winner |
| :--- | :--- | :--- | :--- |
| Câu hỏi đơn giản (chào hỏi, hỏi chung) | Đúng | Đúng | **Chatbot** ( vì tối ưu chi phí và thời gian hơn) |
| Câu hỏi cần dữ liệu thời gian thực (thời tiết/tỷ giá) | Dễ "hallucination" hoặc trả về số liệu trong quá khứ | Gọi tool và trả số liệu cụ thể theo thời gian thực | **Agent** |
| Câu hỏi cần làm rõ thông tin đầu vào | Trả lời đoán hoặc mơ hồ | Có cơ chế hỏi ngược qua `request_user` (khi graph đi vào `human_review`) | **Agent** |
| Câu hỏi ngoài phạm vi du lịch | Có thể trả lời lan man | Được chặn bằng guardrail | **Agent** |

---

## 6. Production Readiness Review

- **Security**:
  - Đầu vào tool được kiểm tra kiểu dữ liệu và giới hạn định dạng.
  - Hàm tính toán dùng cơ chế AST an toàn thay vì "eval" trực tiếp.

- **Guardrails**:
  - Có kiểm soát "out-of-scope" ở API.
  - Có luồng "human-in-the-loop" khi thiếu dữ liệu thay vì suy đoán.
  - Có giới hạn vòng lặp reasoning qua cấu trúc graph và checkpoint.

- **Scaling**:
  - Kiến trúc hiện tại tách được FE-BE, thuận tiện mở rộng dịch vụ.
  - Hướng nâng cấp tiếp theo:
    - chuẩn hóa telemetry "token/latency/cost",
    - tối ưu prompt và phát triển thêm các tools cần thiết khác liên quan
    - bổ sung lớp lưu trữ log theo phiên,
    - mở rộng "vector database" cho "tool retrieval" trong hệ "many-tool".


---

> [!NOTE]
> Báo cáo nhóm này được viết theo trạng thái repo và dữ liệu test hiện có, ưu tiên trung thực kỹ thuật, có nêu rõ điểm mạnh, điểm thiếu và kế hoạch cải tiến để đạt mức "production-grade" cao hơn.

# Phân tích `src/` hiện tại so với yêu cầu Lab 4

Tài liệu này đối chiếu backend hiện tại trong `src/` với đề bài trong `LAB4.md`, theo 4 lớp:

1. Tổng quát logic backend AI chatbot hiện tại.
2. Tổng quát mục tiêu Lab 4.
3. So sánh tổng quát Lab 4 và hệ thống hiện tại.
4. So sánh chi tiết theo từng yêu cầu và mức độ đạt được.

Mục tiêu cuối cùng: xác định cần làm gì để đạt đủ yêu cầu tối thiểu của Lab 4 trước, sau đó mới tối ưu phần điểm cộng "extra".

---

## 1) Tổng quát logic backend AI chatbot hiện tại (`src/`)

### 1.1 Kiến trúc backend

- `src/api_main.py`: API FastAPI (`/health`, `/chat`) và CORS.
- `src/agent/graph.py`: đồ thị LangGraph với các node `agent`, `tools`, `human_review`.
- `src/agent/nodes.py`: khởi tạo model Gemini, gắn công cụ, gọi model.
- `src/agent/tools.py`: bộ công cụ thực tế (thời tiết, tỷ giá, tìm kiếm, tính toán, chuyến bay SerpApi, khách sạn SerpApi, `request_user`).
- `src/agent/state.py`: định nghĩa trạng thái chứa `messages`.

### 1.2 Luồng xử lý backend

1. Giao diện gọi `POST /chat`.
2. Backend tạo hoặc nhận `thread_id`, đọc trạng thái từ checkpointer SQLite.
3. Graph chạy node `agent`.
4. Nếu model tạo tool call thì chuyển sang node `tools`.
5. Nếu tool là `request_user` thì graph dừng tại điểm chờ, API trả `status=need_input`.
6. Người dùng trả lời tiếp, API cập nhật trạng thái rồi graph chạy tiếp.
7. API lấy message AI cuối cùng và trả về giao diện.

### 1.3 Điểm mạnh hiện tại

- Đã có vòng lặp LangGraph và cơ chế gọi công cụ thực tế.
- Đã có luồng hỏi lại người dùng "human-in-the-loop".
- Đã có checkpointer SQLite theo `thread_id`.
- Đã có CORS theo danh sách cho phép từ biến môi trường.
- Đã tách lớp API và lớp agent tương đối rõ.

### 1.4 Giới hạn hiện tại

- System prompt hiện tại chưa theo đúng cấu trúc XML của Lab 4.
- Bộ công cụ chưa trùng bộ 3 công cụ cốt lõi Lab 4.
- Mục tiêu công cụ hiện tại thiên về dữ liệu thực tế, chưa bám mock data bắt buộc của đề.

---

## 2) Tổng quát yêu cầu Lab 4 (`LAB4.md`)

Lab 4 yêu cầu một mini-project TravelBuddy với khung khá cụ thể.

### 2.1 Ý tưởng cốt lõi

- Agent phải kết hợp nhiều nguồn để tư vấn chuyến đi.
- Trọng tâm là chuỗi 3 bước:
  1. tìm chuyến bay;
  2. tìm khách sạn;
  3. tính ngân sách còn lại.

### 2.2 Deliverable bắt buộc theo đề

- `system_prompt.txt` (prompt XML có rules/constraints/response format).
- `tools.py` với 3 tool:
  - `search_flights`
  - `search_hotels`
  - `calculate_budget`
- `agent.py` có vòng lặp LangGraph hoàn chỉnh.
- `test_results.md` chứa kết quả 5 test case.

### 2.3 Rubric chính

- Thiết lập LangGraph đúng: 25%.
- Logic công cụ + xử lý lỗi đúng: 25%.
- Prompt và guardrail đúng: 20%.
- Chuỗi nhiều bước thành công (Test 3): 20%.
- Mã sạch, type hints, logging rõ: 10%.

---

## 3) So sánh tổng quát: Lab 4 và backend hiện tại

### 3.1 Nhận xét cấp cao

Backend hiện tại vượt mức khung cơ bản ở nhiều điểm (API tương đối hoàn chỉnh, CORS theo env, checkpointer, luồng hỏi lại người dùng).  
Tuy nhiên, nếu chấm sát rubric Lab 4 thì hệ thống hiện tại chưa khớp trực tiếp đề vì:

- khác bộ tool cốt lõi;
- khác format prompt yêu cầu;
- chưa có đúng bộ deliverable theo tên và nội dung của đề.

### 3.2 Mức độ đạt tổng quát theo đề

- Yêu cầu kiến trúc LangGraph: đạt tốt.
- Yêu cầu tool đúng theo đề: chưa đạt đầy đủ.
- Yêu cầu prompt đúng form đề: chưa đạt đầy đủ.
- Yêu cầu test result chuẩn đề: chưa có tệp kết quả đúng mẫu.

Kết luận: hệ thống hiện tại mạnh về kỹ thuật tổng quát, nhưng lệch định dạng triển khai cần nộp của Lab 4.

---

## 4) So sánh chi tiết theo từng nhóm yêu cầu

### 4.1 Phần 0 - Setup API

#### Yêu cầu Lab 4

- Có bước kiểm tra model OpenAI (`gpt-4o-mini`) bằng `test_api.py`.

#### Hiện tại (`src/`)

- Backend đang dùng Gemini qua `ChatGoogleGenerativeAI`.
- Có endpoint `/health` và luồng chat API đầy đủ.

#### Đánh giá

- Nếu bám sát mẫu nộp Lab 4: chưa đúng setup mẫu.
- Nếu xét năng lực hệ thống: đã chạy tốt.

### 4.2 Phần 1 - System Prompt

#### Yêu cầu Lab 4

- Prompt XML gồm `persona`, `rules`, `tools_instruction`, `response_format`, `constraints`.
- Có guardrail từ chối yêu cầu ngoài phạm vi du lịch.

#### Hiện tại

- Prompt nằm trong `src/agent/nodes.py`, dạng chuỗi tự do, không phải XML.
- Có hướng dẫn dùng `request_user` và phong cách trả lời.
- Chưa ép định dạng đầu ra đúng mẫu của đề.

#### Đánh giá

- Đạt một phần về điều hướng hành vi.
- Chưa đạt yêu cầu định dạng và guardrail theo mẫu đề.

### 4.3 Phần 2 - Custom Tools

#### Yêu cầu Lab 4

Bộ 3 tool bắt buộc:

1. `search_flights(origin, destination)` với lookup tuple và thử chiều ngược.
2. `search_hotels(city, max_price_per_night)` có lọc giá và sắp xếp theo rating.
3. `calculate_budget(total_budget, expenses)` có parse chuỗi và xử lý lỗi format.

#### Hiện tại

`src/agent/tools.py` đang có bộ công cụ:

- `get_weather`
- `get_exchange_rate`
- `web_search`
- `calculator`
- `search_flights_serpapi`
- `search_hotels` (Google Hotels)
- `request_user`

#### Đánh giá

- Công cụ hiện tại mạnh và có tính thực tế cao.
- Nhưng chưa khớp đúng bộ 3 tool cần nộp theo Lab 4.

### 4.4 Phần 3 - LangGraph

#### Yêu cầu Lab 4

- Có node agent + node tool + các cạnh:
  - `START -> agent`
  - `agent -> tools/END`
  - `tools -> agent`

#### Hiện tại

- Đã có graph đầy đủ:
  - `START -> agent`
  - `agent -> tools/END` qua `should_continue`
  - `tools -> human_review/agent`
  - `human_review -> agent`
- Có thêm interrupt và checkpointer.

#### Đánh giá

- Đạt và vượt yêu cầu phần graph cơ bản.

### 4.5 Phần 4 - Test cases

#### Yêu cầu Lab 4

- Chạy đủ 5 test case theo đề.
- Có bằng chứng trong `test_results.md`.

#### Hiện tại

- Chưa có `test_results.md` theo mẫu Lab 4.
- Có thể test API được, nhưng chưa đóng gói đúng theo bộ test của đề.

#### Đánh giá

- Chưa đạt phần deliverable kiểm thử.

### 4.6 Phần 5 - Deliverables

#### Yêu cầu Lab 4

Phải nộp:

- `system_prompt.txt`
- `tools.py`
- `agent.py`
- `test_results.md`

#### Hiện tại

- Hệ thống tổ chức theo `src/` theo hướng ứng dụng nhiều module.
- Chưa có bộ file đúng form nộp Lab 4 theo mẫu.

#### Đánh giá

- Chưa đạt định dạng nộp bài theo rubric.

---

## 5) Backend hiện tại làm được gì và đạt bao nhiêu so với Lab 4

Lưu ý: tỷ lệ dưới đây là ước lượng kỹ thuật để ưu tiên công việc, không phải điểm chấm chính thức.

### 5.1 Nhóm đã làm tốt

- API chat có trạng thái theo phiên và health endpoint.
- LangGraph loop có tool calling.
- Có luồng hỏi lại người dùng.
- Có bộ tool đa dạng với dữ liệu thực tế.
- Có CORS theo env và readiness check.

### 5.2 Nhóm chưa khớp đề

- Chưa có đúng bộ 3 tool mock bắt buộc.
- Chưa có prompt XML đúng mẫu Lab 4.
- Chưa ép format đầu ra đúng mẫu TravelBuddy.
- Chưa có `test_results.md` theo 5 test của đề.
- Chưa đóng gói deliverable theo định dạng bài nộp.

### 5.3 Ước lượng mức đạt theo rubric

- LangGraph setup (25%): khoảng 22-25/25.
- Tool logic theo đề (25%): khoảng 8-12/25.
- System prompt + guardrail (20%): khoảng 8-12/20.
- Multi-step đúng test đề (20%): khoảng 8-12/20.
- Code sạch/type hints/logging (10%): khoảng 6-8/10.

Tổng ước lượng: khoảng 52%-69%, tùy mức giảng viên chấp nhận phần mở rộng ngoài đề.

---

## 6) Kế hoạch để đạt đủ yêu cầu tối thiểu Lab 4 trước

### 6.1 Ưu tiên P0 (bắt buộc)

1. Tạo đủ bộ file nộp bài:
   - `system_prompt.txt`
   - `tools.py`
   - `agent.py`
   - `test_results.md`
2. Viết đúng 3 tool theo đề:
   - `search_flights`
   - `search_hotels`
   - `calculate_budget`
3. Đồng bộ prompt theo XML và guardrail.
4. Đảm bảo agent chạy được chuỗi Test 3 đúng mô tả đề.
5. Chạy đủ 5 test case và ghi log vào `test_results.md`.

Mục tiêu của P0 là đạt đủ yêu cầu tối thiểu để chấm đúng rubric.

### 6.2 Ưu tiên P1 (ổn định sau khi đã đạt bài)

- Nâng chất lượng xử lý lỗi.
- Chuẩn hóa logging rõ ràng hơn.
- Bổ sung type hints đầy đủ hơn.
- Thêm script kiểm thử bán tự động nếu còn thời gian.

### 6.3 Ưu tiên P2 (điểm cộng "extra", làm sau cùng)

- Giữ nhánh `src/` hiện tại như hướng sản phẩm thực tế.
- Mở rộng tool dữ liệu thời gian thực.
- Tích hợp telemetry sâu hơn.
- Tối ưu CORS và bảo mật theo môi trường triển khai.

---

## 7) Kết luận và khuyến nghị hành động

1. `src/` hiện tại là nền backend tốt cho hệ thống thực tế.
2. Để đạt điểm Lab 4 theo rubric, cần căn chỉnh lại đúng đề, đặc biệt ở bộ 3 tool, prompt XML và deliverable.
3. Chiến lược phù hợp:
   - làm bản "đạt chuẩn Lab 4 tối thiểu" trước;
   - sau đó mới đưa năng lực mở rộng để lấy điểm cộng.

---

## 8) Checklist thực thi nhanh

- [ ] Tạo `system_prompt.txt` theo XML.
- [ ] Tạo `tools.py` đúng 3 tool của đề.
- [ ] Tạo `agent.py` đúng vòng lặp LangGraph theo đề.
- [ ] Chạy Test 1-5 và ghi `test_results.md`.
- [ ] Tự rà lại theo rubric 25/25/20/20/10.
- [ ] Sau khi đạt tối thiểu mới triển khai phần mở rộng.


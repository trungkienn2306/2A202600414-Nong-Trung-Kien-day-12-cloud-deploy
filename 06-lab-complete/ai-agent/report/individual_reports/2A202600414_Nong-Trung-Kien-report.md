# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nong Trung Kien
- **Student ID**: 2A202600414
- **Date**: 2026-04-06

---

## I. Technical Contribution (15 Points)

Trong Lab 3, em tập trung vào phần tích hợp hệ thống, "vibe coding" UI/UX, ghép frontend với backend agent, và xử lý vấn đề nhánh Git để đảm bảo nhóm có thể demo ổn định trên localhost.

- **Modules Implementated**:
  - `frontend/` (thiết kế và tổ chức lại giao diện người dùng theo trải nghiệm một luồng chat)
  - `frontend/src/hooks/useTravelChat.ts` (luồng gửi nhận chat, xử lý trạng thái hiển thị)
  - `frontend/src/lib/chatApi.ts` (kết nối API backend, chuẩn hóa request/response)
  - `src/api_main.py` (ghép contract backend phục vụ frontend và bổ sung guardrail)
  - `.gitignore` và thao tác Git branch/repo hygiene (loại file thư viện khỏi commit)

- **Code Highlights**:
  1. Thiết kế lại FE theo hướng "single chat thread", tập trung trải nghiệm người dùng khi hỏi đáp liên tục.
  2. Ghép FE với backend `src` theo contract `response/thread_id/status/question` để hỗ trợ flow "human-in-the-loop".
  3. Bổ sung xử lý lỗi tích hợp thực tế: CORS, port conflict, nhầm endpoint (`/chat` vs `/api/chat`), và lỗi do process backend cũ.
  4. Dọn conflict nhánh `Cong` và `cong`, chuẩn hóa nhánh làm việc `cong-main`, giảm rủi ro sai lệch lịch sử commit.

- **Documentation**:
  - Em không trực tiếp viết logic lõi AI agent, nhưng đã đọc và hiểu kiến trúc ở `src/agent/*`, nắm được luồng `"tool-calling"` và `"need_input"`, sau đó nối đúng backend vào FE để hệ thống chạy được end-to-end.
  - Vai trò chính của em là "integration engineer": làm cầu nối giữa UI/UX và logic agent.

---

## II. Debugging Case Study (10 Points)

- **Problem Description**:
  1. FE báo lỗi `404` khi gọi chat endpoint.
  2. Có lúc chatbot trả lời ngoài phạm vi du lịch (ví dụ câu hỏi về "quicksort").
  3. Repo có commit rác (hàng nghìn file thư viện) do thiếu rule ignore.

- **Log Source**:
  - Console FE: log từ `chatApi`/`useTravelChat` cho thấy endpoint sai hoặc backend instance cũ.
  - Kết quả test backend được lưu ở `tool result/backend_testcases_report.md`.
  - Traces tool output trong `tool result/*.json` (weather, exchange, search).

- **Diagnosis**:
  1. `404` phát sinh do mismatch contract và tồn tại nhiều backend process cũ trên cùng cổng.
  2. Out-of-scope xảy ra vì chỉ dựa vào prompt mềm, chưa có guard cứng tại tầng API.
  3. Git chứa file thư viện vì `.gitignore` chưa bao phủ `node_modules`, cache build và artifact frontend.

- **Solution**:
  1. Chuẩn hóa endpoint FE-BE theo contract `src`.
  2. Bổ sung hard guard out-of-scope ở API để từ chối câu hỏi ngoài du lịch theo phản hồi ngắn gọn.
  3. Bổ sung `.gitignore`, reset commit rác, và dọn nhánh để ổn định quy trình làm việc nhóm.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**:
   - "Chatbot" thường trả lời trực tiếp theo ngữ cảnh text.
   - "ReAct Agent" có khả năng quyết định dùng "tool", lấy dữ liệu thật và phản hồi theo từng bước nên phù hợp bài toán du lịch thực tế hơn.

2. **Reliability**:
   - Agent có thể tệ hơn chatbot khi cấu hình thiếu key, tool timeout, hoặc mapping endpoint sai.
   - Nếu không có guardrail, agent cũng có thể trả lời ngoài phạm vi nghiệp vụ.

3. **Observation**:
   - Tín hiệu "observation" từ tool ảnh hưởng trực tiếp tới bước kế tiếp của agent.
   - Khi log đầy đủ, việc sửa lỗi nhanh hơn nhiều vì nhìn được đúng điểm hỏng trong chuỗi suy luận-thực thi.

4. **Tự kiểm điểm cá nhân**:
   - Em đã thiết kế hệ thống theo hướng DB "vector" và frontend quá lớn ngay từ giai đoạn đầu, khiến việc nối FE với logic AI chatbot không suôn sẻ.
   - Bài học rút ra là cần ưu tiên làm ổn định logic core trước ("core-first"), sau đó mới mở rộng scale với DB "vector" và các thành phần nâng cao.

---

## IV. Future Improvements (5 Points)

- **Scalability**:
  - Đã chuẩn bị tư duy thiết kế DB để scale và lưu trữ log/trace theo phiên làm việc.
  - Tách lớp telemetry riêng để phục vụ thống kê "token", "latency", "loop count" theo chuẩn đánh giá.

- **Safety**:
  - Tăng cường "policy guardrail" cho out-of-scope và kiểm tra input trước khi đi vào graph.
  - Bổ sung cơ chế "fallback" khi external API lỗi để tránh crash luồng demo.

- **Performance**:
  - Chuẩn bị hướng dùng "vector database" cho "tool retrieval" trong hệ thống nhiều công cụ ("many-tool system").
  - Kết hợp cache theo intent/tool để giảm số lần gọi API ngoài và giảm độ trễ tổng.

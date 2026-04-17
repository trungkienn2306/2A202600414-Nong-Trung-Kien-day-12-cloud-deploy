# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Trần Ngọc Huy 
- **Student ID**: 2A202600298
- **Date**: 6/4/2026

---

## I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.).*

- **Modules Implementated**: `src/agent/tools.py`; `tool result/`
- **Code Highlights**: `src/agent/tools.py`
- **Documentation**: Hệ thống công cụ (Tools) này đóng vai trò là "cánh tay thực thi" giúp Agent thoát khỏi giới hạn dữ liệu cũ của LLM. Nó cung cấp các Observation (quan sát) chính xác từ API thực tế (thời tiết, chuyến bay, tỷ giá), giúp triệt tiêu hiện tượng ảo giác và cho phép Agent thực hiện các chuỗi suy luận ReAct đa bước phức tạp.

---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

- **Problem Description**: Agent cố gắng thực hiện hành động "Đặt vé" (booking) thay vì chỉ "Tìm kiếm" (searching) khi người dùng yêu cầu: "Đặt cho tôi phòng khách sạn rẻ nhất ở Đà Lạt".
- **Log Source**: `logs/2026-04-06.log` - `{"event": "tool_error", "data": {"tool": "book_hotel", "error": "Tool 'book_hotel' not found."}}`
- **Diagnosis**: Do Domain của Agent là về Du lịch, LLM đôi khi bị "quá nhiệt tình" và giả định rằng nó có quyền thực thi các tác vụ thanh toán/đặt chỗ (Transactional). Điều này dẫn đến việc nó tự sáng tạo ra (hallucinate) tên công cụ `book_hotel` hoặc `confirm_reservation` không hề có trong danh sách được định nghĩa.
- **Solution**: Bổ sung "Negative Constraints" vào System Prompt: Nhấn mạnh Agent chỉ là một "Travel Consultant" (Tư vấn viên), tuyệt đối không có khả năng thực hiện đặt vé hay giao dịch tài chính. Nếu người dùng yêu cầu đặt vé, Agent phải trả lời là chỉ có thể cung cấp thông tin so sánh giá và yêu cầu người dùng tự thực hiện bước tiếp theo trên website.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1.  **Reasoning**: Khối `Thought` đóng vai trò là "bản nháp tư duy". Nó ép Agent phải lập kế hoạch (Plan) trước khi hành động. Ví dụ, khi được hỏi về chuyến bay và quy đổi tiền tệ, Agent sẽ "nghĩ" về việc lấy giá vé trước, sau đó mới lấy tỷ giá. Chatbot thông thường thường bỏ qua bước trung gian này và dễ dẫn đến trả về dữ liệu cũ hoặc hallucination.
2.  **Reliability**: Agent có xác suất lỗi cao hơn ở các câu hỏi đơn giản (về kiến thức phổ thông) do quy trình ReAct rườm rà và tốn token. Ngược lại, với các tác vụ yêu cầu dữ liệu thời gian thực (real-time), Agent vượt trội hoàn toàn về độ tin cậy nhờ kết nối trực tiếp với API Weather/SerpApi.
3.  **Observation**: Kết quả trả về từ môi trường (Observation) là "mỏ neo" thực tế. Nếu API trả về rỗng, Agent sẽ tự điều chỉnh truy vấn (Prompt Engineering nội bộ) để tìm kiếm lại. Đây là khả năng tự phục hồi (self-healing) mà Chatbot truyền thống không có.

---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

- **Scalability**: Triển khai gọi Tool không đồng bộ (`asyncio`) để thực hiện song song các task độc lập (ví dụ: vừa tìm khách sạn vừa tìm chuyến bay) nhằm giảm đáng kể tổng Latency (P99).
- **Safety**: Sử dụng `Pydantic` để kiểm tra kiểu dữ liệu đầu vào (Schema validation) cho Tool. Ngăn chặn Agent truyền tham số sai định dạng hoặc inject mã độc vào biểu thức calculator.
- **Performance**: Tích hợp cơ chế Caching (như Redis) cho các kết quả API có tần suất truy cập cao (weather, exchange rate) để tiết kiệm chi phí API và giảm thời gian phản hồi xuống dưới 200ms cho các dữ liệu đã biết.



# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Repo link**: https://github.com/trungkienn2306/Lab3-Chatbot.git (nhánh cong-main)
- **Student Name**: Bùi Thế Công
- **Student ID**: 2A202600008
- **Date**: 6/4/2026

---

## I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.).*

- **Modules Implementated**: `src/agent/nodes.py`, `src/agent/graph.py`, `src/agent/state`, `src/app.py`, `src/core/logger.py`, `src/api_main.py`
- **Code Highlights**: `src/agent/nodes.py`, `src/agent/graph.py`, `src/agent/state`, `src/api_main.py`
- **Documentation**: 
Các module cốt lõi được xây dựng đóng vai trò điều phối toàn bộ vòng lặp ReAct của hệ thống:
  - **`state.py`**: Định nghĩa `AgentState` để giữ context (danh sách tin nhắn) xuyên suốt vòng lặp.
  - **`nodes.py`**: Xử lý pha **Reason** (`call_model` nhận input, gọi LLM suy luận ra danh sách công cụ cần gọi hoặc trả lời trực tiếp) và pha **Act/Observe** (`LoggedToolNode` thực thi công cụ thật và trả về `ToolMessage` làm Observation để LLM dựa vào đó suy luận tiếp).
  - **`graph.py`**: Định nghĩa cấu trúc đồ thị luồng chạy (StateGraph). Quyết định bộ định tuyến (conditional edges) như: LLM có gọi tool không (quấn qua `tools`), tool đó có phải là yêu cầu hỏi người dùng không (chuyển sang `human_review`), hay đã đủ thông tin trả lời (kết thúc vòng lặp).
  - **`api_main.py`**: Môi trường kích hoạt và duy trì vòng lặp. Xử lý logic ngắt quãng (interrupt) khi luồng ReAct cần lấy thêm thông tin từ người dùng, sau đó nối lại (`resume`) vòng lặp bằng cách truyền câu trả lời của người dùng vào state.

---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

- **Problem Description**: LLM gọi tool tìm kiếm (`search_web_info`) nhưng tool bị định nghĩa sai (lỗi `tavily is not defined` / thiếu thư viện cấu hình). Hậu quả là thay vì dừng lại ngay (crash hệ thống), ReAct Node trả về lỗi dạng text cho LLM. LLM nhận lỗi nhưng mất phương hướng, báo cho user là đang có lỗi kỹ thuật và hỏi user thông tin khác.
- **Log Source**: Trích xuất từ file `logs/agent_trace.log`. Log: `[LLM] step=call_model | latency=1395ms | tokens(in/out/total)=2190/83/2273 | tools_called=['search_web_info']
{"type": "tool", "tool_name": "search_web_info", "tool_input": {"query": "thời tiết Hà Nội hôm nay", "thought": "Tìm kiếm thời tiết hiện tại ở Hà Nội"}, "tool_output": "Error searching Tavily: name 'tavily' is not defined", "latency_ms": 0, "timestamp": "2026-04-06T15:46:01.143739+00:00"}
[TOOL] search_web_info | latency=0ms | output_preview=Error searching Tavily: name 'tavily' is not defined`
- **Diagnosis**: Về mặt Node/Tool Execution: Hàm search_web_info thiếu biến global tavily vì biến này bị comment hoặc chưa được import đúng cách. Về LLM: Khi công cụ trả về content="Error searching Tavily: name 'tavily' is not defined", model Gemini vẫn xử lý nó như một kết quả quan sát bình thường. Do Prompt không được train cách fix lỗi hoặc không có Fallback Tool, LLM đành đóng context lại bằng một câu trả lời trống hoặc bị "hallucinate".
- **Solution**: Khắc phục lỗi Syntax: đã sửa nhánh import config thành from src.core.config import settings và khởi tạo lại tavily = TavilyClient(api_key=settings.TAVILY_API_KEY). 

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1.  **Reasoning**: 
 - **Phân tách suy luận và hành động**: Thay vì vội vã đưa ra câu trả lời (dễ gây hallucination), thông qua `Thought`, Agent tự "phân tích" yêu cầu của người dùng trước. Ví dụ: *"Người dùng cần tìm chuyến bay ở Tokyo -> LLM cần hỏi thêm các thông tin liên quan về thời gian bay, địa điểm đi, loại vé 1 chiều/khứ hồi, đặt vé cho mấy người,... -> Sau đó gọi tool `search_flights`"*.
   - **Tối ưu định tuyến**: Quá trình suy luận này giúp LLM chọn đích xác tool nào cần gọi và tham số truyền vào là gì, giúp câu trả lời mang tính hệ thống, có căn cứ và giải quyết được các bài toán phức tạp gồm nhiều bước (multi-step tasks).
2.  **Reliability**: 
  - **Chậm trễ (Latency) trong giao tiếp cơ bản**: Với những câu giao tiếp nhỏ hẹp, đơn giản, luồng ReAct Agent vẫn phải đi qua các node kiểm tra tool, khiến thời gian phản hồi bị kéo dài so với Chatbot thuần túy có thể phản hồi tức thì.
   - **Phụ thuộc quá lớn vào Tool/API ngoài**: Agent dễ bị tổn thương hơn nếu API bên thứ 3 (như Google Flights, Tavily) bị sập, rate-limit, hoặc thay đổi cấu trúc trả về. Khi tool bị lỗi (như lỗi thiếu `tavily` đã phân tích ở trên), Agent có thể bị bối rối, trong khi Chatbot thuần luôn duy trì được cuộc hội thoại mạch lạc dựa trên dữ liệu pre-train.
3.  **Observation**: 
 Observation chính là dữ liệu "thực" mà tool trả về (ví dụ: mảng JSON chứa giá vé máy bay hoặc nội dung Error text). Nhờ có observation này mà LLM biết được hành động trước đó của nó thành công hay thất bại.
   - Lấy ví dụ, nếu gọi tool `search_hotels` nhưng observation trả về `total_found: 0`, Agent sẽ sử dụng feedback này làm ngữ cảnh để tự sinh ra hành động tiếp theo: báo cáo cho người dùng không tìm thấy khách sạn và gợi ý họ đổi ngày, thay vì bịa ra một khách sạn ảo (điều mà Chatbot thường xuyên mắc phải).


---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

- **Scalability**: 
  - **Bất đồng bộ & Hàng đợi (Async & Message Queues)**: Chuyển đổi toàn bộ quá trình gọi Tool (đặc biệt là các API cào dữ liệu qua SerpApi vốn tốn nhiều thời gian) sang kiến trúc không đồng bộ (`async/await` với FastAPI) hoặc đẩy vào hàng đợi (RabbitMQ/Celery). Điều này giúp API Server không bị "treo" khi chặn các request đồng thời từ hàng ngàn user.
  - **Quản lý State tập trung**: Thay thế bộ nhớ tạm thời của LangGraph bằng hệ thống lưu trữ phân tán bền vững (ví dụ: Redis hoặc PostgreSQL) cho `checkpointer` để dễ dàng mở rộng nhiều instance server chạy song song mà không mất lịch sử chat.
- **Safety**:
  - **Kiến trúc Multi-Agent & Supervisor**: Bổ sung thêm một Agent đóng vai trò "Supervisor" hay "Guardrail" độc lập. LLM Giám sát này sẽ chạy ngầm để chặn các luồng tấn công Prompt Injection từ User, đồng thời "audit" (kiểm duyệt) các tham số trước khi gửi vào Tool (chặn việc đặt vé ảo bằng thẻ credit không hợp lệ) và lọc ngôn từ của câu trả lời trước khi trả về cho Client.
   - **Rate Limiting & Circuit Breaker**: Thiết lập giới hạn API (rate limit) ở mức hệ thống cho các tool trả phí, kèm cơ chế ngắt mạch (Circuit Breaker) để không đốt cạn ngân sách khi LLM rơi vào vòng lặp lỗi.
- **Performance**: 
  - **Vector DB (RAG)**: Hiện tại Agent đang được bind tĩnh toàn bộ danh sách tool vào context window. Khi dự án scale lên hàng trăm tools, việc này sẽ gây tốn kém token và làm LLM dễ bối rối. Giải pháp là lưu metadata của các tools vào Vector Database. Khi User hỏi, hệ thống sẽ Semantic Search để trích xuất và chỉ cấp quyền đúng 3-5 tools liên quan nhất (Dynamic Tool Binding).
  - **Caching System**: Cài đặt lớp Semantic Cache (như Redis) ở tầng ngoài cùng. Nếu người dùng hỏi các câu tương tự nhau (ví dụ: "Thời tiết Tokyo hôm nay"), hệ thống sẽ trả ngay kết quả từ Cache thay vì kích hoạt toàn bộ luồng ReAct cực kỳ tốn chi phí.
---



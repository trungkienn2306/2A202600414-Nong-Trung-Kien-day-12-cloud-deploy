import sys
import os
from dotenv import load_dotenv

load_dotenv()

# Pre-checks if API key exists. If not, exit gracefully to let user add it.
if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY").startswith("sk-proj-xxxx"):
    print("[CANH BAO] Cần cấu hình OPENAI_API_KEY thực trong file .env trước khi chạy test script!")
    sys.exit(1)

from agent import graph
class ConversationBufferWindowMemory:
    def __init__(self, k=3, return_messages=True):
        self.k = k
        self.messages = []
        
    def load_memory_variables(self, inputs):
        return {"history": self.messages[-(self.k * 2):] if self.k > 0 and self.messages else []}
        
    def save_context(self, inputs, outputs):
        self.messages.append(("human", inputs["input"]))
        self.messages.append(("ai", outputs["output"]))

def save_test_results_markdown():
    tests = [
        {
            "name": "Test 1 — Trả lời trực tiếp (không cần tool)",
            "query": "Xin chào! Tôi đang muốn đi du lịch nhưng chưa biết đi đâu.",
            "expected": "Agent chào hỏi, hỏi thêm sở thích/ngân sách/thời gian. Không gọi tool."
        },
        {
            "name": "Test 2 — Một lần gọi tool",
            "query": "Tìm giúp tôi chuyến bay từ Hà Nội đi Đà Nẵng",
            "expected": "Gọi search_flights('Hà Nội', 'Đà Nẵng'), liệt kê các chuyến bay."
        },
        {
            "name": "Test 3 — Chuỗi nhiều bước (multi-step tool chaining)",
            "query": "Tôi ở Hà Nội, muốn đi Phú Quốc 2 đêm, budget 5 triệu. Tư vấn giúp!",
            "expected": "Agent tự chuỗi: search_flights -> search_hotels -> calculate_budget, tổng hợp gợi ý."
        },
        {
            "name": "Test 4 — Thiếu thông tin / làm rõ",
            "query": "Tôi muốn đặt khách sạn",
            "expected": "Agent hỏi lại: thành phố, số đêm, ngân sách. Không gọi tool vội."
        },
        {
            "name": "Test 5 — Guardrail / từ chối",
            "query": "Giải giúp tôi bài tập lập trình Python về linked list",
            "expected": "Từ chối lịch sự, nêu rõ chỉ hỗ trợ du lịch."
        },
        {
            "name": "Test 6 — Xử lý lỗi Timeout khi trả lời quá lâu",
            "query": "[TEST TIMEOUT] Hãy đếm từ 1 đến 10 tỷ.",
            "expected": "Hệ thống phải ngắt phản hồi quá 45 giây và trả thông báo lỗi hệ thống."
        },
        {
            "name": "Test 7 — Xử lý Memory (k=3)",
            "query": [
                "Xin chào, tôi tên là Minh Khang.",
                "Tôi đang muốn tìm vé máy bay từ Hà Nội đi Đà Nẵng",
                "Quên mất, bạn còn nhớ tôi tên là gì và nãy giờ tôi đang tìm điểm đến nào không?"
            ],
            "expected": "Agent nhớ được tên Minh Khang và đang tìm đi Đà Nẵng (bộ nhớ ConversationBufferWindowMemory k=3)."
        }
    ]

    with open("test_results.md", "w", encoding="utf-8") as f:
        f.write("# KẾT QUẢ CHẠY TEST CHUYÊN ĐỀ LANGGRAPH (LAB 4)\n\n")
        f.write("> **Lưu ý:** Script này được chạy tự động để lưu lịch sử console output đẹp vào markdown.\n\n")
        
        for i, t in enumerate(tests, 1):
            f.write(f"## {t['name']}\n")
            f.write(f"**Question:** `{t['query']}`\n\n")
            f.write(f"**Expected behavior:** *{t['expected']}*\n\n")
            
            # Xử lý query: Test bình thường là chuỗi (string), còn Test 7 là mảng (list) để test đa turn
            queries = t['query'] if isinstance(t['query'], list) else [t['query']]
            test_memory = ConversationBufferWindowMemory(k=3, return_messages=True)
            
            for q_idx, query_str in enumerate(queries):
                # Print to stdout
                if len(queries) > 1:
                    print(f"\n--- [Lượt {q_idx + 1}/{len(queries)}] ---")
                print(f"Người dùng: {query_str}")
                
                import io
                
                old_stdout = sys.stdout
                new_stdout = io.StringIO()
                sys.stdout = new_stdout
                
                try:
                    import concurrent.futures
                    import time
                    
                    # Nạp trí nhớ
                    history = test_memory.load_memory_variables({})["history"]
                    messages_to_send = history + [("human", query_str)]
                    
                    # Hàm mô phỏng invoke
                    def call_graph(msg_query, msg_to_send):
                        # Nếu là test case timeout, cố tình ép hàm sleep 47 giây
                        if "[TEST TIMEOUT]" in msg_query:
                            time.sleep(47) 
                        return graph.invoke({"messages": msg_to_send})
                    
                    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
                    future = executor.submit(call_graph, query_str, messages_to_send)
                    try:
                        result = future.result(timeout=45)
                        final_response = result["messages"][-1].content
                        # Lưu trí nhớ
                        test_memory.save_context({"input": query_str}, {"output": final_response})
                    except concurrent.futures.TimeoutError:
                        final_response = "[LỖI TIMEOUT] Hệ thống tự động ngắt kết nối vì AI xử lý quá lâu (Vượt 45s định mức)."
                    finally:
                        executor.shutdown(wait=False, cancel_futures=True)
                except Exception as e:
                    final_response = f"Lỗi thực thi: {e}"
                finally:
                    sys.stdout = old_stdout
                
                log_output = new_stdout.getvalue()
                
                print(log_output)
                print(f"TravelBuddy: {final_response}")
                
                f.write(f"**Question:** `{query_str}`\n\n")
                f.write("**System Log (Từ LangGraph Tool Calling):**\n")
                f.write("```text\n")
                f.write(log_output.strip() + "\n")
                f.write("```\n\n")
                
                f.write("**Agent Response:**\n")
                f.write("```text\n")
                f.write(final_response + "\n")
                f.write("```\n\n")
                
            f.write("---\n\n")
    
    print("[THANH CONG] Đã chạy test và ghi kết quả vào file test_results.md!")

if __name__ == '__main__':
    save_test_results_markdown()

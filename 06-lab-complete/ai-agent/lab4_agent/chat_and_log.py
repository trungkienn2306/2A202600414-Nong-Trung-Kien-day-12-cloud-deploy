import sys
import io
from dotenv import load_dotenv

load_dotenv()

import concurrent.futures
import time
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

def start_interactive_session():
    print("=" * 60)
    print("CHẾ ĐỘ TƯƠNG TÁC LƯU LOG - TravelBuddy")
    print("Gõ 'quit' hoặc 'exit' để kết thúc và lưu xuất file")
    print("=" * 60)

    session_logs = []
    turn_count = 1
    
    # Cài đặt bộ nhớ 3 lượt gần nhất
    memory = ConversationBufferWindowMemory(k=3, return_messages=True)

    while True:
        try:
            user_input = input("\nBạn: ").strip()
            if user_input.lower() in ["quit", "exit", "q"]:
                break
                
            if not user_input:
                continue

            print("\nTravelBuddy đang suy nghĩ...", end="", flush=True)
            
            # Đổi stdout để bắt log của tools
            old_stdout = sys.stdout
            new_stdout = io.StringIO()
            sys.stdout = new_stdout
            
            try:
                start_total = time.time()
                
                # Nạp trí nhớ
                history = memory.load_memory_variables({})["history"]
                messages_to_send = history + [("human", user_input)]
                
                executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
                future = executor.submit(graph.invoke, {"messages": messages_to_send})
                try:
                    result = future.result(timeout=45)
                    final_response = result["messages"][-1].content
                    # Lưu trí nhớ
                    memory.save_context({"input": user_input}, {"output": final_response})
                except concurrent.futures.TimeoutError:
                    final_response = "[LỖI] Hệ thống phản hồi quá lâu (Timeout > 45s). Yêu cầu đã bị huỷ."
                finally:
                    executor.shutdown(wait=False, cancel_futures=True)
                    
                end_total = time.time()
                log_output = new_stdout.getvalue()
                log_output += f"\n[PROFILER] 🎯 TỔNG THỜI GIAN THEO LUỒNG (Từ lúc nhấn Enter đến lúc có câu trả lời): {end_total - start_total:.2f} giây"
            except Exception as e:
                final_response = f"Lỗi thực thi: {e}"
                log_output = new_stdout.getvalue()
            finally:
                sys.stdout = old_stdout # Trả lại stdout để in ra màn hình
            
            # In ra màn hình ngay lập tức cho người dùng thấy
            print(log_output)
            print(f"TravelBuddy: {final_response}")
            
            # Ghi nhớ lại vào bộ nhớ để lát xuất file
            session_logs.append({
                "turn": turn_count,
                "user": user_input,
                "system_log": log_output.strip(),
                "agent_response": final_response
            })
            turn_count += 1
            
        except KeyboardInterrupt:
            print("\nĐã ép thoát.")
            break

    # Lưu xuất file
    if session_logs:
        with open("test_results.md", "w", encoding="utf-8") as f:
            f.write("# KẾT QUẢ CHẠY TEST CHUYÊN ĐỀ LANGGRAPH (LAB 4)\n\n")
            f.write("> **Lưu ý:** Log được xuất tự động từ phiên tương tác thủ công.\n\n")
            
            for log in session_logs:
                f.write(f"## Lượt chat {log['turn']}\n")
                f.write(f"**Question:** `{log['user']}`\n\n")
                
                f.write("**System Log (Từ LangGraph Tool Calling):**\n")
                f.write("```text\n")
                f.write(log['system_log'] + "\n")
                f.write("```\n\n")
                
                f.write("**Agent Response:**\n")
                f.write("```text\n")
                f.write(log['agent_response'] + "\n")
                f.write("```\n\n")
                f.write("---\n\n")
                
        print("\nĐã lưu toàn bộ lịch sử thành công vào file `test_results.md`!")

if __name__ == '__main__':
    start_interactive_session()

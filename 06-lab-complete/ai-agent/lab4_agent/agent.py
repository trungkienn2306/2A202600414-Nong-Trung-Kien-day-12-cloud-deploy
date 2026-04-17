from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, ToolMessage
from tools import search_flights, search_hotels, calculate_budget
from dotenv import load_dotenv

load_dotenv()

# 1. Đọc System Prompt
with open("system_prompt.txt", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

# 2. Khai báo State
class AgentState(TypedDict):
    messages: Annotated[list[-1], add_messages]

# 3. Khởi tạo LLM và Tools
tools_list = [search_flights, search_hotels, calculate_budget]
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
llm_with_tools = llm.bind_tools(tools_list)

import time

# 4. Agent Node
def agent_node(state: AgentState):
    messages = state["messages"]
    
    # Nếu tin nhắn đầu chưa phải là System Message thì chèn vào
    if not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    start_llm = time.time()
    response = llm_with_tools.invoke(messages)
    end_llm = time.time()

    # === LOGGING CHO TERMINAL ===
    print(f"\n[PROFILER]  Thời gian chờ OpenAI API trả về: {end_llm - start_llm:.2f} giây")
    if response.tool_calls:
        import json
        for tc in response.tool_calls:
            args_formatted = json.dumps(tc['args'], ensure_ascii=False, indent=2)
            print(f"\n[SYSTEM LOG] GỌI TOOL: {tc['name']}")
            print(f"[SYSTEM LOG] THAM SỐ TRUYỀN VÀO:\n{args_formatted}")
    else:
        print("\n[SYSTEM LOG] TRẢ LỜI TRỰC TIẾP KẾT QUẢ TỚI NGƯỜI DÙNG (Không dùng Tool)")

    return {"messages": [response]}

# 5. Xây dựng Graph
builder = StateGraph(AgentState)
builder.add_node("agent", agent_node)

tool_node = ToolNode(tools_list)
builder.add_node("tools", tool_node)

# --- Khai báo edges ---
# Bắt đầu tại agent
builder.add_edge(START, "agent")
# Sau node agent, dùng điều kiện nếu có tool_calls thì rẽ nhánh tới "tools", ngược lại tới END
builder.add_conditional_edges("agent", tools_condition)
# Sau khi node tools xử lý kết quả xong, quay lại agent để suy luận tiếp
builder.add_edge("tools", "agent")

graph = builder.compile()

import concurrent.futures
class ConversationBufferWindowMemory:
    def __init__(self, k=3, return_messages=True):
        self.k = k
        self.messages = []
        
    def load_memory_variables(self, inputs):
        # Lấy tối đa k lượt (mỗi lượt 2 message) -> k*2 latest messages
        return {"history": self.messages[-(self.k * 2):] if self.k > 0 and self.messages else []}
        
    def save_context(self, inputs, outputs):
        self.messages.append(("human", inputs["input"]))
        self.messages.append(("ai", outputs["output"]))

# 6. Chat loop
if __name__ == "__main__":
    print("=" * 60)
    print("TravelBuddy - Trợ lý Du lịch Thông minh")
    print("Gõ 'quit' hoặc 'exit' để thoát")
    print("=" * 60)

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
            
            # Lấy lịch sử 3 lần chat gần nhất (6 messages)
            history = memory.load_memory_variables({})["history"]
            messages_to_send = history + [("human", user_input)]
            
            # Xử lý Timeout (ví dụ 45 giây) để tránh treo kịch bản
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            future = executor.submit(graph.invoke, {"messages": messages_to_send})
            try:
                result = future.result(timeout=45) # Giới hạn 45 giây
                final = result["messages"][-1]
                print(f"\nTravelBuddy: \n\n{final.content}")
                
                # Lưu lại cặp Hỏi-Đáp vào bộ nhớ để dùng cho lượt sau
                memory.save_context({"input": user_input}, {"output": final.content})
            except concurrent.futures.TimeoutError:
                print(f"\nTravelBuddy: \n\n[LỖI] Xin lỗi, hệ thống máy chủ AI đang phản hồi quá chậm (vượt quá 45 giây). Vui lòng thử lại sau!")
            finally:
                # Buông bỏ thread bị treo để hệ thống sẵn sàng nhận câu hỏi tiếp theo
                executor.shutdown(wait=False, cancel_futures=True)
                
        except KeyboardInterrupt:
            print("\nĐã thoát.")
            break
        except Exception as e:
            print(f"\n[Lỗi chương trình]: {e}")

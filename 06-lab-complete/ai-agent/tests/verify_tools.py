from src.agent.graph import app
from src.core.config import settings
from langchain_core.messages import HumanMessage
import uuid

def test_tool_toggle():
    # Test with current global setting
    print(f"--- Testing with USE_TOOLS={settings.USE_TOOLS} (from config) ---")
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    input_data = {
        "messages": [HumanMessage(content="What is the weather in Hanoi?")]
    }
    
    events = list(app.stream(input_data, config, stream_mode="values"))
    last_msg = events[-1]["messages"][-1]
    
    # Check for tool calls
    has_tool_calls = bool(getattr(last_msg, "tool_calls", []))
    print(f"Tool calls present: {has_tool_calls}")
    print(f"Response: {last_msg.content[:100]}...")

if __name__ == "__main__":
    test_tool_toggle()

if __name__ == "__main__":
    test_tool_toggle()

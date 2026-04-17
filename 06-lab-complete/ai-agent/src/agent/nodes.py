from src.agent.state import AgentState
from src.agent.tools import tools
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import ToolNode
import os
from dotenv import load_dotenv
from src.core.config import settings
from langchain_core.messages import SystemMessage


# Initialize the model with Tool Calling
# Initialize the base model
llm = ChatGoogleGenerativeAI(
    model=settings.MODEL_NAME, 
    google_api_key=settings.GEMINI_API_KEY,
    temperature=settings.TEMPERATURE
)


# Define the system instructions for the agent
SYSTEM_PROMPT = """You are a professional Smart Travel Assistant. 
Your mission is to support users with all information related to travel:
1. Suggest attractive destinations. If you don't know the user's preferences (e.g., mountains vs. beach), USE 'request_user' to ask.
2. Provide weather info (Use 'search').
3. Help with currency/costs (Use 'calculator' or 'search').
4. Provide travel tips, visa info, etc.

Rules:
- CRITICAL: If you are missing personal info to make a good recommendation (name, budget, companion, travel dates), you MUST call 'request_user' with a clear question.
- Always use the 'search' tool for real-time data.
- Maintain a friendly, professional tone. If the user provides info, acknowledge it and continue."""

def call_model(state: AgentState):
    """
    Node that calls the LLM with the current message history.
    It conditionally binds tools if settings.USE_TOOLS is True.
    """
    messages = state["messages"]
    
    # Prepend the system prompt if it's the beginning of the conversation
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    
    # Conditionally bind tools based on global settings
    if settings.USE_TOOLS:
        model = llm.bind_tools(tools)
    else:
        model = llm
        
    response = model.invoke(messages)
    # We return a list, which will be appended to the existing messages 
    return {"messages": [response]}

# ToolNode is a prebuilt node in LangGraph that handles tool execution
tool_node = ToolNode(tools)

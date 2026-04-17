from src.agent.state import AgentState
from src.agent.tools import tools
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode
import os
import logging
from src.core.config import settings
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)

def get_llm():
    """
    Factory function to get the LLM with fallback support.
    Gemini (Primary) -> OpenAI (Fallback)
    """
    # 1. Try Gemini
    if settings.GEMINI_API_KEY:
        try:
            return ChatGoogleGenerativeAI(
                model=settings.MODEL_NAME, 
                google_api_key=settings.GEMINI_API_KEY,
                temperature=settings.TEMPERATURE
            )
        except Exception as e:
            logger.warning(f"Failed to init Gemini: {e}. Trying fallback...")
            
    # 2. Try OpenAI fallback
    if settings.OPENAI_API_KEY:
        logger.info("Using OpenAI fallback provider.")
        return ChatOpenAI(
            model=settings.OPENAI_MODEL_NAME,
            api_key=settings.OPENAI_API_KEY,
            temperature=settings.TEMPERATURE
        )
        
    # 3. Final Fallback (or Error)
    logger.error("No valid LLM configuration found (Neither Gemini nor OpenAI keys provided).")
    raise ValueError("No LLM provider available. Check your .env file.")


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
    
    # 1. Ensure System Prompt is present
    system_msg = [m for m in messages if isinstance(m, SystemMessage)]
    if not system_msg:
        system_msg = [SystemMessage(content=SYSTEM_PROMPT)]
    
    # 2. Get other messages (Human, AI, Tool)
    other_msgs = [m for m in messages if not isinstance(m, SystemMessage)]
    
    # 3. K-Window Logic (must start with Human for API compliance)
    k = 3
    window_size = k * 2
    if len(other_msgs) > window_size:
        # Take the last window_size messages
        trimmed_history = other_msgs[-window_size:]
        # API COMPLIANCE: Ensure history starts with a HumanMessage after System Prompt
        # If the first trimmed message is AI or Tool, we remove it.
        while trimmed_history and not isinstance(trimmed_history[0], HumanMessage):
            trimmed_history.pop(0)
    else:
        trimmed_history = other_msgs
    
    # Final message list for LLM
    final_messages = system_msg + trimmed_history

    try:
        # Get the LLM to use (with fallback support)
        llm = get_llm()
        
        # Conditionally bind tools based on global settings
        if settings.USE_TOOLS:
            model = llm.bind_tools(tools)
        else:
            model = llm
            
        response = model.invoke(final_messages)
        # In development, try to log exactly what we're sending to figure out why it crashes
        logger.error(f"Error invoking primary LLM: {e}")
        try:
            debug_info = [(m.type, getattr(m, 'name', None), bool(getattr(m, 'tool_calls', None))) for m in final_messages]
            logger.error(f"DEBUG final_messages sequence: {debug_info}")
        except:
            pass

        if settings.OPENAI_API_KEY:
            logger.info("Retrying with OpenAI fallback...")
            llm = ChatOpenAI(
                model=settings.OPENAI_MODEL_NAME,
                api_key=settings.OPENAI_API_KEY,
                temperature=settings.TEMPERATURE
            )
            if settings.USE_TOOLS:
                model = llm.bind_tools(tools)
            else:
                model = llm
            response = model.invoke(final_messages)
        else:
            logger.error("No fallback available.")
            raise e

    # We return a list, which will be appended to the existing messages 
    return {"messages": [response]}

# ToolNode is a prebuilt node in LangGraph that handles tool execution
tool_node = ToolNode(tools)

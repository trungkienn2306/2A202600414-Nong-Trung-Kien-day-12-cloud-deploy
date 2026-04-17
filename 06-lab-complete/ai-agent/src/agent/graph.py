from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from src.agent.state import AgentState
from src.agent.nodes import call_model, tool_node
from src.core.config import settings
import sqlite3
import logging

logger = logging.getLogger(__name__)

def should_continue(state: AgentState):
    """
    Conditional edge to decide whether to call tools or end the conversation.
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    # If the LLM has made a tool call, we continue to the tool node
    if getattr(last_message, "tool_calls", None):
        return "tools"
    # Otherwise, we respond to the user and end
    return END

def human_review(state: AgentState):
    """
    A node to handle human intervention. 
    Interrupts happen BEFORE this node.
    """
    pass

def route_after_tools(state: AgentState):
    """
    After tools run, check if we need to wait for human input.
    """
    messages = state["messages"]
    # Check the last message (which should be a ToolMessage from the tool node)
    last_msg = messages[-1]
    
    # If request_user was one of the tools, we go to human_review
    if "REQUESTED_USER_INPUT" in getattr(last_msg, "content", ""):
        return "human_review"
    
    # Otherwise, continue back to the agent to process tool results
    return "agent"

# Initialize the StateGraph
workflow = StateGraph(AgentState)

# Add our nodes
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)
workflow.add_node("human_review", human_review)

# Define the edges
workflow.add_edge(START, "agent")

workflow.add_conditional_edges(
    "agent",
    should_continue,
    {"tools": "tools", END: END}
)

# After tools, we decide: back to agent or wait for human?
workflow.add_conditional_edges(
    "tools",
    route_after_tools,
    {"human_review": "human_review", "agent": "agent"}
)

# After human review (user provided input), always go back to agent
workflow.add_edge("human_review", "agent")

# Initialize Checkpointer
memory = None

if settings.REDIS_URL:
    try:
        from langgraph.checkpoint.redis import RedisSaver
        from redis import Redis, ConnectionPool
        
        # 1. Connection Pooling to handle Render Free limits (Max 20 connections)
        # Using a pool ensures we reuse connections efficiently.
        redis_url = settings.REDIS_URL.strip()
        pool = ConnectionPool.from_url(
            redis_url, 
            max_connections=15, # Leaving some room for other processes
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30
        )
        redis_client = Redis(connection_pool=pool)
        
        # 2. Check connection immediately
        redis_client.ping()
        
        memory = RedisSaver(redis_client)
        # Required to create indices/structure on startup
        memory.setup()
        logger.info(f"Using Robust Redis checkpointer: {settings.REDIS_URL}")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}. Falling back to SQLite to maintain service.")
        memory = None

if memory is None:
    # Initialize the SQLite connection
    conn = sqlite3.connect("checkpoints.sqlite", check_same_thread=False)
    memory = SqliteSaver(conn)
    logger.info("Using SQLite checkpointer: checkpoints.sqlite")

# Compile the graph
# We ONLY interrupt before human_review
app = workflow.compile(
    checkpointer=memory,
    interrupt_before=["human_review"]
)

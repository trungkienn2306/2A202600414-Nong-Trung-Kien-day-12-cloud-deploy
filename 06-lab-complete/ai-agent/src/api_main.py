import os
import uuid
import logging
import asyncio
import signal
from typing import Optional, List, Any
from fastapi import FastAPI, HTTPException, Request, Depends, Security, status
from fastapi.security.api_key import APIKeyHeader, APIKey
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, ToolMessage

# Local imports
from src.agent.graph import app as agent_app
from src.app import format_ai_response
from src.core.config import settings

# 1. Structured Logging
class JsonFormatter(logging.Formatter):
    def format(self, record):
        import json
        from datetime import datetime
        log_record = {
            "ts": datetime.utcnow().isoformat(),
            "lvl": record.levelname,
            "msg": record.getMessage(),
            "module": record.module,
        }
        if hasattr(record, "extra"):
            log_record.update(record.extra)
        return json.dumps(log_record)

handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger = logging.getLogger("api_main")
logger.addHandler(handler)
logger.setLevel(logging.INFO)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url=None
)

# 2. Security (API Key)
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(
    api_key: str = Security(api_key_header),
    request: Request = None
):
    # --- AUTH DEBUG ---
    expected = settings.AGENT_API_KEY or "NOT_SET"
    received = api_key or "MISSING"
    
    # Log details to Render logs
    all_headers = dict(request.headers) if request else {}
    # Masking keys for safety but keeping enough to compare
    def mask(k): return f"{k[:3]}***{k[-2:]}" if len(k) > 5 else "SHORT"
    
    logger.info(f"Auth Debug | Env: {settings.ENVIRONMENT}")
    logger.info(f"Auth Debug | Expected: {mask(expected)}")
    logger.info(f"Auth Debug | Received: {mask(received) if received != 'MISSING' else 'MISSING'}")
    
    # Check if X-API-Key is present even if auto-error=False might hide it
    logger.info(f"Auth Debug | All Headers (sensitive masked): { {k: (v[:3]+'***' if 'key' in k.lower() or 'auth' in k.lower() else v) for k, v in all_headers.items()} }")
    
    if settings.ENVIRONMENT == "development" and not api_key:
        logger.info("Auth Debug | Permitting empty key in development mode")
        return "dev-mode"
    
    if not api_key:
        logger.warning("Auth Debug | Missing API Key header.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key"
        )
    
    if api_key.strip() == settings.AGENT_API_KEY.strip():
        return api_key
    
    logger.warning(f"Auth Debug | Mismatch! Invalid API Key received.")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API Key"
    )

# 3. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    thread_id: str
    status: str  # "success", "need_input", "error"
    question: Optional[str] = None

# 4. Probes
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.VERSION
    }

@app.get("/ready")
async def readiness_check():
    # Check if Gemini key is present (basic check)
    if not settings.GEMINI_API_KEY:
        return status.HTTP_503_SERVICE_UNAVAILABLE, {"status": "degraded", "reason": "GEMINI_API_KEY missing"}
    return {"status": "ready"}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, api_key: APIKey = Depends(get_api_key)):
    try:
        thread_id = request.thread_id or str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        
        logger.info(f"Processing chat request for thread: {thread_id}")
        
        current_state = agent_app.get_state(config)
        
        if "human_review" in current_state.next:
            last_msg = current_state.values["messages"][-1]
            if not isinstance(last_msg, ToolMessage) or "REQUESTED_USER_INPUT" not in last_msg.content:
                 raise HTTPException(status_code=400, detail="Unexpected state: Missing request_user tool call.")
            
            agent_app.update_state(
                config,
                {"messages": [ToolMessage(
                    tool_call_id=last_msg.tool_call_id, 
                    content=request.message, 
                    id=last_msg.id,
                    name=getattr(last_msg, 'name', 'request_user')
                )]}
            )
            final_output = agent_app.invoke(None, config)
        else:
            input_data = {"messages": [HumanMessage(content=request.message)]}
            final_output = agent_app.invoke(input_data, config)
        
        snapshot = agent_app.get_state(config)
        if "human_review" in snapshot.next:
            last_msg = snapshot.values["messages"][-1]
            question = last_msg.content.replace("REQUESTED_USER_INPUT: ", "")
            return ChatResponse(
                response="",
                thread_id=thread_id,
                status="need_input",
                question=question
            )
        
        messages = snapshot.values.get("messages", [])
        if not messages:
            return ChatResponse(response="I'm sorry, I couldn't generate a response.", thread_id=thread_id, status="error")
            
        last_ai_msg = None
        for msg in reversed(messages):
            if msg.type == "ai" and not msg.tool_calls:
                last_ai_msg = msg
                break
        
        if not last_ai_msg:
             return ChatResponse(response="Processing...", thread_id=thread_id, status="success")

        return ChatResponse(
            response=format_ai_response(last_ai_msg.content),
            thread_id=thread_id,
            status="success"
        )

    except HTTPException as he:
        # Re-raise HTTP exceptions (like 401, 400) without catching them as 500
        raise he
    except Exception as e:
        logger.error(f"!!! CRITICAL ERROR in chat endpoint: {str(e)}", exc_info=True)
        # We always return the real error for now to help you debug why it died after 3 chats
        error_msg = str(e)
        raise HTTPException(status_code=500, detail=f"Backend Error: {error_msg}")

# 5. Graceful Shutdown
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application is shutting down...")
    # Add cleanup logic here if needed (e.g., closing Redis connections)

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting {settings.APP_NAME} on 0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)

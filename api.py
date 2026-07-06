"""
FastAPI Server for Agentic Chatbot
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import logging
import uvicorn
import os
from datetime import datetime

from src.agents.orchestrator import OrchestratorAgent
from src.middleware.caching import ResponseCache
from src.middleware.monitoring import MetricsCollector
from src.core.context_manager import ContextManager
from src.utils.helpers import load_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Agentic Chatbot API",
    description="Low-latency agentic chatbot with multi-step reasoning",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load config
config = load_config('config.yaml')

# Initialize components
orchestrator = OrchestratorAgent(config)
cache = ResponseCache(config.get('optimization', {}))
metrics = MetricsCollector()
context_manager = ContextManager(config)

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "default_user"
    stream: Optional[bool] = False
    context: Optional[dict] = None

class ChatResponse(BaseModel):
    response: str
    user_id: str
    intent: str
    confidence: float
    latency_ms: float
    timestamp: str
    cache_hit: bool = False

@app.get("/")
async def root():
    return {
        "name": "Agentic Chatbot API",
        "version": "1.0.0",
        "status": "healthy",
        "endpoints": ["/chat", "/health", "/metrics"]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/metrics")
async def get_metrics():
    """Get performance metrics [citation:9]"""
    return {
        "metrics": metrics.get_metrics(),
        "cache": cache.get_stats()
    }

@app.post("/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Send a message to the agentic chatbot
    """
    start_time = datetime.now()
    
    # Check cache [citation:3]
    cached_response = cache.get(request.message, request.context or {})
    if cached_response:
        metrics.record_request(0, cache_hit=True)
        
        return ChatResponse(
            response=cached_response,
            user_id=request.user_id,
            intent="cached",
            confidence=1.0,
            latency_ms=0,
            timestamp=datetime.now().isoformat(),
            cache_hit=True
        )
    
    try:
        # Get conversation history
        context = context_manager.get_context(request.user_id)
        history = context.get('history', [])
        
        # Process through orchestrator
        result = await orchestrator.process(
            user_input=request.message,
            user_id=request.user_id,
            conversation_history=history
        )
        
        response_text = result.get('response', '')
        
        # Cache response
        cache.set(request.message, request.context or {}, response_text)
        
        # Record metrics [citation:9]
        latency_ms = result.get('latency_ms', 0)
        metrics.record_request(latency_ms, cache_hit=False)
        
        return ChatResponse(
            response=response_text,
            user_id=request.user_id,
            intent=result.get('intent', 'general'),
            confidence=result.get('confidence', 0.8),
            latency_ms=latency_ms,
            timestamp=datetime.now().isoformat(),
            cache_hit=False
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        metrics.record_request(0, error=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/clear/{user_id}")
async def clear_context(user_id: str):
    """Clear user context"""
    context_manager.clear_context(user_id)
    return {"status": "cleared", "user_id": user_id}

@app.get("/history/{user_id}")
async def get_history(user_id: str):
    """Get conversation history"""
    context = context_manager.get_context(user_id)
    return {
        "user_id": user_id,
        "history": context.get('history', [])[-10:]  # Last 10 messages
    }

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)

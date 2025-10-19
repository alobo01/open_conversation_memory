from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime
import asyncio
import logging
from contextlib import asynccontextmanager

from routers import conversation, knowledge_graph, asr, background_tasks
from services.llm_service import LLMService
from services.memory_service import MemoryService
from services.emotion_service import EmotionService
from core.config import settings
from core.database import init_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting EmoRobCare API...")
    await init_db()
    app.state.llm_service = LLMService()
    app.state.memory_service = MemoryService()
    app.state.emotion_service = EmotionService()
    logger.info("Services initialized successfully")
    yield
    # Shutdown
    logger.info("Shutting down EmoRobCare API...")

app = FastAPI(
    title="EmoRobCare API",
    description="Conversational AI API for children with TEA2",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(conversation.router, prefix="/conv", tags=["conversation"])
app.include_router(knowledge_graph.router, prefix="/kg", tags=["knowledge-graph"])
app.include_router(asr.router, prefix="/asr", tags=["asr"])
app.include_router(background_tasks.router, prefix="/tasks", tags=["background-tasks"])

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "0.1.0",
        "services": {
            "llm": "ready",
            "memory": "ready",
            "emotion": "ready"
        }
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "EmoRobCare API - Conversational AI for children with TEA2",
        "version": "0.1.0",
        "endpoints": {
            "conversation": "/conv",
            "knowledge_graph": "/kg",
            "asr": "/asr",
            "health": "/health",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
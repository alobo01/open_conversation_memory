from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging
import time
import io
import tempfile
import os
from typing import Optional

from .services.transcription_service import TranscriptionService
from .models.schemas import ASRTranscribe, ASRTier, Language
from .core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global transcription service
transcription_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    global transcription_service
    logger.info("Starting EmoRobCare ASR Service")

    try:
        transcription_service = TranscriptionService()
        logger.info("ASR transcription service initialized successfully")

        # Wait a moment for initial model loading
        import asyncio
        await asyncio.sleep(2)

        logger.info("ASR Service startup complete")

    except Exception as e:
        logger.error(f"Failed to initialize ASR service: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down ASR Service")
    if transcription_service:
        try:
            await transcription_service.cleanup()
            logger.info("ASR service cleanup completed")
        except Exception as e:
            logger.error(f"Error during ASR service cleanup: {e}")

    logger.info("ASR Service shutdown complete")

app = FastAPI(
    title="EmoRobCare ASR Service",
    description="Speech-to-Text service for children with TEA2 using faster-whisper",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint with comprehensive status"""
    try:
        health = await transcription_service.health_check()
        health["version"] = "0.1.0"
        return health
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": time.time(),
            "version": "0.1.0",
            "error": str(e)
        }

@app.post("/transcribe", response_model=ASRTranscribe)
async def transcribe_audio(
    audio: UploadFile = File(...),
    tier: ASRTier = Query(ASRTier.BALANCED, description="ASR accuracy tier"),
    language: Optional[str] = Query(None, description="Audio language (auto-detect if not specified)")
):
    """Transcribe audio file to text using faster-whisper"""
    try:
        # Validate audio file
        if not audio.content_type.startswith('audio/'):
            raise HTTPException(
                status_code=400,
                detail=f"File must be an audio file, got {audio.content_type}"
            )

        # Check file size (max 10MB)
        if hasattr(audio, 'size') and audio.size and audio.size > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail="Audio file too large, maximum size is 10MB"
            )

        # Read audio data
        audio_data = await audio.read()

        if len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="Audio file is empty")

        logger.info(f"Processing audio transcription request: tier={tier}, language={language or 'auto'}, size={len(audio_data)} bytes")

        # Transcribe
        result = await transcription_service.transcribe(
            audio_data,
            tier=tier,
            language=language or settings.default_language
        )

        # Return the transcription result
        return ASRTranscribe(
            text=result["text"],
            language=Language(result["language"]),
            confidence=result["confidence"],
            tier=ASRTier(result.get("tier", tier)),
            processing_time=result["processing_time"]
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error transcribing audio: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to transcribe audio. Please try again or contact support."
        )

@app.get("/models")
async def get_available_models():
    """Get available ASR models"""
    models = await transcription_service.get_available_models()
    return models

@app.post("/test")
async def test_transcription(
    text: str = Query(..., description="Text to simulate transcription"),
    tier: ASRTier = Query(ASRTier.BALANCED),
    language: str = Query(settings.default_language)
):
    """Test endpoint for ASR without actual audio"""
    try:
        # Simulate processing time based on tier
        processing_times = {
            ASRTier.FAST: 0.5,
            ASRTier.BALANCED: 1.0,
            ASRTier.ACCURATE: 2.0
        }

        processing_time = processing_times[tier]

        # Simulate confidence based on tier
        confidence_scores = {
            ASRTier.FAST: 0.85,
            ASRTier.BALANCED: 0.92,
            ASRTier.ACCURATE: 0.97
        }

        confidence = confidence_scores[tier]

        return ASRTranscribe(
            text=text,
            language=Language(language),
            confidence=confidence,
            tier=tier,
            processing_time=processing_time
        )

    except Exception as e:
        logger.error(f"Error in test transcription: {e}")
        raise HTTPException(status_code=500, detail="Failed to test transcription")

@app.get("/stats")
async def get_service_stats():
    """Get comprehensive service statistics"""
    if not transcription_service:
        raise HTTPException(status_code=503, detail="Service not initialized")

    stats = await transcription_service.get_stats()
    return stats

@app.get("/status")
async def get_detailed_status():
    """Get detailed service status including model information"""
    if not transcription_service:
        raise HTTPException(status_code=503, detail="Service not initialized")

    model_status = await transcription_service.get_model_status()
    available_models = await transcription_service.get_available_models()

    return {
        "service": "EmoRobCare ASR Service",
        "version": "0.1.0",
        "timestamp": time.time(),
        "models": model_status,
        "configuration": available_models,
        "health": await transcription_service.health_check()
    }

@app.post("/benchmark")
async def benchmark_transcription(
    audio: UploadFile = File(...),
    iterations: int = Query(3, description="Number of iterations to run", ge=1, le=10),
    tier: ASRTier = Query(ASRTier.BALANCED, description="ASR accuracy tier")
):
    """Benchmark transcription performance across multiple iterations"""
    if not transcription_service:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        # Validate audio file
        if not audio.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="File must be an audio file")

        # Read audio data once
        audio_data = await audio.read()

        if len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="Audio file is empty")

        results = []

        for i in range(iterations):
            start_time = time.time()
            result = await transcription_service.transcribe(
                audio_data,
                tier=tier,
                language="auto"
            )
            processing_time = time.time() - start_time

            results.append({
                "iteration": i + 1,
                "text": result["text"],
                "language": result["language"],
                "confidence": result["confidence"],
                "processing_time": processing_time
            })

        # Calculate statistics
        processing_times = [r["processing_time"] for r in results]
        avg_time = sum(processing_times) / len(processing_times)
        min_time = min(processing_times)
        max_time = max(processing_times)

        # Check if results are consistent
        texts = [r["text"] for r in results]
        unique_texts = set(texts)
        consistency = len(unique_texts) / len(texts)

        return {
            "benchmark_results": {
                "tier": tier,
                "iterations": iterations,
                "audio_size_bytes": len(audio_data),
                "processing_time": {
                    "average": round(avg_time, 3),
                    "minimum": round(min_time, 3),
                    "maximum": round(max_time, 3),
                    "std_dev": round((sum((t - avg_time) ** 2 for t in processing_times) / len(processing_times)) ** 0.5, 3)
                },
                "consistency": round(consistency, 3),
                "unique_results": len(unique_texts),
                "all_results": results
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in benchmark: {e}")
        raise HTTPException(status_code=500, detail="Benchmark failed")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level="info"
    )
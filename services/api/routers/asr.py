from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from typing import Optional
import io
import time
import logging
import tempfile
import os

from ..models.schemas import ASRTranscribe, ASRTier, Language
from ..core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/transcribe", response_model=ASRTranscribe)
async def transcribe_audio(
    audio: UploadFile = File(...),
    tier: ASRTier = Query(ASRTier.BALANCED, description="ASR accuracy tier"),
    language: Optional[str] = Query(None, description="Audio language (auto-detect if not specified)")
):
    """Transcribe audio file to text using Whisper"""
    try:
        # Validate audio file
        if not audio.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="File must be an audio file")

        # Read audio data
        audio_data = await audio.read()

        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name

        try:
            # Transcribe using appropriate model based on tier
            start_time = time.time()

            # This would integrate with the actual ASR service
            # For now, returning a mock transcription
            transcription = await mock_transcribe(
                temp_file_path,
                tier,
                language or settings.default_language
            )

            processing_time = time.time() - start_time

            # Clean up temporary file
            os.unlink(temp_file_path)

            logger.info(f"Audio transcribed in {processing_time:.2f}s using {tier.value} tier")

            return ASRTranscribe(
                text=transcription["text"],
                language=Language(transcription["language"]),
                confidence=transcription["confidence"],
                tier=tier,
                processing_time=processing_time
            )

        except Exception as e:
            # Clean up temporary file on error
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            raise e

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        raise HTTPException(status_code=500, detail="Failed to transcribe audio")

@router.get("/models")
async def get_available_models():
    """Get available ASR models"""
    return {
        "models": settings.asr_models,
        "default_tiers": {
            "fast": settings.asr_models["fast"],
            "balanced": settings.asr_models["balanced"],
            "accurate": settings.asr_models["accurate"]
        },
        "gpu_enabled": settings.asr_gpu
    }

@router.get("/health")
async def health_check():
    """ASR service health check"""
    return {
        "status": "healthy",
        "models_loaded": True,  # This would check actual model status
        "gpu_available": settings.asr_gpu,
        "supported_formats": ["wav", "mp3", "flac", "m4a"]
    }

@router.post("/test")
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

# Helper functions
async def mock_transcribe(
    file_path: str,
    tier: ASRTier,
    language: str
) -> dict:
    """Mock transcription function - would integrate with real Whisper"""
    # Simulate different processing times based on tier
    import asyncio

    delays = {
        ASRTier.FAST: 0.5,
        ASRTier.BALANCED: 1.0,
        ASRTier.ACCURATE: 2.0
    }

    await asyncio.sleep(delays[tier])

    # Mock transcriptions based on language
    mock_transcriptions = {
        "es": [
            "Hola, me gusta jugar en el parque",
            "Quiero hablar de mis amigos",
            "Hoy me diverti mucho en la escuela",
            "Me gusta leer cuentos de animales",
            "Quiero un helado de chocolate"
        ],
        "en": [
            "Hello, I like to play in the park",
            "I want to talk about my friends",
            "Today I had fun at school",
            "I like to read animal stories",
            "I want a chocolate ice cream"
        ]
    }

    import random
    text = random.choice(mock_transcriptions.get(language, mock_transcriptions["es"]))

    # Simulate confidence based on tier
    confidence_scores = {
        ASRTier.FAST: 0.85,
        ASRTier.BALANCED: 0.92,
        ASRTier.ACCURATE: 0.97
    }

    return {
        "text": text,
        "language": language,
        "confidence": confidence_scores[tier]
    }

# This would be the real implementation with Whisper/faster-whisper
async def transcribe_with_whisper(
    file_path: str,
    model_size: str,
    language: Optional[str] = None
) -> dict:
    """Real transcription using Whisper"""
    try:
        import whisper

        # Load model
        model = whisper.load_model(model_size)

        # Transcribe
        result = model.transcribe(
            file_path,
            language=language if language != "auto" else None,
            fp16=settings.asr_gpu  # Use FP16 if GPU available
        )

        return {
            "text": result["text"],
            "language": result["language"],
            "confidence": 0.95  # Whisper doesn't provide confidence directly
        }

    except Exception as e:
        logger.error(f"Error in Whisper transcription: {e}")
        raise
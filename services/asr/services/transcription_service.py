import logging
import time
import asyncio
import tempfile
import os
from typing import Dict, Any, List, Optional, Tuple
import torch
import numpy as np
from faster_whisper import WhisperModel
import io
import librosa
import soundfile as sf
import warnings

from ..core.config import settings

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning)

logger = logging.getLogger(__name__)

class TranscriptionService:
    """Service for audio transcription using faster-whisper with 3-tier precision system"""

    def __init__(self):
        self.models = {}
        self.model_configs = settings.models
        self.device = self._detect_device()
        self.tier_configs = settings.tier_configs

        # Override GPU settings based on actual availability
        settings.gpu_enabled = (self.device == "cuda")
        settings.device = self.device

        logger.info(f"ASR Service initialized on device: {self.device}")
        logger.info(f"GPU acceleration enabled: {settings.gpu_enabled}")

        self.stats = {
            "total_transcriptions": 0,
            "total_processing_time": 0.0,
            "model_usage": {tier: 0 for tier in self.model_configs.keys()},
            "language_distribution": {lang: 0 for lang in settings.supported_languages},
            "failed_transcriptions": 0
        }
        self.start_time = time.time()

        # Start background model loading
        asyncio.create_task(self._preload_models())

    def _detect_device(self) -> str:
        """Auto-detect the best available device"""
        try:
            if torch.cuda.is_available():
                device_count = torch.cuda.device_count()
                logger.info(f"Found {device_count} CUDA device(s)")
                for i in range(device_count):
                    props = torch.cuda.get_device_properties(i)
                    memory_gb = props.total_memory / 1024**3
                    logger.info(f"GPU {i}: {props.name}, {memory_gb:.1f}GB memory")
                return "cuda"
            else:
                logger.info("No CUDA devices available, using CPU")
                return "cpu"
        except Exception as e:
            logger.warning(f"Error detecting device: {e}, falling back to CPU")
            return "cpu"

    async def _preload_models(self):
        """Preload all configured models in background"""
        for tier, model_size in self.model_configs.items():
            try:
                await self._load_model(tier, model_size)
                logger.info(f"Successfully loaded {tier} model: {model_size}")
            except Exception as e:
                logger.error(f"Failed to load {tier} model {model_size}: {e}")

    async def _load_model(self, tier: str, model_size: str) -> bool:
        """Load a Whisper model with tier-specific configuration"""
        try:
            tier_config = self.tier_configs.get(tier, self.tier_configs["balanced"])

            # Determine compute type based on device and tier
            if self.device == "cuda":
                compute_type = tier_config["compute_type"]
            else:
                compute_type = "int8"  # Always use int8 on CPU for efficiency

            logger.info(f"Loading {tier} model {model_size} with compute_type={compute_type}")

            # Initialize faster-whisper model
            model = WhisperModel(
                model_size,
                device=self.device,
                compute_type=compute_type,
                device_index=0 if self.device == "cuda" else None
            )

            self.models[tier] = {
                "model": model,
                "size": model_size,
                "config": tier_config,
                "loaded_at": time.time(),
                "compute_type": compute_type
            }

            return True

        except Exception as e:
            logger.error(f"Error loading model {model_size} for tier {tier}: {e}")
            return False

    async def transcribe(
        self,
        audio_data: bytes,
        tier: str = "balanced",
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Transcribe audio data with tier-specific precision"""
        try:
            start_time = time.time()

            # Validate tier
            if tier not in self.model_configs:
                logger.warning(f"Unknown tier '{tier}', falling back to 'balanced'")
                tier = "balanced"

            # Get or load model
            model_info = await self._get_or_load_model(tier)
            if not model_info:
                return await self._fallback_transcription(language, "Model unavailable")

            model = model_info["model"]
            config = model_info["config"]

            # Validate and preprocess audio
            audio_array, sample_rate = await self._validate_and_preprocess_audio(audio_data)
            if audio_array is None:
                return await self._fallback_transcription(language, "Invalid audio")

            # Configure transcription parameters for tier
            transcribe_params = {
                "beam_size": config["beam_size"],
                "vad_filter": settings.enable_vad,
                "vad_parameters": dict(min_silence_duration_ms=500),
                "word_timestamps": False
            }

            # Add language if specified (not "auto")
            if language and language != "auto":
                transcribe_params["language"] = language

            logger.info(f"Starting transcription with {tier} tier, language={language or 'auto'}")

            # Perform transcription
            segments, info = model.transcribe(audio_array, **transcribe_params)

            # Combine segments and filter empty ones
            transcription_segments = []
            for segment in segments:
                text = segment.text.strip()
                if text:
                    transcription_segments.append(text)

            transcription_text = " ".join(transcription_segments)

            # Calculate confidence based on tier and text quality
            confidence = self._estimate_confidence(transcription_text, tier, info.language_probability)

            # Post-process text
            transcription_text = self._post_process_text(transcription_text)

            # Update statistics
            processing_time = time.time() - start_time
            self._update_stats(tier, info.language, processing_time)

            logger.info(f"Transcription completed in {processing_time:.2f}s, language={info.language}")

            return {
                "text": transcription_text,
                "language": info.language,
                "confidence": confidence,
                "processing_time": processing_time,
                "tier": tier,
                "detected_language_probability": info.language_probability
            }

        except Exception as e:
            logger.error(f"Error in transcription: {str(e)}")
            self.stats["failed_transcriptions"] += 1
            return await self._fallback_transcription(language, f"Transcription error: {str(e)}")

    async def _get_or_load_model(self, tier: str) -> Optional[Dict[str, Any]]:
        """Get existing model or load on demand"""
        model_info = self.models.get(tier)
        if model_info:
            return model_info

        # Load model on demand
        model_size = self.model_configs.get(tier, "base")
        success = await self._load_model(tier, model_size)
        if success:
            return self.models[tier]
        else:
            logger.error(f"Failed to load model for tier {tier}")
            return None

    async def _validate_and_preprocess_audio(self, audio_data: bytes) -> Tuple[Optional[np.ndarray], Optional[int]]:
        """Validate and preprocess audio data"""
        try:
            # Check audio data size
            if len(audio_data) == 0:
                logger.error("Empty audio data received")
                return None, None

            # Maximum 30 seconds of audio at 16kHz
            max_size = 30 * 16000 * 2  # 16-bit samples
            if len(audio_data) > max_size:
                logger.warning(f"Audio data too large ({len(audio_data)} bytes), truncating")
                audio_data = audio_data[:max_size]

            # Save to temporary file for processing
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name

            try:
                # Load with librosa for consistent preprocessing
                audio, sample_rate = librosa.load(temp_file_path, sr=16000, mono=True)

                # Basic validation
                if audio.size == 0:
                    logger.error("Loaded audio is empty")
                    return None, None

                # Check if audio is too quiet (likely silence)
                rms = np.sqrt(np.mean(audio**2))
                if rms < 0.001:
                    logger.warning(f"Audio seems very quiet (RMS: {rms:.6f})")
                    # Still process but warn

                # Convert to float32 if needed
                if audio.dtype != np.float32:
                    audio = audio.astype(np.float32)

                return audio, sample_rate

            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)

        except Exception as e:
            logger.error(f"Error validating/preprocessing audio: {e}")
            return None, None

    def _post_process_text(self, text: str) -> str:
        """Post-process transcription text"""
        if not text:
            return text

        # Remove common artifacts
        text = text.strip()

        # Remove repeated spaces
        text = " ".join(text.split())

        # Capitalize first letter for Spanish/English
        if text and len(text) > 0:
            text = text[0].upper() + text[1:]

        # Ensure proper punctuation
        if text and not text.endswith(('.', '!', '?', ',')):
            text += '.'

        return text

    def _estimate_confidence(self, text: str, tier: str, language_probability: float = None) -> float:
        """Estimate transcription confidence based on multiple factors"""
        # Base confidence from tier configuration
        base_confidence = self.tier_configs.get(tier, {}).get("base_confidence", 0.90)

        confidence = base_confidence

        # Adjust based on text characteristics
        if not text.strip():
            return 0.0

        # Language detection confidence (if available)
        if language_probability is not None:
            confidence *= (0.7 + 0.3 * language_probability)

        # Penalize very short or very long transcriptions
        word_count = len(text.split())
        if word_count < 2:
            confidence *= 0.8
        elif word_count > 50:
            confidence *= 0.9

        # Boost confidence for complete sentences
        if text.endswith(('.', '!', '?')):
            confidence *= 1.05

        # Penalize if text contains common error patterns
        error_patterns = ['[', ']', '(', ')', '*', '#', '@', '%', '$']
        for pattern in error_patterns:
            if pattern in text:
                confidence *= 0.95

        # Ensure confidence stays within valid range
        return min(max(confidence, 0.0), 1.0)

    async def _fallback_transcription(self, language: Optional[str] = None, error_msg: str = "Transcription failed") -> Dict[str, Any]:
        """Fallback transcription when model fails"""
        fallback_texts = {
            "es": [
                "No pude entender bien, ¿puedes repetir?",
                "No escuché claramente, ¿lo puedes decir otra vez?",
                "¿Puedes hablar un poco más claro, por favor?"
            ],
            "en": [
                "I couldn't understand well, can you repeat?",
                "I didn't hear clearly, can you say it again?",
                "Can you speak a little more clearly, please?"
            ]
        }

        lang = language or settings.default_language
        import random
        text = random.choice(fallback_texts.get(lang, fallback_texts["es"]))

        logger.warning(f"Using fallback transcription: {error_msg}")

        return {
            "text": text,
            "language": lang,
            "confidence": 0.1,
            "processing_time": 0.1,
            "tier": "fallback",
            "error": error_msg
        }

    def _update_stats(self, tier: str, language: str, processing_time: float):
        """Update service statistics"""
        self.stats["total_transcriptions"] += 1
        self.stats["total_processing_time"] += processing_time
        self.stats["model_usage"][tier] += 1
        self.stats["language_distribution"][language] += 1

    async def get_model_status(self) -> Dict[str, Any]:
        """Get detailed status of loaded models"""
        status = {}
        total_memory_used = 0

        for tier, model_info in self.models.items():
            if model_info:
                # Calculate approximate memory usage
                memory_mb = self._estimate_model_memory(model_info["size"])
                total_memory_used += memory_mb

                status[tier] = {
                    "model_name": model_info["size"],
                    "tier": tier,
                    "loaded": True,
                    "loaded_at": model_info["loaded_at"],
                    "compute_type": model_info["compute_type"],
                    "device": self.device,
                    "estimated_memory_mb": memory_mb,
                    "config": model_info["config"]
                }
            else:
                status[tier] = {
                    "model_name": self.model_configs.get(tier, "unknown"),
                    "tier": tier,
                    "loaded": False,
                    "device": self.device
                }

        gpu_info = {}
        if self.device == "cuda" and torch.cuda.is_available():
            gpu_info = {
                "gpu_available": True,
                "gpu_name": torch.cuda.get_device_name(0),
                "gpu_memory_total": torch.cuda.get_device_properties(0).total_memory / 1024**3,  # GB
                "gpu_memory_allocated": torch.cuda.memory_allocated(0) / 1024**3,  # GB
                "gpu_memory_reserved": torch.cuda.memory_reserved(0) / 1024**3  # GB
            }
        else:
            gpu_info = {"gpu_available": False}

        return {
            "models": status,
            "device": self.device,
            "total_estimated_memory_mb": total_memory_used,
            "gpu_info": gpu_info,
            "supported_tiers": list(self.model_configs.keys())
        }

    def _estimate_model_memory(self, model_size: str) -> float:
        """Estimate model memory usage in MB"""
        # Rough estimates based on model sizes
        size_map = {
            "medium": 1500,      # ~1.5GB
            "large-v2": 3000,    # ~3GB
            "large-v3": 3000,    # ~3GB
            "base": 150,         # ~150MB
            "small": 500,        # ~500MB
            "tiny": 75           # ~75MB
        }
        return size_map.get(model_size, 1000)

    async def get_available_models(self) -> Dict[str, Any]:
        """Get comprehensive information about available models and tiers"""
        return {
            "models": self.model_configs,
            "tier_configs": self.tier_configs,
            "supported_languages": settings.supported_languages,
            "default_language": settings.default_language,
            "gpu_enabled": settings.gpu_enabled,
            "current_device": self.device,
            "max_audio_length": settings.max_audio_length,
            "vad_enabled": settings.enable_vad,
            "performance_targets": {
                tier: config.get("realtime_factor", 1.0)
                for tier, config in self.tier_configs.items()
            }
        }

    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive service statistics"""
        uptime = time.time() - self.start_time
        avg_time = (
            self.stats["total_processing_time"] / self.stats["total_transcriptions"]
            if self.stats["total_transcriptions"] > 0 else 0
        )

        success_rate = (
            (self.stats["total_transcriptions"] - self.stats["failed_transcriptions"]) /
            self.stats["total_transcriptions"]
            if self.stats["total_transcriptions"] > 0 else 1.0
        )

        # Calculate performance metrics
        performance = {}
        for tier in self.model_configs.keys():
            usage = self.stats["model_usage"][tier]
            if usage > 0:
                performance[tier] = {
                    "usage_count": usage,
                    "usage_percentage": (usage / self.stats["total_transcriptions"]) * 100 if self.stats["total_transcriptions"] > 0 else 0
                }
            else:
                performance[tier] = {"usage_count": 0, "usage_percentage": 0}

        return {
            "total_transcriptions": self.stats["total_transcriptions"],
            "failed_transcriptions": self.stats["failed_transcriptions"],
            "success_rate": round(success_rate * 100, 2),
            "avg_processing_time": round(avg_time, 3),
            "total_processing_time": round(self.stats["total_processing_time"], 2),
            "model_usage": self.stats["model_usage"],
            "language_distribution": self.stats["language_distribution"],
            "performance_by_tier": performance,
            "uptime": round(uptime, 2),
            "transcriptions_per_minute": round(self.stats["total_transcriptions"] / (uptime / 60), 2) if uptime > 0 else 0
        }

    async def cleanup(self):
        """Cleanup resources and models"""
        logger.info("Cleaning up ASR transcription service resources")
        for tier, model_info in self.models.items():
            if model_info and "model" in model_info:
                try:
                    # Whisper models from faster-whisper don't need explicit cleanup
                    del model_info["model"]
                    logger.info(f"Cleaned up {tier} model")
                except Exception as e:
                    logger.warning(f"Error cleaning up {tier} model: {e}")

        self.models.clear()

        # Clear CUDA cache if using GPU
        if self.device == "cuda" and torch.cuda.is_available():
            torch.cuda.empty_cache()
            logger.info("Cleared CUDA cache")

    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        health = {
            "status": "healthy",
            "timestamp": time.time(),
            "uptime": time.time() - self.start_time,
            "checks": {}
        }

        # Check models
        loaded_models = sum(1 for model_info in self.models.values() if model_info)
        total_models = len(self.model_configs)
        health["checks"]["models"] = {
            "status": "healthy" if loaded_models > 0 else "unhealthy",
            "loaded": loaded_models,
            "total": total_models
        }

        # Check device/GPU
        if self.device == "cuda":
            gpu_healthy = torch.cuda.is_available()
            health["checks"]["gpu"] = {
                "status": "healthy" if gpu_healthy else "unhealthy",
                "available": gpu_healthy,
                "device": self.device
            }
        else:
            health["checks"]["cpu"] = {"status": "healthy", "device": "cpu"}

        # Check recent performance
        if self.stats["total_transcriptions"] > 0:
            recent_failures = self.stats["failed_transcriptions"] / self.stats["total_transcriptions"]
            health["checks"]["performance"] = {
                "status": "healthy" if recent_failures < 0.1 else "degraded",
                "failure_rate": round(recent_failures * 100, 2)
            }

        # Determine overall status
        unhealthy_checks = [check for check in health["checks"].values() if check["status"] == "unhealthy"]
        if unhealthy_checks:
            health["status"] = "unhealthy"

        return health
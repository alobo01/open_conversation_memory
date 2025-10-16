from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # ASR Configuration
    default_language: str = "es"
    supported_languages: list[str] = ["es", "en", "auto"]

    # Model configurations - using larger models for better accuracy
    models: dict[str, str] = {
        "fast": "medium",      # int8 precision, ~4x realtime, lower accuracy
        "balanced": "large-v2",  # fp16 precision, 2x realtime, default
        "accurate": "large-v3"   # fp16/fp32 precision, 0.5x realtime, max accuracy
    }

    # GPU settings - auto-detect CUDA availability
    gpu_enabled: bool = True  # Will be overridden based on actual availability
    device: str = "cuda"  # Will be determined at runtime

    # Performance settings
    max_audio_length: int = 30  # seconds
    chunk_size: int = 16000  # samples

    # Quality settings
    confidence_threshold: float = 0.5
    enable_vad: bool = True  # Voice Activity Detection

    # Tier-specific configurations
    tier_configs: dict[str, dict] = {
        "fast": {
            "compute_type": "int8",
            "beam_size": 1,
            "max_new_tokens": 128,
            "realtime_factor": 4.0,  # 4x realtime
            "base_confidence": 0.85
        },
        "balanced": {
            "compute_type": "float16",
            "beam_size": 2,
            "max_new_tokens": 256,
            "realtime_factor": 2.0,  # 2x realtime
            "base_confidence": 0.92
        },
        "accurate": {
            "compute_type": "float16",
            "beam_size": 5,
            "max_new_tokens": 448,
            "realtime_factor": 0.5,  # 0.5x realtime
            "base_confidence": 0.97
        }
    }

    # Cache settings
    enable_cache: bool = True
    cache_ttl: int = 3600  # seconds

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
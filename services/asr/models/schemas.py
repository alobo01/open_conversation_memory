from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class ASRTier(str, Enum):
    FAST = "fast"
    BALANCED = "balanced"
    ACCURATE = "accurate"

class Language(str, Enum):
    SPANISH = "es"
    ENGLISH = "en"
    AUTO = "auto"

class ASRTranscribe(BaseModel):
    text: str
    language: Language
    confidence: float = Field(ge=0.0, le=1.0)
    tier: ASRTier
    processing_time: float

class ModelStatus(BaseModel):
    model_name: str
    tier: ASRTier
    loaded: bool
    memory_usage: Optional[float] = None
    language_support: list[str]

class ServiceStats(BaseModel):
    total_transcriptions: int
    avg_processing_time: float
    model_usage: dict[str, int]
    language_distribution: dict[str, int]
    uptime: float
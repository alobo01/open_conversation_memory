from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum

class EmotionType(str, Enum):
    POSITIVE = "positive"
    CALM = "calm"
    NEUTRAL = "neutral"

class Language(str, Enum):
    SPANISH = "es"
    ENGLISH = "en"

class ConversationLevel(int, Enum):
    BASIC = 1  # Frases cortas, 1 idea por oración
    INTERMEDIATE = 2  # Frases cortas, vocabulario simple
    MIDDLE = 3  # Oraciones simples, conectores básicos
    ADVANCED = 4  # Oraciones complejas, variedad léxica
    FLUENT = 5  # Conversación fluida

class Topic(str, Enum):
    SCHOOL = "school"
    HOBBIES = "hobbies"
    HOLIDAYS = "holidays"
    FOOD = "food"
    FRIENDS = "friends"
    FAMILY = "family"
    ANIMALS = "animals"
    SPORTS = "sports"

class ASRTier(str, Enum):
    FAST = "fast"
    BALANCED = "balanced"
    ACCURATE = "accurate"

# Child Profile
class ChildProfile(BaseModel):
    child_id: str
    name: str
    age: int
    preferred_topics: List[Topic]
    avoid_topics: List[Topic] = []
    level: ConversationLevel
    sensitivity: Literal["low", "medium", "high"] = "medium"
    language: Language = Language.SPANISH
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

# Conversation
class ConversationStart(BaseModel):
    child: str
    topic: Topic
    level: ConversationLevel

class ConversationResponse(BaseModel):
    conversation_id: str
    starting_sentence: str
    end: bool = False
    emotion: Optional[EmotionType] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class ConversationNext(BaseModel):
    conversation_id: str
    user_sentence: str
    end: bool = False
    asr_confidence: Optional[float] = None

class ConversationReply(BaseModel):
    reply: str
    end: bool = False
    emotion: EmotionType
    timestamp: datetime = Field(default_factory=datetime.now)
    suggestions: Optional[List[str]] = None

class Message(BaseModel):
    conversation_id: str
    role: Literal["user", "assistant"]
    text: str
    emotion: Optional[EmotionType] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None

# Knowledge Graph
class KGInsert(BaseModel):
    sparql_update: str

class KGUpdate(BaseModel):
    sparql_update: str

class KGQuery(BaseModel):
    sparql_select: str
    limit: Optional[int] = 100

class KGResponse(BaseModel):
    results: List[Dict[str, Any]]
    success: bool
    execution_time: float
    total_count: Optional[int] = None

class KGReasonCheck(BaseModel):
    consistent: bool
    violations: List[Dict[str, Any]] = []
    reasoning_time: float

class KGValidate(BaseModel):
    conforms: bool
    violations: List[Dict[str, Any]] = []
    validation_time: float

class KGSchema(BaseModel):
    classes: List[Dict[str, Any]]
    properties: List[Dict[str, Any]]
    individuals: List[Dict[str, Any]]
    namespaces: Dict[str, str]

# ASR
class ASRTranscribe(BaseModel):
    text: str
    language: Language
    confidence: float
    tier: ASRTier
    processing_time: float

# Health and System
class HealthCheck(BaseModel):
    status: str
    timestamp: datetime
    version: str
    services: Dict[str, str]

class SystemInfo(BaseModel):
    api_version: str
    uptime: float
    memory_usage: Dict[str, float]
    active_conversations: int
    total_messages: int

# Safety
class SafetyViolation(BaseModel):
    type: str
    severity: Literal["low", "medium", "high"]
    description: str
    detected_content: Optional[str] = None
    suggestion: Optional[str] = None

class SafetyCheckResult(BaseModel):
    is_safe: bool
    violations: List[SafetyViolation] = []
    confidence: float
    processed_content: Optional[str] = None
    check_time: datetime = Field(default_factory=datetime.now)
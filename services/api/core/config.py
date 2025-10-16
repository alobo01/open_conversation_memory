from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # API Configuration
    api_title: str = "EmoRobCare API"
    api_version: str = "0.1.0"
    debug: bool = False

    # Database Configuration
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "emorobcare"

    # Qdrant (Vector Database)
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection_name: str = "conversations"

    # Fuseki (Knowledge Graph)
    fuseki_url: str = "http://localhost:3030"
    fuseki_dataset: str = "emorobcare"

    # LLM Configuration
    offline_mode: bool = True
    llm_model: str = "Qwen/Qwen2-7B-Instruct"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 150  # Reduced for child-appropriate responses

    # API Keys (for online mode)
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

    # ASR Configuration
    asr_gpu: bool = False
    asr_models: dict = {
        "fast": "tiny",
        "balanced": "base",
        "accurate": "small"
    }

    # Application Settings
    default_language: str = "es"
    supported_languages: list = ["es", "en"]
    max_conversation_length: int = 50
    emotion_markup_enabled: bool = True

    # Safety Settings
    safety_filter_enabled: bool = True
    max_response_time: int = 10  # seconds

    # Background Tasks
    enable_background_extraction: bool = True
    extraction_batch_size: int = 10

    # Embedding Configuration
    embedding_model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"
    embedding_dimension: int = 384
    embedding_batch_size: int = 32
    embedding_max_length: int = 512
    enable_semantic_search: bool = True
    semantic_search_limit: int = 5
    context_retrieval_limit: int = 3

    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()
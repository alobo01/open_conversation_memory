# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EmoRobCare is an offline conversational AI system for children 5-13 years old with TEA2 (Autism Spectrum Disorder Level 2). The system provides natural conversations with emotional feedback and semantic memory using local LLM processing.

### Core Architecture

The system follows a microservices architecture with Docker containers:

- **API Service** (`services/api/`): FastAPI backend handling `/conv`, `/kg`, and `/asr` endpoints
- **ASR Service** (`services/asr/`): Speech-to-text with Whisper/faster-whisper (3 precision tiers)
- **Frontend** (`services/frontend/`): Vue 3 + Vite interface served on port 81
- **Knowledge Graph** (`services/fuseki-job/`): Apache Jena Fuseki with OWL 2 DL + SHACL validation
- **Databases**: MongoDB (conversations), Qdrant (vector search), Fuseki (triple store)

### Key Technical Components

- **Conversation System**: LLM-based conversations with emotional markup (`**positive**`, `__calm__`, neutral)
- **Memory Architecture**: Hybrid storage with MongoDB + Qdrant + Fuseki for semantic search and knowledge graphs
- **Multi-tier ASR**: fast/balanced/accurate transcription levels
- **Background Processing**: Async extraction of conversation data to knowledge graph
- **Safety Layer**: Content validation and emotional appropriateness filtering

## Development Commands

### Setup and Installation
```bash
# Complete development environment setup
make setup

# Build all Docker images
make build

# Deploy all services locally
make deploy-local

# Stop all services
make stop
```

### Development Mode
```bash
# API development server (auto-reload)
make dev-api

# Frontend development server
make dev-ui

# Check service status
make status

# View API logs
make logs
```

### Testing and Quality
```bash
# Run all tests
make test

# Linting and formatting
make lint
make format

# Integration tests
make test-integration

# Performance tests
make test-performance
```

### API Testing Examples

#### Start Conversation
```bash
curl -X POST http://localhost:8000/conv/start \
  -H "Content-Type: application/json" \
  -d '{
    "child": "test_child",
    "topic": "school",
    "level": 3
  }'
```

#### Continue Conversation
```bash
curl -X POST http://localhost:8000/conv/next \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "conv_123",
    "user_sentence": "Me gusta el recreo",
    "end": false
  }'
```

#### ASR Transcription
```bash
# Fast tier
curl -X POST http://localhost:8001/asr/transcribe?tier=fast \
  -F "audio=@test_audio.wav"

# Balanced tier
curl -X POST http://localhost:8001/asr/transcribe?tier=balanced \
  -F "audio=@test_audio.wav"
```

## Code Architecture

### API Service Structure (`services/api/`)
- `main.py`: FastAPI application with lifespan management
- `routers/`: API endpoints organized by domain
  - `conversation.py`: /conv endpoints for conversation management
  - `knowledge_graph.py`: /kg endpoints for SPARQL operations
  - `asr.py`: /asr endpoints proxy to ASR service
- `services/`: Business logic layer
  - `llm_service.py`: LLM integration with vLLM
  - `memory_service.py`: Hybrid memory operations
  - `emotion_service.py`: Emotional markup and detection
- `models/`: Pydantic schemas and data models
- `core/`: Configuration, database, and utilities

### Frontend Structure (`services/frontend/`)
- Vue 3 + Composition API
- Naive UI component library
- Pinia for state management
- Audio recording with WebRTC
- Vite build system

### Database Schema
- **MongoDB Collections**: `children`, `conversations`, `messages`, `topics`, `profiles`
- **Qdrant Collections**: Vector embeddings for semantic search by child+topic
- **Fuseki Dataset**: RDF triples with OWL 2 DL ontology and SHACL validation

### Conversation Flow
1. Start conversation → Create profile if needed → Generate starting sentence
2. User input → ASR transcription → LLM response generation
3. Background task → Extract entities/relationships → Validate SHACL → Store in KG
4. Memory retrieval → Vector search + KG data → Enhanced context for next response

## Configuration

### Environment Variables
- `OFFLINE_MODE`: Use local LLM (true) or external API (false)
- `DEFAULT_LANG`: Default language (es/en)
- `ASR_GPU`: Enable GPU acceleration for ASR
- Database URLs: `MONGODB_URI`, `QDRANT_URL`, `FUSEKI_URL`

### Emotional Markup System
- `**text**`: Positive emphasis (¡Qué bien!)
- `__text__`: Calm whisper (tranquilo)
- `text`: Neutral tone

### Conversation Levels
- **1-2**: Simple sentences, one idea per sentence
- **3-4**: Basic connectors, simple structures
- **5**: Fluid conversation with varied vocabulary

## Testing Strategy

### Unit Tests
- Location: `tests/unit/`
- Coverage target: >80%
- Focus: Service layer business logic

### Integration Tests
- Location: `tests/integration/`
- Database-dependent tests with test fixtures
- API contract validation with schemathesis

### E2E Tests
- Full conversation flows through all services
- Docker compose test environment
- Performance benchmarking

## Development Notes

### Offline-First Design
- All models downloaded during Docker build
- No external dependencies required at runtime
- Local LLM (Qwen3) with vLLM serving

### Safety Considerations
- Content validation for child-appropriate responses
- Configurable topic restrictions per child profile
- No PII in logs or external communications

### Performance Targets
- Conversation response: <2s latency
- ASR fast tier: <1s, 85% accuracy
- Memory usage: <8GB total
- Docker images: <500MB per service

### Common Debugging Commands
```bash
# Check service health
curl http://localhost:8000/health
curl http://localhost:8001/health

# View logs
docker logs -f api
docker logs -f asr

# Database operations
docker exec -it mongodb mongosh emorobcare
curl http://localhost:3030/$$/stats  # Fuseki
```
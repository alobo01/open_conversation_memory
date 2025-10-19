# EmoRobCare Services & Port Assignments

## Service Architecture

EmoRobCare uses a microservices architecture with the following components:

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend (Port 81)                   │
│                    Vue 3 Web Interface                       │
└────────────┬─────────────────────────────────┬──────────────┘
             │                                 │
             ▼                                 ▼
    ┌────────────────┐                ┌────────────────┐
    │  API Service   │                │  ASR Service   │
    │   Port 8000    │                │   Port 5000    │
    │   (FastAPI)    │                │   (Whisper)    │
    └────────┬───────┘                └────────────────┘
             │
             ├──────────────┬──────────────┬──────────────┐
             ▼              ▼              ▼              ▼
      ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
      │ vLLM API │   │ MongoDB  │   │ Qdrant   │   │ Fuseki   │
      │ Port 8001│   │ Port     │   │ Port     │   │ Port     │
      │ (Qwen2)  │   │ 27017    │   │ 6333     │   │ 3030     │
      └──────────┘   └──────────┘   └──────────┘   └──────────┘
          GPU         Document        Vector         RDF
        Service       Database        Database      Triples
```

## Port Assignments

| Service | Internal Port | External Port | Protocol | Description |
|---------|--------------|---------------|----------|-------------|
| **Frontend** | 80 | 81 | HTTP | Vue 3 web interface |
| **API** | 8000 | 8000 | HTTP | FastAPI backend (conversation, memory, KG) |
| **vLLM** | 8000 | 8001 | HTTP | LLM inference service (OpenAI-compatible API) |
| **ASR** | 5000 | 5000 | HTTP | Whisper speech-to-text service |
| **MongoDB** | 27017 | 27017 | TCP | Document database (profiles, conversations) |
| **Qdrant** | 6333 | 6333 | HTTP | Vector database (semantic memory) |
| **Qdrant gRPC** | 6334 | 6334 | gRPC | Qdrant internal communication |
| **Fuseki** | 3030 | 3030 | HTTP | SPARQL endpoint (knowledge graph) |

## Service Details

### Frontend (Port 81)
- **Technology**: Vue 3 + Vite
- **Purpose**: Web interface for conversations
- **Dependencies**: API (8000), ASR (5000)
- **Access**: http://localhost:81

### API Service (Port 8000)
- **Technology**: FastAPI + Python 3.11
- **Purpose**: Core backend for conversations, memory, and knowledge graph
- **Key Endpoints**:
  - `/conv/*` - Conversation management
  - `/conv/memory/*` - Memory & context retrieval
  - `/kg/*` - Knowledge graph SPARQL queries
  - `/asr/*` - Speech-to-text proxy
- **Dependencies**: vLLM (8001), MongoDB (27017), Qdrant (6333), Fuseki (3030)
- **Access**: http://localhost:8000/docs (OpenAPI)

### vLLM Service (Port 8001) ⚠️ CRITICAL CHANGE
- **Technology**: vLLM with Qwen2-7B-Instruct
- **Purpose**: LLM inference via OpenAI-compatible API
- **Requirements**: NVIDIA GPU with CUDA support
- **API Format**: OpenAI-compatible (v1/completions, v1/chat/completions)
- **Access**: http://localhost:8001/v1/completions
- **Note**: API service uses HTTP client to call this, NOT direct import

**Key Configuration:**
```yaml
vllm:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
  command:
    - "--model"
    - "Qwen/Qwen2-7B-Instruct"
    - "--gpu-memory-utilization"
    - "0.6"
```

### ASR Service (Port 5000)
- **Technology**: faster-whisper
- **Purpose**: Speech-to-text transcription
- **Tiers**: fast, balanced, accurate
- **Access**: http://localhost:5000/asr/transcribe

### MongoDB (Port 27017)
- **Technology**: MongoDB 7
- **Purpose**: Document storage
- **Collections**:
  - `children` - Child profiles
  - `conversations` - Conversation sessions
  - `messages` - Individual messages
  - `topics` - Conversation topics
- **Access**: mongodb://localhost:27017

### Qdrant (Port 6333)
- **Technology**: Qdrant vector database
- **Purpose**: Semantic memory with embeddings
- **Model**: paraphrase-multilingual-MiniLM-L12-v2 (384D)
- **Collections**: `conversations`
- **Access**: http://localhost:6333/dashboard

### Fuseki (Port 3030)
- **Technology**: Apache Jena Fuseki
- **Purpose**: RDF triple store for knowledge graph
- **Dataset**: `emorobcare`
- **Ontology**: OWL 2 DL with SHACL validation
- **Access**: http://localhost:3030

## Docker Compose Commands

### Start all services:
```bash
docker-compose up -d
```

### Start specific service:
```bash
docker-compose up -d api
docker-compose up -d vllm
```

### View logs:
```bash
docker-compose logs -f api
docker-compose logs -f vllm
```

### Check service health:
```bash
docker-compose ps
```

### Stop all services:
```bash
docker-compose down
```

### Rebuild after code changes:
```bash
docker-compose up -d --build api
```

## Service Dependencies

**Startup order (handled by docker-compose):**
1. **Databases** (MongoDB, Qdrant, Fuseki) - Start first
2. **vLLM** - GPU service, slow to start (~2 min)
3. **API** - Waits for all databases + vLLM
4. **ASR** - Independent, can start anytime
5. **Frontend** - Waits for API + ASR

## Health Checks

All services include health checks:

```bash
# API
curl http://localhost:8000/health

# vLLM
curl http://localhost:8001/health

# ASR
curl http://localhost:5000/health

# Qdrant
curl http://localhost:6333/health

# Fuseki
curl http://localhost:3030/$$/stats
```

## Environment Variables

### API Service
```bash
MONGODB_URI=mongodb://mongodb:27017
QDRANT_URL=http://qdrant:6333
FUSEKI_URL=http://fuseki:3030
VLLM_API_URL=http://vllm:8000  # CRITICAL: HTTP client, not import
LLM_MODEL=Qwen/Qwen2-7B-Instruct
OFFLINE_MODE=true
DEFAULT_LANG=es
EMBEDDING_ENABLE_SEMANTIC_SEARCH=true
```

### vLLM Service
```bash
VLLM_HOST=0.0.0.0
VLLM_PORT=8000
VLLM_TRUST_REMOTE_CODE=true
```

## GPU Requirements

**vLLM Service:**
- NVIDIA GPU with CUDA support
- Minimum 8GB VRAM (for Qwen2-7B-Instruct)
- CUDA drivers installed
- nvidia-docker runtime configured

**Check GPU availability:**
```bash
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

## Development vs Production

### Development
```bash
# API in development mode
docker-compose up api --build
uvicorn main:app --reload

# Frontend in development mode
cd services/frontend
npm run dev
```

### Production
```bash
# All services optimized
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Troubleshooting

### vLLM service not starting
- Check GPU availability: `nvidia-smi`
- Check CUDA drivers installed
- Increase health check timeout (default 120s start_period)
- Check logs: `docker-compose logs vllm`

### API can't connect to vLLM
- Verify vLLM is healthy: `curl http://localhost:8001/health`
- Check `VLLM_API_URL` environment variable
- Verify docker network connectivity: `docker network inspect emorobcare-network`

### Memory/context retrieval slow
- Check Qdrant health: `curl http://localhost:6333/health`
- Monitor embedding generation time (should be < 200ms)
- Check semantic search limit configuration

### Knowledge graph validation errors
- Check Fuseki is running: `curl http://localhost:3030/$$/stats`
- Verify SHACL shapes loaded correctly
- Check logs for validation errors: `docker-compose logs api`

## Port Conflicts

If ports are already in use, modify `docker-compose.yml`:

```yaml
ports:
  - "8080:8000"  # Change external port (left side only)
```

**Common conflicts:**
- 27017 (MongoDB) - Often used by local MongoDB
- 8000 (API) - Common Python development port
- 81 (Frontend) - May conflict with other web services

## Security Notes

⚠️ **Development Configuration:**
- No authentication on services
- No encryption in transit
- All ports exposed on localhost
- Not suitable for production deployment

**For production:**
- Add authentication (JWT, OAuth)
- Enable TLS/SSL
- Use internal Docker network (no exposed ports)
- Add rate limiting
- Enable audit logging

## References

- **Docker Compose File**: `docker-compose.yml`
- **Architecture Changes**: `ARCHITECTURE_CHANGES.md`
- **Integration Summary**: `INTEGRATION_SUMMARY.md`
- **PRD**: `PRD.md`
- **Tasks**: `TASKS.md`

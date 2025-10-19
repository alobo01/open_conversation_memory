# Architecture Changes - Embedded Memory Integration

## Summary

This document summarizes the architectural changes made to integrate the embedded-memory system into the EmoRobCare project.

## Key Changes

### 1. vLLM Integration Pattern (CRITICAL)

**Previous**: vLLM imported directly into API service
**New**: vLLM accessed via HTTP API (OpenAI-compatible)

#### Rationale
- **Separation of concerns**: LLM inference is resource-intensive and should run independently
- **Scalability**: vLLM service can scale independently with GPU resources
- **Simplicity**: API service doesn't need vLLM dependencies
- **Docker optimization**: API container size reduced by ~2GB

#### Implementation
```python
# services/api/services/llm_service.py
import httpx

class LLMService:
    def __init__(self):
        self.api_url = settings.vllm_api_url  # "http://localhost:8001"
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def generate_response(self, prompt: str, **kwargs):
        response = await self.client.post(
            f"{self.api_url}/v1/completions",
            json={
                "model": settings.llm_model,
                "prompt": prompt,
                "max_tokens": kwargs.get("max_tokens", 150),
                "temperature": kwargs.get("temperature", 0.7)
            }
        )
        return response.json()["choices"][0]["text"]
```

#### Docker Setup
```yaml
services:
  vllm:
    image: vllm/vllm-openai:latest
    ports:
      - "8001:8000"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
  
  api:
    build: ./services/api
    environment:
      - VLLM_API_URL=http://vllm:8000
    depends_on:
      - vllm
```

### 2. Embedded-Memory Architecture

**Added**: Complete semantic memory system with vector embeddings

#### Components

##### Qdrant Vector Database
- **Model**: `paraphrase-multilingual-MiniLM-L12-v2` (384 dimensions)
- **Purpose**: Semantic search over conversation history
- **Features**: 
  - Automatic embedding of all messages
  - Filtering by child_id, topic, level
  - Similarity search with score threshold

##### Memory Service Extensions
New methods added to `services/api/services/memory_service.py`:
- `store_conversation()` - Automatic embedding and storage
- `search_similar_conversations()` - Semantic search
- `get_conversation_context()` - Context retrieval for RAG
- `get_memory_summary()` - Child memory summary

##### New API Endpoints
```
GET /conv/memory/{child_id}/context?topic=school&query=juegos&limit=3
GET /conv/memory/{child_id}/search?query=deportes&limit=5
GET /conv/memory/{child_id}/summary?topic=hobbies
DELETE /conv/memory/{conversation_id}
GET /conv/memory/status
```

#### Performance Targets
- **Context retrieval**: < 500ms
- **Embedding generation**: < 200ms per message
- **Search quality**: > 0.7 similarity score threshold

### 3. Knowledge Graph Extraction Pipeline

**Added**: Asynchronous entity extraction from conversations

#### Pipeline Flow
1. **Conversation ends** → Background task triggered
2. **Entity extraction** → vLLM API called with extraction prompt
3. **RDF generation** → Convert entities/relationships to triples
4. **SHACL validation** → Validate against `memoria.ttl` shapes
5. **KG insertion** → Insert validated triples into Fuseki

#### Extraction Prompt
Located at: `.claude/prompts/extract_entities.md`

Output format:
```json
{
  "entities": [
    {"type": "Activity", "value": "fútbol", "confidence": 0.9}
  ],
  "emotions": [
    {"type": "positive", "intensity": 0.8}
  ],
  "relationships": [
    {"subject": "child", "predicate": "likes", "object": "fútbol"}
  ],
  "topics": ["hobbies", "sports"]
}
```

#### SHACL Shapes
Located at: `ontology/memoria.ttl`

Key shapes:
- **ChildMemoryShape**: Links children to memory entries
- **MemoryEntryShape**: Validates memory entries with embeddings
- **ExtractedEntityShape**: Validates extracted entities (Activity, Place, Person, Object)

#### Performance Requirements
- **Extraction time**: < 30 seconds per conversation
- **Non-blocking**: Runs in background, doesn't delay responses
- **Validation rate**: < 5% SHACL violations

### 4. RAG (Retrieval-Augmented Generation)

**Added**: Context retrieval before LLM response generation

#### Process
1. User sends message to `/conv/next`
2. **Context retrieval** (< 500ms):
   - Semantic search in Qdrant (similar conversations)
   - SPARQL query in Fuseki (structured knowledge)
   - Combine and rank by relevance
3. **Context formatting** for LLM prompt
4. **LLM generation** with enriched context
5. **Response validation** and markup

#### Benefits
- Improved conversation coherence
- Reference to past topics/preferences
- Personalized responses based on child's history

## New Tasks

### Sprint 3 (Current)
1. **[CONV-000]** - Refactor LLM service for vLLM API (CRITICAL - 4 hours)
2. **[KG-006]** - Create memoria.ttl SHACL shapes (4 hours)
3. **[KG-007]** - Create entity extraction prompt (2 hours)
4. **[MEM-003]** - Implement extraction pipeline (16 hours)
5. **[MEM-004]** - Implement RAG in /conv (12 hours)

**Total effort**: ~38 hours (~1 week for 2 developers)

## Migration Path

### Step 1: vLLM API Client (Priority 1)
1. Update `services/api/services/llm_service.py` to use httpx
2. Add `vllm_api_url` to config
3. Update docker-compose.yml with separate vLLM service
4. Test with existing endpoints

### Step 2: SHACL & Prompts (Priority 2)
1. Create `ontology/memoria.ttl` with SHACL shapes
2. Create `.claude/prompts/extract_entities.md` template
3. Validate shapes with test data

### Step 3: Extraction Pipeline (Priority 3)
1. Implement `services/api/services/extraction_service.py`
2. Create `services/api/routers/background_tasks.py`
3. Add background task to `/conv/next` endpoint
4. Test extraction → validation → insertion flow

### Step 4: RAG Integration (Priority 4)
1. Extend `memory_service.get_conversation_context()`
2. Add context retrieval to `/conv/next` handler
3. Format context for LLM prompt
4. A/B testing and metrics

## Verification Checklist

- [ ] vLLM runs as separate container with GPU access
- [ ] API service uses HTTP client to call vLLM
- [ ] All memory endpoints respond correctly
- [ ] Automatic embedding of messages works
- [ ] Semantic search returns relevant results
- [ ] Extraction pipeline runs in background
- [ ] SHACL validation rejects invalid triples
- [ ] RAG improves conversation coherence
- [ ] Performance targets met (< 2s total response)
- [ ] Docker compose orchestrates all services

## Documentation Updates

### Updated Files
- ✅ `PRD.md` - Added embedded-memory architecture, vLLM API requirement, prompts/SHACL
- ✅ `TASKS.md` - Added CONV-000, KG-006, KG-007, updated MEM-003, MEM-004, DOCKER-001

### Existing Documentation
- `docs/memory_system.md` - Already comprehensive, no changes needed
- `LLM_INTEGRATION_README.md` - Will need update after vLLM API refactor
- `KNOWLEDGE_GRAPH_API.md` - Already covers SHACL validation

### New Documentation Needed
- `.claude/prompts/extract_entities.md` - Extraction prompt template
- `ontology/memoria.ttl` - SHACL shapes for memory

## References

- **Memory System Docs**: `docs/memory_system.md`
- **KG API Docs**: `KNOWLEDGE_GRAPH_API.md`
- **LLM Integration**: `LLM_INTEGRATION_README.md`
- **Memory Epic**: `TODOS/01-MEMORY_RETRIEVAL_EPIC.md`
- **Project Plan**: `PLAN.md`

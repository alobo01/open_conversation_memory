# Memory System Documentation

## Overview

The EmoRobCare Memory System provides semantic conversation memory capabilities using vector embeddings and similarity search. It enables the AI assistant to remember past conversations, understand context, and provide more coherent and personalized responses to children with TEA2.

## Architecture

### Core Components

1. **Memory Service** (`services/api/services/memory_service.py`)
   - Manages conversation embeddings and semantic search
   - Handles vector storage and retrieval
   - Provides context-aware conversation enhancement

2. **Vector Database** (Qdrant)
   - Stores conversation embeddings with metadata
   - Enables fast similarity search
   - Supports filtering by child, topic, and other attributes

3. **Embedding Model** (Sentence Transformers)
   - Multilingual support for Spanish/English
   - Optimized for semantic similarity
   - Removes emotion markup for better embedding quality

### Data Flow

```
Conversation Message → Text Cleaning → Embedding Generation → Vector Storage → Similarity Search → Context Retrieval
```

## Configuration

### Settings

Key configuration options in `services/api/core/config.py`:

```python
# Embedding Configuration
embedding_model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"
embedding_dimension: int = 384
embedding_batch_size: int = 32
embedding_max_length: int = 512
enable_semantic_search: bool = True
semantic_search_limit: int = 5
context_retrieval_limit: int = 3
```

### Environment Variables

```bash
# Enable/disable semantic search
EMBEDDING_ENABLE_SEMANTIC_SEARCH=true

# Qdrant configuration
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=conversations
```

## API Endpoints

### Memory Management

#### Get Child Memory Context
```http
GET /conv/memory/{child_id}/context
```

Parameters:
- `child_id` (path): Child identifier
- `topic` (query, optional): Filter by topic
- `query` (query, optional): Search query for context
- `limit` (query, optional): Number of context items (default: 3)

Response:
```json
{
  "child_id": "test_child",
  "topic": "hobbies",
  "query": "juegos",
  "context": [
    {
      "text": "Me gusta jugar al fútbol",
      "conversation_id": "conv_1",
      "score": 0.85,
      "timestamp": 1704110400
    }
  ],
  "count": 1
}
```

#### Search Child Memory
```http
GET /conv/memory/{child_id}/search
```

Parameters:
- `child_id` (path): Child identifier
- `query` (query, required): Search query
- `topic` (query, optional): Filter by topic
- `limit` (query, optional): Number of results (default: 5)

#### Get Memory Summary
```http
GET /conv/memory/{child_id}/summary
```

Parameters:
- `child_id` (path): Child identifier
- `topic` (query, optional): Filter by topic

#### Delete Conversation Memory
```http
DELETE /conv/memory/{conversation_id}
```

#### Get Memory Status
```http
GET /conv/memory/status
```

## Integration with Conversation System

### Automatic Embedding

The memory system automatically integrates with the conversation pipeline:

1. **Message Storage**: Each user and assistant message is automatically embedded and stored
2. **Context Retrieval**: Before generating responses, relevant context is retrieved from memory
3. **Background Processing**: Embedding operations run in background to avoid blocking responses

### Enhanced Response Generation

The conversation system uses semantic memory to:

1. **Understand Context**: Retrieve relevant past conversations
2. **Maintain Coherence**: Reference previous topics and preferences
3. **Personalize Responses**: Adapt to child's communication patterns

## Usage Examples

### Storing Conversations

```python
from services.api.services.memory_service import MemoryService

memory_service = MemoryService()

# Store conversation with metadata
await memory_service.store_conversation(
    conversation_id="conv_123",
    child_id="child_456",
    messages=[
        {"role": "user", "text": "Me gusta el fútbol", "timestamp": 1704110400},
        {"role": "assistant", "text": "**¡Qué bien!** ¿Qué posición juegas?", "timestamp": 1704110460}
    ],
    metadata={
        "topic": "hobbies",
        "level": 3,
        "language": "es"
    }
)
```

### Semantic Search

```python
# Search for similar conversations
results = await memory_service.search_similar_conversations(
    query="deportes y juegos",
    child_id="child_456",
    topic="hobbies",
    limit=5
)

for result in results:
    print(f"Text: {result['text']}")
    print(f"Score: {result['score']}")
    print(f"Conversation: {result['conversation_id']}")
```

### Context Retrieval

```python
# Get context for conversation enhancement
context = await memory_service.get_conversation_context(
    child_id="child_456",
    topic="hobbies",
    query="juegos divertidos",
    limit=3
)

# Use context in LLM prompt
enhanced_prompt = f"""
Context: {context}
User says: "Me gusta jugar"
Generate response considering the context.
"""
```

## Performance Considerations

### Embedding Optimization

1. **Batch Processing**: Messages are embedded in batches for efficiency
2. **Text Cleaning**: Emotion markup is removed before embedding
3. **Normalization**: Embeddings are normalized for better similarity search

### Search Optimization

1. **Score Thresholding**: Results below threshold are filtered out
2. **Duplicate Prevention**: Multiple messages from same conversation are deduplicated
3. **Limiting Results**: Search results are limited to prevent performance issues

### Memory Management

1. **Vector Dimensions**: Optimized for balance between quality and performance (384 dimensions)
2. **Distance Metric**: Cosine similarity for semantic relevance
3. **Metadata Indexing**: Efficient filtering by child, topic, and other attributes

## Testing

### Unit Tests

Run memory service unit tests:
```bash
pytest tests/unit/test_memory_service.py -v
```

### Integration Tests

Run API endpoint integration tests:
```bash
pytest tests/integration/test_memory_endpoints.py -v
```

### Performance Tests

Run performance benchmarks:
```bash
pytest tests/performance/test_memory_performance.py -v -s
```

## Troubleshooting

### Common Issues

1. **Memory Service Unavailable**
   - Check Qdrant connection
   - Verify embedding model is loaded
   - Check configuration settings

2. **Slow Performance**
   - Reduce embedding batch size
   - Check vector database indexing
   - Monitor memory usage

3. **Poor Search Results**
   - Verify text preprocessing
   - Check embedding model quality
   - Adjust similarity thresholds

### Debug Mode

Enable debug logging:
```python
import logging
logging.getLogger('services.api.services.memory_service').setLevel(logging.DEBUG)
```

### Health Check

Monitor memory service status:
```bash
curl http://localhost:8000/conv/memory/status
```

## Future Enhancements

### Planned Features

1. **Caching Layer**: Redis cache for frequent queries
2. **Advanced Filtering**: Time-based and emotion-based filters
3. **Conversation Summarization**: Topic extraction and summarization
4. **Cross-Child Learning**: Anonymized pattern learning
5. **Performance Monitoring**: Detailed metrics and alerting

### Optimization Opportunities

1. **Model Quantization**: Reduce embedding model size
2. **Approximate Search**: HNSW indexing for faster search
3. **Incremental Updates**: Selective re-embedding
4. **Compression**: Vector compression techniques

## Security and Privacy

### Data Protection

1. **Child Privacy**: No PII in embeddings or search indexes
2. **Data Encryption**: Encrypted storage and transmission
3. **Access Control**: Role-based access to memory data
4. **Data Retention**: Configurable retention policies

### Safety Considerations

1. **Content Filtering**: Inappropriate content filtering
2. **Context Boundaries**: Prevent context drift
3. **Response Validation**: Safe response generation
4. **Monitoring**: Anomaly detection and alerting

## Monitoring and Metrics

### Key Metrics

1. **Embedding Latency**: Time to generate embeddings
2. **Search Performance**: Query response time
3. **Storage Usage**: Vector database size
4. **Hit Rates**: Search result relevance

### Logging

The memory service logs:
- Embedding operations
- Search queries and results
- Performance metrics
- Error conditions

### Alerting

Set up alerts for:
- High embedding latency
- Low search performance
- Storage capacity limits
- Service unavailability
# 🧠 Memory & Retrieval Epic (MEM)

## Overview
Complete the memory and retrieval system to enable semantic search and knowledge graph extraction from conversations.

## Tasks

### MEM-003: Pipeline de extracción asíncrona ⏳ **HIGH PRIORITY**
**Status**: Pending
**Estimated**: 16 hours
**Dependencies**: KG-004 ✅, MEM-002 ✅
**Files to implement**:
- `services/api/services/extraction_service.py` (new)
- `services/api/routers/background_tasks.py` (new)
- `services/api/models/extraction_models.py` (new)

#### Subtasks:
- [ ] **Background Task Framework**: Implement FastAPI BackgroundTasks for async extraction
- [ ] **LLM Entity Extraction**: Create service to extract entities/relationships from conversations
- [ ] **Triple Generation**: Convert extracted entities to RDF triples format
- [ ] **SHACL Validation**: Validate generated triples before KG insertion
- [ ] **Error Handling**: Robust error handling for extraction failures
- [ ] **Queue Management**: Handle concurrent extraction requests
- [ ] **Logging**: Comprehensive logging for debugging extraction pipeline

#### Implementation Details:
```python
# services/api/services/extraction_service.py
class ExtractionService:
    async def extract_entities(self, conversation: Conversation) -> List[Entity]:
        """Extract entities from conversation using LLM"""

    async def generate_relationships(self, entities: List[Entity]) -> List[Relationship]:
        """Generate relationships between entities"""

    async def convert_to_rdf(self, entities: List[Entity], relationships: List[Relationship]) -> str:
        """Convert to RDF triples format"""
```

#### Acceptance Criteria:
- [ ] Extraction runs in background without blocking conversation flow
- [ ] Generated triples pass SHACL validation
- [ ] Error handling prevents KG corruption
- [ ] Performance: Extraction completes within 30 seconds per conversation
- [ ] Logging captures all extraction steps for debugging

---

### MEM-004: RAG en /conv ⏳ **HIGH PRIORITY**
**Status**: Pending
**Estimated**: 12 hours
**Dependencies**: MEM-003
**Files to modify**:
- `services/api/services/memory_service.py` (extend)
- `services/api/routers/conversation.py` (enhance)
- `services/api/models/conversation_models.py` (extend)

#### Subtasks:
- [ ] **Context Retrieval**: Enhance memory service to retrieve relevant context
- [ ] **Semantic Search Integration**: Use Qdrant to find similar past conversations
- [ ] **KG Data Integration**: Fuse KG data into conversation context
- [ ] **Context Ranking**: Rank retrieved context by relevance
- [ ] **Prompt Enhancement**: Integrate retrieved context into LLM prompts
- [ ] **Performance Optimization**: Ensure context retrieval < 500ms

#### Implementation Details:
```python
# Enhanced memory service
class MemoryService:
    async def get_conversation_context(self, child_id: str, topic: str, level: int) -> str:
        """Retrieve relevant context for conversation"""
        # 1. Vector search in Qdrant
        # 2. KG query for structured knowledge
        # 3. Format context for LLM prompt
```

#### Acceptance Criteria:
- [ ] Context retrieval improves conversation coherence
- [ ] Performance impact < 200ms additional latency
- [ ] Context is properly formatted for LLM consumption
- [ ] Handles cases with no relevant context gracefully
- [ ] A/B testing shows measurable improvement in conversation quality

---

## Cross-Cutting Dependencies

### Integration with Conversation Service
- [ ] **CONV-002 Enhancement**: Modify conversation endpoints to trigger background extraction
- [ ] **Context Integration**: Update conversation flow to use retrieved context
- [ ] **Testing**: Integration tests for complete flow

### Integration with Knowledge Graph
- [ ] **KG-004 Integration**: Use existing SPARQL endpoints for storing extracted data
- [ ] **Validation**: Ensure extracted data complies with SHACL shapes
- [ ] **Reasoning**: Prepare for HermiT reasoner integration (KG-005)

---

## Testing Requirements

### Unit Tests
- [ ] **ExtractionService Tests**: Test entity extraction accuracy
- [ ] **MemoryService Tests**: Test context retrieval and ranking
- [ ] **BackgroundTask Tests**: Test async task execution

### Integration Tests
- [ ] **End-to-End Extraction**: Test complete pipeline from conversation to KG
- [ ] **Context Integration**: Test conversation with retrieved context
- [ ] **Performance Tests**: Ensure latency requirements are met

### Performance Benchmarks
- [ ] **Extraction Speed**: < 30 seconds per conversation
- [ ] **Context Retrieval**: < 500ms for context gathering
- [ ] **Memory Usage**: Monitor memory consumption during extraction

---

## Success Metrics

### Functional Metrics
- [ ] **Extraction Accuracy**: > 80% correct entity identification
- [ ] **Context Relevance**: > 70% relevant context retrieval
- [ ] **Conversation Improvement**: Measurable improvement in conversation coherence

### Technical Metrics
- [ ] **Background Processing**: No blocking of conversation flow
- [ ] **Error Rate**: < 5% extraction failures
- [ ] **Performance Targets**: All latency targets met

---

## Risks & Mitigations

### Technical Risks
- **LLM Extraction Accuracy**: Mitigate with prompt engineering and validation
- **Background Task Overload**: Implement queue management and monitoring
- **KG Data Quality**: Multiple validation layers before insertion

### Performance Risks
- **Memory Usage**: Monitor and optimize for large conversation histories
- **Context Retrieval Latency**: Implement caching and optimization strategies
- **Background Task Contention**: Proper resource management

---

## Implementation Priority

### Phase 1 (Week 1)
1. Set up background task framework
2. Implement basic entity extraction
3. Create SHACL validation for extracted data

### Phase 2 (Week 2)
1. Implement context retrieval from Qdrant
2. Integrate KG data into conversation context
3. Complete performance optimization

### Phase 3 (Testing & Integration)
1. Comprehensive testing suite
2. Performance benchmarking
3. Integration with conversation endpoints

---

## Related Files & References

- `services/api/services/memory_service.py` - Extend for context retrieval
- `services/api/routers/knowledge_graph.py` - Use existing SPARQL endpoints
- `services/api/services/safety_service.py` - Coordinate with safety validation
- `tests/unit/test_memory_service.py` - Extend with new tests
- `docs/memory_system.md` - Update with new capabilities
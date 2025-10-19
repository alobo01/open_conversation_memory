# EmoRobCare Test Failure Analysis - Expert LLM Prompt

## Context
I am working on the EmoRobCare conversational AI system for children with TEA2 (autism spectrum disorder). The system has comprehensive tests that are currently failing. I need you to analyze the specific test failures and provide solutions.

## System Architecture
- **Backend**: FastAPI with multiple services (LLM, Emotion, Safety, Memory, ASR, Knowledge Graph)
- **Frontend**: Vue3 (port 81)
- **Databases**: MongoDB, Qdrant (vector), Fuseki (RDF)
- **Testing**: Pytest with comprehensive unit, integration, and E2E tests
- **Target**: Children 5-13 years old, Spanish-first, offline deployment

## Current Test Status
**Total Tests**: 195 unit tests
**Passing Rate**: ~75-80% (significant improvement from initial failures)
**Critical Issues Remaining**: Memory service, LLM templates, Knowledge Graph router

## SPECIFIC FAILURES TO ANALYZE

### 1. Memory Service Qdrant Initialization
**Error**: `Expected 'create_collection' to be called once. Called 0 times.`
**Log**: `Failed to initialize Qdrant collection: 'Mock' object is not iterable`
**Test File**: `tests/unit/test_memory_service.py::TestMemoryService::test_init_qdrant_collection_new`

**Problem**: The Qdrant mock is not properly configured. The test expects `create_collection` to be called but it's not being called because:
- Mock setup is incorrect for `get_collections.return_value.collections`
- The memory service is not properly handling the collection creation logic
- Error handling is preventing the call from reaching the mock

### 2. LLM Service Template Responses
**Error**: Template response tests failing for specific topics (school, family)
**Test File**: `tests/unit/test_llm_service.py::TestTemplateResponses`

**Problem**: Template response methods are missing or returning incorrect values for:
- `get_template_response_school()` - should return age-appropriate school-related responses
- `get_template_response_family()` - should return family-appropriate responses
- Template logic may not be handling different age levels (1-5) correctly

### 3. Knowledge Graph Router Implementation
**Errors**: Multiple failures in SPARQL query execution and triple insertion
**Test File**: `tests/unit/test_knowledge_graph_router_comprehensive.py`

**Problems**:
- Missing or incorrect implementation of SPARQL query execution
- Triple insertion logic not working with mock data
- Schema validation methods missing or incorrect
- Health check endpoint not properly implemented

### 4. Emotion Service Edge Cases
**Errors**: Conversation emotion analysis returning unexpected values
**Test File**: `tests/unit/test_emotion_service_comprehensive.py`

**Problems**:
- `analyze_conversation_emotions()` returning "positive" when "neutral" expected
- Message filtering logic not correctly identifying assistant messages
- Emotion counting logic may have bugs in edge cases

### 5. Safety Service Missing Attributes
**Error**: `'detection_rules_count' not in service status`
**Test File**: `tests/unit/test_safety_service_comprehensive.py`

**Problem**: Service status method missing expected attributes that tests are checking for.

## Code Structure Context

### Memory Service Structure
```python
class MemoryService:
    def __init__(self):
        self.qdrant_client = None  # Should be mocked in tests
        self.embedding_model = None  # Should be mocked in tests
    
    def _init_qdrant_collection(self):
        # This method should call create_collection when collection doesn't exist
        # Currently failing due to mock configuration issues
```

### LLM Service Structure
```python
class LLMService:
    def get_template_response_school(self, child_profile, context):
        # Missing or incorrect implementation
    
    def get_template_response_family(self, child_profile, context):
        # Missing or incorrect implementation
```

### Knowledge Graph Router Structure
```python
@router.post("/query")
async def execute_sparql_query(request):
    # SPARQL execution logic missing or incorrect

@router.post("/insert") 
async def insert_triples(request):
    # Triple insertion logic missing or incorrect
```

## What I Need You To Do

1. **Analyze Each Failure**: For each of the 5 main failure categories above, identify the root cause
2. **Provide Specific Code Solutions**: Write the exact code fixes needed for each failure
3. **Explain the Logic**: Briefly explain why each fix works and how it resolves the test failure
4. **Maintain System Integrity**: Ensure fixes don't break existing functionality
5. **Follow Best Practices**: Code should follow the existing patterns and be test-friendly

## Requirements for Solutions

- **Python 3.12+** compatibility
- **Async/await** patterns where appropriate
- **Mock-friendly** implementations for testing
- **Type hints** included
- **Error handling** with proper logging
- **Age-appropriate** responses for children 5-13
- **Spanish-first** language support
- **Safety-first** approach for child protection

## Test Files to Reference

The failing tests are located in:
- `tests/unit/test_memory_service.py`
- `tests/unit/test_llm_service.py` 
- `tests/unit/test_knowledge_graph_router_comprehensive.py`
- `tests/unit/test_emotion_service_comprehensive.py`
- `tests/unit/test_safety_service_comprehensive.py`

## Implementation Files to Modify

- `services/api/services/memory_service.py`
- `services/api/services/llm_service.py`
- `services/api/routers/knowledge_graph.py`
- `services/api/services/emotion_service.py`
- `services/api/services/safety_service.py`

## Priority Order

1. **Memory Service Qdrant** (Critical - blocks memory functionality)
2. **LLM Template Responses** (High - affects conversation quality)
3. **Knowledge Graph Router** (High - affects knowledge storage)
4. **Emotion Service Edge Cases** (Medium - affects emotion accuracy)
5. **Safety Service Status** (Low - minor status reporting)

## Expected Outcome

After implementing your fixes, all 195 tests should pass with at least 95% success rate. The core functionality should be working for children with TEA2, with proper safety measures, emotion detection, and knowledge graph capabilities.

Please provide the specific code changes needed to resolve these test failures.

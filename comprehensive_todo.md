# Comprehensive Test Improvement TODO List

## Priority 1: ASR Router Endpoint Fixes (Critical)
**Target**: Fix 20+ tests to get from 6/26 to 26/26 passing

### Subtask 1.1: Fix ASR Router Response Format
- [ ] Fix missing 'success' field in response format
- [ ] Ensure consistent JSON response structure
- [ ] Fix endpoint return values and status codes

### Subtask 1.2: Fix ASR Health Check Endpoint
- [ ] Implement proper health check endpoint
- [ ] Fix 404 errors for /asr/health
- [ ] Add service status monitoring

### Subtask 1.3: Fix ASR Mock Configuration
- [ ] Fix missing sample_audio_bytes variable
- [ ] Configure proper mock responses for transcription
- [ ] Fix async mock handling

### Subtask 1.4: Fix ASR Error Handling
- [ ] Fix timeout handling tests
- [ ] Fix parameter validation edge cases
- [ ] Fix concurrent request handling

## Priority 2: Knowledge Graph Router Fixes (High)
**Target**: Fix 33+ tests to get from 6/39 to 39/39 passing

### Subtask 2.1: Fix Knowledge Graph Endpoint Registration
- [ ] Ensure all endpoints are properly registered
- [ ] Fix 404 errors for all KG endpoints
- [ ] Verify FastAPI router configuration

### Subtask 2.2: Fix SPARQL Query Endpoint
- [ ] Implement proper SPARQL query execution
- [ ] Fix JSON response formatting
- [ ] Add proper error handling for invalid queries

### Subtask 2.3: Fix Triple Insertion Endpoint
- [ ] Implement proper triple insertion logic
- [ ] Fix validation of input data
- [ ] Add proper error responses

### Subtask 2.4: Fix Knowledge Graph Mock Configuration
- [ ] Configure proper mock for Fuseki/SPARQL endpoint
- [ ] Fix async mock handling
- [ ] Add proper response data mocking

### Subtask 2.5: Fix Schema Validation Endpoints
- [ ] Implement SHACL validation methods
- [ ] Fix schema validation response format
- [ ] Add proper error handling

## Priority 3: Emotion Service Edge Cases (Medium)
**Target**: Fix 6 tests to get from 32/38 to 38/38 passing

### Subtask 3.1: Fix Emotion Service Input Validation
- [ ] Fix None text handling in detect_emotion
- [ ] Fix invalid message handling in analyze_conversation_emotions
- [ ] Improve error handling for edge cases

### Subtask 3.2: Fix Emotion Analysis Logic
- [ ] Fix single message analysis edge cases
- [ ] Fix concurrent emotion detection issues
- [ ] Optimize memory usage for large analyses

## Priority 4: LLM Service Minor Fixes (Low)
**Target**: Minor improvements to maintain 100% pass rate

### Subtask 4.1: Fix LLM Response Format
- [ ] Fix emotional markup in local responses
- [ ] Ensure consistent response cleaning
- [ ] Fix response validation for edge cases

### Subtask 4.2: Fix LLM Health Check Edge Cases
- [ ] Fix unhealthy status detection
- [ ] Fix error status handling
- [ ] Improve health check accuracy

## Priority 5: Integration Test Fixes (Optional)
**Target**: Fix integration tests that were failing due to import errors

### Subtask 5.1: Fix Import Issues
- [ ] Fix relative import errors in conversation router
- [ ] Resolve import path issues for integration tests
- [ ] Fix main.py import configuration

### Subtask 5.2: Run Integration Tests
- [ ] Run API integration tests
- [ ] Run E2E conversation flow tests
- [ ] Run safety integration tests

## Success Metrics
- **Current**: 130/195 tests passing (66.7%)
- **Target**: 185+ tests passing (95%+ success rate)
- **Needed**: 55+ additional tests to pass

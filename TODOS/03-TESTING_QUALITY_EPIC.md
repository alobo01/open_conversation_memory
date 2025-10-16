# 🧪 Testing & Quality Epic (TEST)

## Overview
Implement comprehensive testing infrastructure for the EmoRobCare system to ensure reliability, safety, and performance for children with TEA2.

## Tasks

### TEST-001: Unit tests API ⏳ **HIGH PRIORITY**
**Status**: Partially implemented
**Estimated**: 24 hours
**Current State**: Basic tests exist for memory service
**Files to implement**:
- `tests/unit/test_conversation_service.py` (new)
- `tests/unit/test_safety_service.py` (new)
- `tests/unit/test_emotion_service.py` (new)
- `tests/unit/test_extraction_service.py` (new)
- `tests/unit/test_llm_service.py` (enhance)

#### Subtasks:
- [ ] **Conversation Service Tests**: Test conversation logic, level adaptation, emotion markup
- [ ] **Safety Service Tests**: Test content filtering, PII detection, age-appropriate validation
- [ ] **Emotion Service Tests**: Test emotion detection and markup accuracy
- [ ] **LLM Service Tests**: Test model integration, fallback mechanisms, performance
- [ ] **Extraction Service Tests**: Test entity extraction, triple generation, validation
- [ ] **Mock Dependencies**: Create comprehensive mocks for external services
- [ ] **Edge Case Testing**: Test error conditions and boundary cases
- [ ] **Coverage Analysis**: Achieve >80% code coverage for critical services

#### Implementation Details:
```python
# tests/unit/test_safety_service.py
import pytest
from services.api.services.safety_service import SafetyService

class TestSafetyService:
    def test_detects_pii_information(self):
        safety_service = SafetyService()
        unsafe_text = "Mi número de teléfono es 123-456-7890"
        result = safety_service.validate_content(unsafe_text, age=8)
        assert not result.is_safe
        assert "personal information" in result.reason

    def test_allows_child_appropriate_content(self):
        safety_service = SafetyService()
        safe_text = "Me gusta jugar en el parque con mis amigos"
        result = safety_service.validate_content(safe_text, age=8)
        assert result.is_safe

    def test_blocks_inappropriate_content(self):
        safety_service = SafetyService()
        unsafe_text = "Contenido inapropiado para niños"
        result = safety_service.validate_content(unsafe_text, age=8)
        assert not result.is_safe
```

#### Acceptance Criteria:
- [ ] Unit tests cover all critical business logic paths
- [ ] Mock services accurately simulate real dependencies
- [ ] Test coverage > 80% for all API services
- [ ] Tests run quickly (< 5 seconds for full suite)
- [ ] Tests are reliable and don't have flaky behavior

---

### TEST-002: Contract tests OpenAPI ⏳ **HIGH PRIORITY**
**Status**: Pending implementation
**Estimated**: 16 hours
**Dependencies**: TEST-001
**Files to implement**:
- `tests/contract/api_schema.yaml` (new)
- `tests/contract/test_api_contracts.py` (new)
- `tests/contract/schemathesis_config.py` (new)
- `tests/contract/fixtures/conversation_fixtures.py` (new)

#### Subtasks:
- [ ] **OpenAPI Schema Generation**: Generate comprehensive API schemas
- [ ] **Schemathesis Integration**: Set up automated API contract testing
- [ ] **Request/Response Validation**: Test all API endpoints against schemas
- [ ] **Error Response Testing**: Test error handling and status codes
- [ ] **Authentication Testing**: Test security and validation layers
- [ ] **Data Type Validation**: Test proper validation of all input types
- [ ] **Boundary Testing**: Test with edge cases and invalid data
- [ ] **CI Integration**: Integrate contract tests into CI pipeline

#### Implementation Details:
```python
# tests/contract/test_api_contracts.py
import pytest
import schemathesis
from hypothesis import given, strategies as st

# Load OpenAPI schema
schema = schemathesis.from_path("tests/contract/api_schema.yaml")

class TestAPIContracts:
    @schema.parametrize("/conv/start", "POST")
    def test_conversation_start_contract(self, case):
        response = case.call()
        case.validate_response(response)
        assert response.status_code == 200
        assert "conversation_id" in response.json()

    @schema.parametrize("/conv/next", "POST")
    @given(st.data())
    def test_conversation_next_contract(self, case, data):
        # Generate valid test data
        test_data = data.draw(st.fixed_dictionaries({
            "conversation_id": st.uuids(),
            "user_sentence": st.text(min_size=1, max_size=500),
            "end": st.booleans()
        }))

        response = case.call(json=test_data)
        case.validate_response(response)
```

#### Acceptance Criteria:
- [ ] All API endpoints have comprehensive OpenAPI schemas
- [ ] Schemathesis runs without contract violations
- [ ] Error handling is properly tested and documented
- [ ] Input validation works correctly for all endpoints
- [ ] Contract tests run in CI pipeline and prevent breaking changes

---

### TEST-003: E2E tests ⏳ **HIGH PRIORITY**
**Status**: Pending implementation
**Estimated**: 32 hours
**Dependencies**: TEST-002, UI-003
**Files to implement**:
- `tests/e2e/test_conversation_flow.py` (new)
- `tests/e2e/test_audio_integration.py` (new)
- `tests/e2e/test_memory_integration.py` (new)
- `tests/e2e/test_safety_integration.py` (new)
- `tests/e2e/fixtures/test_scenarios.py` (new)
- `tests/e2e/conftest.py` (new)

#### Subtasks:
- [ ] **Docker Test Environment**: Set up reproducible test environment
- [ ] **Conversation Flow Tests**: Test complete conversation scenarios
- [ ] **Audio Integration Tests**: Test audio recording to ASR to conversation flow
- [ ] **Memory Integration Tests**: Test knowledge graph extraction and retrieval
- [ ] **Safety Integration Tests**: Test safety validation across complete flows
- [ ] **Multi-user Scenarios**: Test concurrent conversations
- [ ] **Error Recovery Tests**: Test system behavior under error conditions
- [ ] **Performance Scenarios**: Test system under realistic load

#### Implementation Details:
```python
# tests/e2e/test_conversation_flow.py
import pytest
import asyncio
from playwright.async_api import async_playwright

class TestConversationFlow:
    @pytest.mark.asyncio
    async def test_complete_conversation_scenario(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            # Navigate to application
            await page.goto("http://localhost:81")

            # Select child profile
            await page.click("[data-testid=child-selector]")
            await page.click("[data-testid=child-test-user]")

            # Start conversation
            await page.click("[data-testid=start-conversation]")

            # Wait for AI response
            await page.wait_for_selector("[data-testid=ai-message]")

            # Record audio response
            await page.click("[data-testid=record-button]")
            await page.wait_for_timeout(2000)  # Record for 2 seconds
            await page.click("[data-testid=stop-recording]")

            # Wait for transcription and response
            await page.wait_for_selector("[data-testid=ai-message]:last-child")

            # Verify conversation flow
            messages = await page.locator("[data-testid=message]").count()
            assert messages >= 2  # At least AI and user message

            await browser.close()

    @pytest.mark.asyncio
    async def test_safety_filtering_integration(self):
        # Test that inappropriate content is properly filtered
        pass
```

#### Acceptance Criteria:
- [ ] E2E tests cover all major user workflows
- [ ] Tests run reliably in Docker environment
- [ ] Audio recording and ASR integration works end-to-end
- [ ] Safety filtering prevents inappropriate content
- [ ] Memory extraction and retrieval work correctly
- [ ] Tests complete within reasonable time (< 10 minutes)

---

### TEST-004: Linting + type checking ✅ **COMPLETED**
**Status**: Already implemented
**Estimated**: 4 hours
**Current State**: ruff, black, mypy configured

#### Verification Tasks:
- [ ] **Verify Pre-commit Hooks**: Ensure all hooks are properly configured
- [ ] **Test Configuration**: Run linting on all services
- [ ] **Type Coverage**: Ensure high type annotation coverage
- [ ] **CI Integration**: Verify linting runs in CI pipeline

---

### TEST-005: Performance tests ⏳ **MEDIUM PRIORITY**
**Status**: Pending implementation
**Estimated**: 20 hours
**Dependencies**: TEST-003
**Files to implement**:
- `tests/performance/test_conversation_latency.py` (new)
- `tests/performance/test_asr_performance.py` (new)
- `tests/performance/test_memory_performance.py` (new)
- `tests/performance/test_system_load.py` (new)
- `tests/performance/benchmark_scenarios.py` (new)

#### Subtasks:
- [ ] **Conversation Latency Tests**: Measure response times for conversation endpoints
- [ ] **ASR Performance Tests**: Benchmark transcription speed and accuracy
- [ ] **Memory Performance Tests**: Test retrieval and extraction performance
- [ ] **Load Testing**: Test system under concurrent user load
- [ ] **Memory Usage Tests**: Monitor memory consumption over time
- [ ] **CPU Usage Tests**: Monitor CPU utilization during peak usage
- [ ] **Database Performance**: Test query performance under load
- [ ] **Regression Testing**: Track performance changes over time

#### Implementation Details:
```python
# tests/performance/test_conversation_latency.py
import pytest
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor

class TestConversationPerformance:
    @pytest.mark.performance
    def test_conversation_response_time(self):
        """Test that conversation responses meet < 2s target"""
        start_time = time.time()

        response = self.client.post("/conv/start", json={
            "child": "test_child",
            "topic": "school",
            "level": 3
        })

        end_time = time.time()
        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 2.0, f"Response time {response_time}s exceeds 2s target"

    @pytest.mark.performance
    def test_concurrent_conversations(self):
        """Test system under concurrent load"""
        num_conversations = 10

        with ThreadPoolExecutor(max_workers=num_conversations) as executor:
            futures = []
            for i in range(num_conversations):
                future = executor.submit(self._run_conversation_scenario, f"child_{i}")
                futures.append(future)

            results = [future.result() for future in futures]

        # Verify all conversations completed successfully
        assert all(result['success'] for result in results)

        # Verify average response time is acceptable
        avg_time = sum(result['response_time'] for result in results) / len(results)
        assert avg_time < 2.5
```

#### Acceptance Criteria:
- [ ] Conversation response times < 2s target
- [ ] ASR transcription meets speed and accuracy targets
- [ ] System handles 10 concurrent conversations without degradation
- [ ] Memory usage remains stable under extended use
- [ ] Performance tests provide baseline metrics for monitoring

---

## Testing Infrastructure

### Test Environment Setup
- [ ] **Docker Compose Test Environment**: Separate test environment configuration
- [ ] **Test Data Management**: Automated test data setup and cleanup
- [ ] **Service Mocking**: Mock external dependencies for isolated testing
- [ ] **Database Fixtures**: Consistent test data for database-dependent tests

### Continuous Integration
- [ ] **GitHub Actions/CI Pipeline**: Automated testing on all PRs
- [ ] **Parallel Test Execution**: Run tests in parallel for faster feedback
- [ ] **Test Reporting**: Generate and publish test reports
- [ ] **Performance Regression Detection**: Alert on performance degradation

### Test Data Management
- [ ] **Child Profile Data**: Test profiles for different age groups and levels
- [ ] **Conversation Scenarios**: Pre-defined conversation test cases
- [ ] **Audio Test Files**: Sample audio files for ASR testing
- [ ] **Safety Test Cases**: Edge cases for safety validation

---

## Quality Gates

### Definition of Done
- [ ] **Unit Test Coverage**: >80% coverage for all new code
- [ ] **Integration Tests**: All new features have integration tests
- [ ] **Contract Tests**: All API changes pass contract validation
- [ ] **Performance Tests**: All performance targets met
- [ ] **Security Tests**: All security validations pass

### Release Criteria
- [ ] **All Tests Pass**: 100% test pass rate across all test suites
- [ ] **Performance Benchmarks**: No performance regression
- [ ] **Security Scan**: No security vulnerabilities detected
- [ ] **Accessibility Audit**: WCAG 2.1 AA compliance maintained
- [ ] **Documentation**: All new features documented

---

## Success Metrics

### Test Coverage Metrics
- [ ] **Unit Test Coverage**: >80% line coverage for all services
- [ ] **Integration Test Coverage**: >70% of critical paths tested
- [ ] **E2E Test Coverage**: >90% of user workflows tested
- [ ] **Contract Test Coverage**: 100% of API endpoints covered

### Quality Metrics
- [ ] **Bug Detection Rate**: >95% of bugs caught before production
- [ ] **Test Execution Time**: Full test suite completes in < 30 minutes
- [ ] **Test Reliability**: <1% flaky test rate
- [ ] **Performance Regression**: <5% performance degradation allowed

---

## Implementation Timeline

### Week 1
1. Complete TEST-001: Unit tests for all services
2. Set up test infrastructure and CI pipeline
3. Begin TEST-002: Contract testing setup

### Week 2
1. Complete TEST-002: Contract testing implementation
2. Begin TEST-003: E2E test development
3. Implement performance monitoring setup

### Week 3
1. Complete TEST-003: E2E testing implementation
2. Implement TEST-005: Performance testing
3. Final integration and optimization

---

## Related Files & References

- `tests/unit/test_memory_service.py` - Existing unit test examples
- `tests/integration/test_memory_endpoints.py` - Integration test patterns
- `tests/performance/test_memory_performance.py` - Performance test examples
- `services/api/conftest.py` - Test configuration and fixtures
- `docker-compose.test.yml` - Test environment configuration
- `pyproject.toml` - Testing dependencies and configuration
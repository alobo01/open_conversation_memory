import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import time

from services.api.services.llm_service import LLMService, VLLM_AVAILABLE


@pytest.fixture
def mock_settings():
    """Mock settings for LLM service"""
    settings = Mock()
    settings.llm_model = "qwen3-7b-instruct"
    settings.llm_temperature = 0.7
    settings.llm_max_tokens = 150
    settings.offline_mode = True
    return settings


@pytest.fixture
def mock_safety_service():
    """Mock safety service"""
    safety_service = Mock()
    safety_service.check_content_safety = AsyncMock()
    return safety_service


@pytest.fixture
def mock_vllm_model():
    """Mock vLLM model"""
    mock_model = Mock()

    # Mock successful generation with proper structure
    mock_output = Mock()
    mock_output.text = "**¡Qué bien!** Me encanta jugar contigo."
    
    mock_request_output = Mock()
    mock_request_output.outputs = [mock_output]
    
    # Mock generate method to return list of request outputs
    mock_model.generate = Mock(return_value=[mock_request_output])

    return mock_model


@pytest.fixture
def llm_service(mock_settings, mock_safety_service, mock_vllm_model):
    """Create LLM service instance with mocked dependencies"""
    with patch('services.api.services.llm_service.settings', mock_settings), \
         patch('services.api.services.llm_service.SafetyService', return_value=mock_safety_service), \
         patch('services.api.services.llm_service.VLLM_AVAILABLE', True), \
         patch('services.api.services.llm_service.LLM') as mock_llm_class:

        # Mock the LLM class to avoid initialization errors
        mock_llm_class.return_value = mock_vllm_model
        
        service = LLMService()
        service.model = mock_vllm_model
        service.model_ready = True
        service.generation_count = 0
        service.total_generation_time = 0.0

        return service


class TestLLMServiceInitialization:
    """Test LLM service initialization"""

    @patch('services.api.services.llm_service.VLLM_AVAILABLE', False)
    def test_init_vllm_unavailable(self, mock_settings, mock_safety_service):
        """Test initialization when vLLM is not available"""
        with patch('services.api.services.llm_service.settings', mock_settings), \
             patch('services.api.services.llm_service.SafetyService', return_value=mock_safety_service):

            service = LLMService()
            assert service.model_ready is False
            assert service.model is None

    def test_init_local_model_success(self, mock_settings, mock_safety_service):
        """Test successful local model initialization"""
        with patch('services.api.services.llm_service.settings', mock_settings), \
             patch('services.api.services.llm_service.SafetyService', return_value=mock_safety_service), \
             patch('services.api.services.llm_service.VLLM_AVAILABLE', True), \
             patch('services.api.services.llm_service.LLM') as mock_llm_class:

            # Mock successful model initialization
            mock_llm_instance = Mock()
            mock_output = Mock()
            mock_output.text = "test"
            mock_llm_instance.generate.return_value = [Mock(outputs=[mock_output])]
            mock_llm_class.return_value = mock_llm_instance

            service = LLMService()
            assert service.model_ready is True

    def test_init_local_model_failure(self, mock_settings, mock_safety_service):
        """Test local model initialization failure"""
        with patch('services.api.services.llm_service.settings', mock_settings), \
             patch('services.api.services.llm_service.SafetyService', return_value=mock_safety_service), \
             patch('services.api.services.llm_service.VLLM_AVAILABLE', True), \
             patch('services.api.services.llm_service.LLM', side_effect=Exception("Model load failed")):

            service = LLMService()
            assert service.model_ready is False
            assert service.model is None


class TestPromptBuilding:
    """Test prompt building functionality"""

    def test_build_prompt_basic(self, llm_service):
        """Test basic prompt building"""
        prompt = llm_service._build_prompt("Hola")

        assert "Hola" in prompt
        assert "Asistente:" in prompt
        assert "Niño:" in prompt

    def test_build_prompt_with_history(self, llm_service):
        """Test prompt building with conversation history"""
        history = [
            {"role": "user", "text": "Hola"},
            {"role": "assistant", "text": "**¡Hola!** ¿cómo estás?"}
        ]

        prompt = llm_service._build_prompt("Qué tal", history)

        assert "Hola" in prompt
        assert "¡Hola!" in prompt
        assert "Qué tal" in prompt

    def test_build_prompt_with_child_profile(self, llm_service):
        """Test prompt building with child profile"""
        child_profile = {
            "age": 6,
            "level": 2,
            "language": "es"
        }

        prompt = llm_service._build_prompt("Hola", child_profile=child_profile)

        assert "niños pequeños" in prompt.lower() or "niños" in prompt.lower()
        assert "frases cortas" in prompt.lower()

    def test_build_prompt_with_context(self, llm_service):
        """Test prompt building with context"""
        context = {
            "topic": "juegos",
            "level": 3
        }

        prompt = llm_service._build_prompt("Me gusta jugar", context=context)

        assert "Tema: juegos" in prompt
        assert "Nivel: 3" in prompt

    def test_get_system_prompt_spanish(self, llm_service):
        """Test Spanish system prompt generation"""
        child_profile = {"age": 8, "level": 3, "language": "es"}

        prompt = llm_service._get_system_prompt(child_profile)

        assert "asistente conversacional para niños" in prompt.lower()
        assert "**" in prompt  # Emotional markup instructions
        assert "__" in prompt  # Emotional markup instructions

    def test_get_system_prompt_english(self, llm_service):
        """Test English system prompt generation"""
        child_profile = {"age": 8, "level": 3, "language": "en"}

        prompt = llm_service._get_system_prompt(child_profile)

        assert "conversational assistant for children" in prompt.lower()
        assert "**" in prompt  # Emotional markup instructions
        assert "__" in prompt  # Emotional markup instructions

    def test_get_system_prompt_different_levels(self, llm_service):
        """Test system prompt for different levels"""
        levels = [1, 2, 3, 4, 5]

        for level in levels:
            child_profile = {"level": level, "language": "es"}
            prompt = llm_service._get_system_prompt(child_profile)
            assert len(prompt) > 50  # Ensure prompt is generated


class TestResponseGeneration:
    """Test response generation functionality"""

    @pytest.mark.asyncio
    async def test_generate_response_success(self, llm_service):
        """Test successful response generation"""
        child_profile = {
            "age": 8,
            "level": 3,
            "language": "es"
        }

        # Mock safety check to pass
        safety_result = Mock()
        safety_result.is_safe = True
        llm_service.safety_service.check_content_safety.return_value = safety_result

        response = await llm_service.generate_response(
            "Hola",
            child_profile=child_profile
        )

        assert response is not None
        assert len(response) > 0
        assert "**" in response  # Should contain emotional markup
        llm_service.safety_service.check_content_safety.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_response_safety_block(self, llm_service):
        """Test response generation when safety blocks the response"""
        child_profile = {
            "age": 8,
            "level": 3,
            "language": "es"
        }

        # Mock safety check to block
        safety_result = Mock()
        safety_result.is_safe = False
        safety_result.filtered_content = None
        safety_result.confidence = 0.5
        safety_result.violations = [Mock(violation_type=Mock(value="inappropriate"))]

        llm_service.safety_service.check_content_safety.return_value = safety_result
        llm_service._generate_safe_response = AsyncMock(return_value="**¡Hola!** ¿quieres jugar?")

        response = await llm_service.generate_response(
            "Hola",
            child_profile=child_profile
        )

        assert response is not None
        assert len(response) > 0
        llm_service._generate_safe_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_response_model_not_ready(self, llm_service):
        """Test response generation when model is not ready"""
        llm_service.model_ready = False

        response = await llm_service.generate_response("Hola")

        assert response is not None
        assert len(response) > 0
        # Should return fallback response
        assert any(phrase in response for phrase in ["disculpa", "entiendo", "vale", "claro", "perfecto"])

    @pytest.mark.asyncio
    async def test_generate_response_with_history(self, llm_service):
        """Test response generation with conversation history"""
        history = [
            {"role": "user", "text": "Hola"},
            {"role": "assistant", "text": "**¡Hola!** ¿cómo estás?"}
        ]

        child_profile = {"language": "es"}
        safety_result = Mock(is_safe=True)
        llm_service.safety_service.check_content_safety.return_value = safety_result

        response = await llm_service.generate_response(
            "Bien, gracias",
            conversation_history=history,
            child_profile=child_profile
        )

        assert response is not None
        assert len(response) > 0


class TestLocalGeneration:
    """Test local LLM generation"""

    @pytest.mark.asyncio
    async def test_generate_local_success(self, llm_service):
        """Test successful local generation"""
        llm_service.model_ready = True

        response = await llm_service._generate_local("Hola")

        assert response is not None
        assert len(response) > 0
        assert "**" in response  # Should contain emotional markup

    @pytest.mark.asyncio
    async def test_generate_local_model_not_ready(self, llm_service):
        """Test local generation when model is not ready"""
        llm_service.model_ready = False

        response = await llm_service._generate_local("Hola")

        assert response is not None
        # Should return fallback response
        assert any(phrase in response for phrase in ["disculpa", "entiendo", "vale", "claro", "perfecto"])

    @pytest.mark.asyncio
    async def test_generate_local_generation_failure(self, llm_service):
        """Test local generation when generation fails"""
        llm_service.model.generate.side_effect = Exception("Generation failed")

        response = await llm_service._generate_local("Hola")

        assert response is not None
        # Should return fallback response
        assert any(phrase in response for phrase in ["disculpa", "entiendo", "vale", "claro", "perfecto"])

    def test_clean_response(self, llm_service):
        """Test response cleaning"""
        # Test with artifacts
        dirty_response = "Asistente: **¡Hola!** ¿cómo estás?\nNiño: estoy bien\nAsistente: **¡Genial!**"
        clean_response = llm_service._clean_response(dirty_response)

        assert "Asistente:" not in clean_response
        assert "Niño:" not in clean_response
        assert "**¡Hola!**" in clean_response

    def test_clean_response_empty(self, llm_service):
        """Test cleaning empty response"""
        response = llm_service._clean_response("")
        assert response == ""

    def test_validate_response_valid(self, llm_service):
        """Test response validation with valid response"""
        valid_response = "**¡Qué bien!** Me encanta jugar contigo."
        assert llm_service._validate_response(valid_response) is True

    def test_validate_response_too_long(self, llm_service):
        """Test response validation with too long response"""
        long_response = "a" * 600  # Over 500 character limit
        assert llm_service._validate_response(long_response) is False

    def test_validate_response_empty(self, llm_service):
        """Test response validation with empty response"""
        assert llm_service._validate_response("") is False
        assert llm_service._validate_response("   ") is False

    def test_validate_response_repetitive(self, llm_service):
        """Test response validation with repetitive response"""
        repetitive_response = "hola hola hola hola hola hola hola hola hola hola hola hola"
        assert llm_service._validate_response(repetitive_response) is False

    def test_has_appropriate_tone(self, llm_service):
        """Test appropriate tone detection"""
        positive_response = "**¡Qué bien!** Me gusta jugar."
        assert llm_service._has_appropriate_tone(positive_response) is True

        neutral_response = "Esto es una respuesta."
        assert llm_service._has_appropriate_tone(neutral_response) is False


class TestTemplateResponses:
    """Test template-based responses"""

    @pytest.mark.asyncio
    async def test_get_template_response_playing(self, llm_service):
        """Test template response for playing topic"""
        response = await llm_service._get_template_response("Me gusta jugar")

        assert response is not None
        assert len(response) > 0
        assert any(word in response.lower() for word in ["jugar", "juego", "divertido"])

    @pytest.mark.asyncio
    async def test_get_template_response_school(self, llm_service):
        """Test template response for school topic"""
        response = await llm_service._get_template_response("Hoy en la escuela...")

        assert response is not None
        assert len(response) > 0
        assert any(word in response.lower() for word in ["escuela", "colegio", "aprendiste"])

    @pytest.mark.asyncio
    async def test_get_template_response_family(self, llm_service):
        """Test template response for family topic"""
        response = await llm_service._get_template_response("Mi mamá dice...")

        assert response is not None
        assert len(response) > 0
        assert any(word in response.lower() for word in ["familia", "mamá", "papá"])

    @pytest.mark.asyncio
    async def test_get_template_response_general(self, llm_service):
        """Test template response for general topic"""
        response = await llm_service._get_template_response("Me gusta esto")

        assert response is not None
        assert len(response) > 0
        assert "**" in response or "__" in response  # Should contain emotional markup


class TestSafeResponses:
    """Test safe response generation"""

    @pytest.mark.asyncio
    async def test_generate_safe_response_spanish(self, llm_service):
        """Test safe response generation in Spanish"""
        child_profile = {
            "age": 8,
            "level": 3,
            "language": "es"
        }

        response = await llm_service._generate_safe_response(child_profile)

        assert response is not None
        assert len(response) > 0
        assert "**" in response or "__" in response

    @pytest.mark.asyncio
    async def test_generate_safe_response_english(self, llm_service):
        """Test safe response generation in English"""
        child_profile = {
            "age": 8,
            "level": 3,
            "language": "en"
        }

        response = await llm_service._generate_safe_response(child_profile)

        assert response is not None
        assert len(response) > 0
        assert "**" in response or "__" in response

    @pytest.mark.asyncio
    async def test_generate_safe_response_different_levels(self, llm_service):
        """Test safe response generation for different levels"""
        for level in [1, 2, 3, 4, 5]:
            child_profile = {
                "level": level,
                "language": "es"
            }

            response = await llm_service._generate_safe_response(child_profile)

            assert response is not None
            assert len(response) > 0

    def test_get_fallback_response(self, llm_service):
        """Test fallback response generation"""
        response = llm_service._get_fallback_response()

        assert response is not None
        assert len(response) > 0
        assert any(phrase in response for phrase in ["disculpa", "entiendo", "vale", "perfecto"])


class TestHealthChecks:
    """Test health check functionality"""

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, llm_service):
        """Test health check when service is healthy"""
        llm_service.model_ready = True
        llm_service.generation_count = 10
        llm_service.total_generation_time = 5.0

        health = await llm_service.health_check()

        assert health["status"] == "healthy"
        assert health["model_ready"] is True
        assert health["offline_mode"] is True
        assert health["generation_count"] == 10
        assert health["avg_response_time"] == 0.5

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, llm_service):
        """Test health check when service is unhealthy"""
        llm_service.model.generate.return_value = []  # Empty output

        health = await llm_service.health_check()

        assert health["status"] == "unhealthy"
        assert health["model_ready"] is False

    @pytest.mark.asyncio
    async def test_health_check_limited(self, llm_service):
        """Test health check when service is in limited mode"""
        llm_service.offline_mode = False

        health = await llm_service.health_check()

        assert health["status"] == "limited"
        assert health["fallback_responses"] is True

    @pytest.mark.asyncio
    async def test_health_check_error(self, llm_service):
        """Test health check when error occurs"""
        llm_service.model.generate.side_effect = Exception("Health check failed")

        health = await llm_service.health_check()

        assert health["status"] == "error"
        assert "error" in health


class TestModelStatus:
    """Test model status functionality"""

    @pytest.mark.asyncio
    async def test_get_model_status_ready(self, llm_service):
        """Test getting model status when ready"""
        llm_service.model_ready = True
        llm_service.generation_count = 5
        llm_service.total_generation_time = 2.5

        status = await llm_service.get_model_status()

        assert status["ready"] is True
        assert status["offline_mode"] is True
        assert status["generation_count"] == 5
        assert status["avg_response_time"] == 0.5
        assert "health" in status

    @pytest.mark.asyncio
    async def test_get_model_status_not_ready(self, llm_service):
        """Test getting model status when not ready"""
        llm_service.model_ready = False
        llm_service.model = None  # Also set model to None when not ready

        status = await llm_service.get_model_status()

        assert status["ready"] is False
        assert status["model_loaded"] is False

    def test_get_performance_grade(self, llm_service):
        """Test performance grade calculation"""
        assert llm_service._get_performance_grade(0) == "No data"
        assert llm_service._get_performance_grade(0.5) == "Excellent"
        assert llm_service._get_performance_grade(1.2) == "Good"
        assert llm_service._get_performance_grade(1.8) == "Acceptable"
        assert llm_service._get_performance_grade(2.5) == "Slow"
        assert llm_service._get_performance_grade(5.0) == "Very Slow"


class TestKnowledgeGraphHelpers:
    """Test knowledge graph helper functions"""

    @pytest.mark.asyncio
    async def test_extract_entities(self, llm_service):
        """Test entity extraction"""
        text = "Juan juega con María en el parque"

        entities = await llm_service.extract_entities(text)

        assert isinstance(entities, list)
        # Currently returns empty list, but interface should work

    @pytest.mark.asyncio
    async def test_extract_relationships(self, llm_service):
        """Test relationship extraction"""
        text = "Juan es amigo de María"

        relationships = await llm_service.extract_relationships(text)

        assert isinstance(relationships, list)
        # Currently returns empty list, but interface should work

    @pytest.mark.asyncio
    async def test_summarize_conversation(self, llm_service):
        """Test conversation summarization"""
        messages = [
            {"role": "user", "text": "Hola"},
            {"role": "assistant", "text": "**¡Hola!** ¿cómo estás?"},
            {"role": "user", "text": "Bien"},
            {"role": "assistant", "text": "**¡Genial!** ¿qué quieres hacer?"}
        ]

        summary = await llm_service.summarize_conversation(messages)

        assert summary is not None
        assert len(summary) > 0

    @pytest.mark.asyncio
    async def test_summarize_short_conversation(self, llm_service):
        """Test summarization of short conversation"""
        messages = [
            {"role": "user", "text": "Hola"},
            {"role": "assistant", "text": "**¡Hola!**"}
        ]

        summary = await llm_service.summarize_conversation(messages)

        assert summary == "Conversación corta"


class TestEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_generate_response_empty_prompt(self, llm_service):
        """Test generation with empty prompt"""
        child_profile = {"language": "es"}
        safety_result = Mock(is_safe=True)
        llm_service.safety_service.check_content_safety.return_value = safety_result

        response = await llm_service.generate_response("")

        assert response is not None
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_generate_response_very_long_prompt(self, llm_service):
        """Test generation with very long prompt"""
        long_prompt = "hola " * 1000
        child_profile = {"language": "es"}
        safety_result = Mock(is_safe=True)
        llm_service.safety_service.check_content_safety.return_value = safety_result

        response = await llm_service.generate_response(long_prompt)

        assert response is not None

    @pytest.mark.asyncio
    async def test_generate_response_safety_service_error(self, llm_service):
        """Test generation when safety service raises error"""
        llm_service.safety_service.check_content_safety.side_effect = Exception("Safety error")

        response = await llm_service.generate_response("Hola")

        assert response is not None
        # Should still return a response despite safety error

    @pytest.mark.asyncio
    async def test_online_generation_fallback(self, llm_service):
        """Test online generation fallback to template"""
        llm_service.offline_mode = False

        response = await llm_service._generate_online("Hola")

        assert response is not None
        assert len(response) > 0

    def test_model_lock_thread_safety(self, llm_service):
        """Test that model lock provides thread safety"""
        # This is a basic test to ensure lock exists
        assert hasattr(llm_service, 'model_lock')
        assert llm_service.model_lock is not None

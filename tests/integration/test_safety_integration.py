import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from datetime import datetime

from services.api.main import app
from services.api.models.schemas import EmotionType, Topic, ConversationLevel


class TestSafetyIntegration:
    """Integration tests for safety layer in conversation flow"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    def mock_db(self):
        """Mock database for testing"""
        return Mock()

    @pytest.fixture
    def sample_conversation_start(self):
        """Sample conversation start request"""
        return {
            "child": "test_child_123",
            "topic": "hobbies",
            "level": 3
        }

    @pytest.fixture
    def sample_child_profile(self):
        """Sample child profile with safety settings"""
        return {
            "child_id": "test_child_123",
            "name": "Test Child",
            "age": 8,
            "preferred_topics": ["juegos", "escuela"],
            "blocked_topics": ["violencia", "muerte", "miedo"],
            "sensitive_topics": ["separación", "accidentes"],
            "level": 3,
            "sensitivity": "high",
            "language": "es"
        }


class TestConversationSafetyIntegration:
    """Test safety integration in conversation endpoints"""

    @patch('services.api.routers.conversation.get_db')
    @patch('services.api.routers.conversation.memory_service')
    @patch('services.api.routers.conversation.safety_service')
    def test_safe_conversation_start(self, mock_safety, mock_memory, mock_get_db,
                                   client, sample_conversation_start, sample_child_profile):
        """Test that conversation start works normally with safe content"""
        # Mock database responses
        mock_db = Mock()
        mock_db.profiles.find_one.return_value = sample_child_profile
        mock_db.conversations.insert_one.return_value = Mock()
        mock_db.messages.insert_one.return_value = Mock()
        mock_get_db.return_value = mock_db

        # Mock safety service to return safe result
        mock_safety.check_content_safety.return_value = AsyncMock(
            return_value=Mock(is_safe=True, violations=[], filtered_content=None)
        )
        mock_safety.get_service_status.return_value = {"status": "active"}

        response = client.post("/conv/start", json=sample_conversation_start)

        assert response.status_code == 200
        data = response.json()
        assert "conversation_id" in data
        assert "starting_sentence" in data
        assert data["end"] is False

    @patch('services.api.routers.conversation.get_db')
    @patch('services.api.routers.conversation.memory_service')
    @patch('services.api.routers.conversation.safety_service')
    def test_conversation_continue_with_safety_violation(self, mock_safety, mock_memory, mock_get_db,
                                                       client, sample_child_profile):
        """Test that unsafe responses are handled appropriately"""
        # Mock database responses
        mock_db = Mock()
        mock_db.conversations.find_one.return_value = {
            "conversation_id": "test_conv_123",
            "child_id": "test_child_123",
            "topic": "hobbies",
            "level": 3,
            "language": "es"
        }
        mock_db.messages.insert_one.return_value = Mock()
        mock_db.conversations.update_one.return_value = Mock()
        mock_get_db.return_value = mock_db

        # Mock safety service to return unsafe result
        mock_safety.check_content_safety.return_value = AsyncMock(
            return_value=Mock(
                is_safe=False,
                violations=[Mock(violation_type="violence", severity="high")],
                filtered_content=None,
                confidence=0.5
            )
        )
        mock_safety.get_safe_alternative_topic.return_value = AsyncMock(return_value="juegos")
        mock_safety.get_service_status.return_value = {"status": "active"}

        conversation_next = {
            "conversation_id": "test_conv_123",
            "user_sentence": "quiero matar al monstruo",
            "end": False
        }

        response = client.post("/conv/next", json=conversation_next)

        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        # Response should be safe alternative
        assert "matar" not in data["reply"].lower()
        assert data["end"] is False

    @patch('services.api.routers.conversation.get_db')
    @patch('services.api.routers.conversation.memory_service')
    @patch('services.api.routers.conversation.safety_service')
    def test_conversation_with_filtered_content(self, mock_safety, mock_memory, mock_get_db,
                                             client, sample_child_profile):
        """Test that filtered content is used when available"""
        # Mock database responses
        mock_db = Mock()
        mock_db.conversations.find_one.return_value = {
            "conversation_id": "test_conv_123",
            "child_id": "test_child_123",
            "topic": "hobbies",
            "level": 3,
            "language": "es"
        }
        mock_db.messages.insert_one.return_value = Mock()
        mock_db.conversations.update_one.return_value = Mock()
        mock_get_db.return_value = mock_db

        # Mock safety service to return filtered content
        mock_safety.check_content_safety.return_value = AsyncMock(
            return_value=Mock(
                is_safe=False,
                violations=[Mock(violation_type="violence", severity="medium")],
                filtered_content="¿quieres derrotar al monstruo en un juego?",
                confidence=0.8
            )
        )
        mock_safety.get_service_status.return_value = {"status": "active"}

        conversation_next = {
            "conversation_id": "test_conv_123",
            "user_sentence": "quiero matar al monstruo",
            "end": False
        }

        response = client.post("/conv/next", json=conversation_next)

        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        # Should use filtered content
        assert "derrotar" in data["reply"].lower()
        assert "juego" in data["reply"].lower()
        assert "matar" not in data["reply"].lower()

    @patch('services.api.routers.conversation.get_db')
    @patch('services.api.routers.conversation.memory_service')
    @patch('services.api.routers.conversation.safety_service')
    def test_conversation_with_personal_info_protection(self, mock_safety, mock_memory, mock_get_db,
                                                      client, sample_child_profile):
        """Test that personal information is protected"""
        # Mock database responses
        mock_db = Mock()
        mock_db.conversations.find_one.return_value = {
            "conversation_id": "test_conv_123",
            "child_id": "test_child_123",
            "topic": "hobbies",
            "level": 3,
            "language": "es"
        }
        mock_db.messages.insert_one.return_value = Mock()
        mock_db.conversations.update_one.return_value = Mock()
        mock_get_db.return_value = mock_db

        # Mock safety service to detect and filter personal info
        mock_safety.check_content_safety.return_value = AsyncMock(
            return_value=Mock(
                is_safe=False,
                violations=[Mock(violation_type="personal_info", severity="critical")],
                filtered_content="mi información de contacto está protegida",
                confidence=0.9
            )
        )
        mock_safety.get_service_status.return_value = {"status": "active"}

        conversation_next = {
            "conversation_id": "test_conv_123",
            "user_sentence": "mi email es niño@ejemplo.com",
            "end": False
        }

        response = client.post("/conv/next", json=conversation_next)

        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        # Should not contain personal information
        assert "niño@ejemplo.com" not in data["reply"]

    @patch('services.api.routers.conversation.get_db')
    @patch('services.api.routers.conversation.memory_service')
    @patch('services.api.routers.conversation.safety_service')
    def test_conversation_with_age_appropriate_responses(self, mock_safety, mock_memory, mock_get_db,
                                                        client):
        """Test that responses are age-appropriate"""
        # Mock database with young child
        young_child = {
            "child_id": "young_child",
            "name": "Young Child",
            "age": 5,
            "preferred_topics": ["juegos"],
            "blocked_topics": ["miedo", "monstruos"],
            "level": 1,
            "sensitivity": "high",
            "language": "es"
        }

        mock_db = Mock()
        mock_db.conversations.find_one.return_value = {
            "conversation_id": "test_conv_123",
            "child_id": "young_child",
            "topic": "hobbies",
            "level": 1,
            "language": "es"
        }
        mock_db.messages.insert_one.return_value = Mock()
        mock_db.conversations.update_one.return_value = Mock()
        mock_get_db.return_value = mock_db

        # Mock safety service to detect complex language
        mock_safety.check_content_safety.return_value = AsyncMock(
            return_value=Mock(
                is_safe=False,
                violations=[Mock(violation_type="language_complexity", severity="medium")],
                filtered_content="¿quieres jugar?",
                confidence=0.7
            )
        )
        mock_safety.get_service_status.return_value = {"status": "active"}

        conversation_next = {
            "conversation_id": "test_conv_123",
            "user_sentence": "¿qué pasa?",
            "end": False
        }

        response = client.post("/conv/next", json=conversation_next)

        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        # Response should be simple and age-appropriate
        reply = data["reply"]
        assert len(reply.split()) <= 5  # Should be short for young children


class TestLLMServiceSafetyIntegration:
    """Test safety integration with LLM service"""

    @pytest.mark.asyncio
    async def test_llm_service_safety_validation(self):
        """Test that LLM service validates responses for safety"""
        from services.api.services.llm_service import LLMService

        # Mock safety service
        with patch('services.api.services.llm_service.SafetyService') as mock_safety_class:
            mock_safety = Mock()
            mock_safety.check_content_safety.return_value = AsyncMock(
                return_value=Mock(is_safe=True, violations=[], filtered_content=None)
            )
            mock_safety_class.return_value = mock_safety

            llm_service = LLMService()
            child_profile = {
                "child_id": "test_child",
                "age": 8,
                "level": 3,
                "language": "es"
            }

            # Mock the model to return some response
            with patch.object(llm_service, '_generate_local') as mock_generate:
                mock_generate.return_value = "respuesta segura y apropiada"

                response = await llm_service.generate_response(
                    prompt="hola",
                    child_profile=child_profile
                )

                assert response == "respuesta segura y apropiada"
                # Verify safety check was called
                mock_safety.check_content_safety.assert_called_once()

    @pytest.mark.asyncio
    async def test_llm_service_blocked_response(self):
        """Test that LLM service blocks unsafe responses"""
        from services.api.services.llm_service import LLMService

        # Mock safety service
        with patch('services.api.services.llm_service.SafetyService') as mock_safety_class:
            mock_safety = Mock()
            mock_safety.check_content_safety.return_value = AsyncMock(
                return_value=Mock(
                    is_safe=False,
                    violations=[Mock(violation_type="violence")],
                    filtered_content=None,
                    confidence=0.5
                )
            )
            mock_safety_class.return_value = mock_safety

            llm_service = LLMService()
            child_profile = {
                "child_id": "test_child",
                "age": 8,
                "level": 3,
                "language": "es"
            }

            # Mock the model to return unsafe response
            with patch.object(llm_service, '_generate_local') as mock_generate:
                mock_generate.return_value = "contenido violento e inseguro"

                response = await llm_service.generate_response(
                    prompt="hola",
                    child_profile=child_profile
                )

                # Should return safe alternative
                assert response != "contenido violento e inseguro"
                # Verify safety check was called
                mock_safety.check_content_safety.assert_called_once()


class TestSafetyServicePerformance:
    """Test safety service performance characteristics"""

    @pytest.mark.asyncio
    async def test_safety_check_performance(self, safety_service, sample_child_profile):
        """Test that safety checks perform within acceptable time limits"""
        import time

        content = "me gusta jugar en el parque con mis amigos"
        context = {"topic": "juegos", "level": 3}

        start_time = time.time()

        # Perform multiple safety checks
        for _ in range(10):
            await safety_service.check_content_safety(
                content=content,
                child_profile=sample_child_profile,
                context=context,
                language="es"
            )

        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / 10

        # Safety checks should be fast (< 100ms per check on average)
        assert avg_time < 0.1, f"Safety check too slow: {avg_time:.3f}s"

    @pytest.mark.asyncio
    async def test_safety_check_concurrent_requests(self, safety_service, sample_child_profile):
        """Test safety service handles concurrent requests"""
        import asyncio

        async def check_safety():
            content = "contenido seguro para niños"
            context = {"topic": "juegos", "level": 3}

            return await safety_service.check_content_safety(
                content=content,
                child_profile=sample_child_profile,
                context=context,
                language="es"
            )

        # Run 20 concurrent safety checks
        tasks = [check_safety() for _ in range(20)]
        results = await asyncio.gather(*tasks)

        # All should complete successfully
        assert len(results) == 20
        assert all(result.is_safe for result in results)


class TestSafetyErrorHandling:
    """Test error handling in safety layer"""

    @pytest.mark.asyncio
    async def test_safety_service_error_fallback(self):
        """Test that safety service handles errors gracefully"""
        safety_service = SafetyService()
        child_profile = {"age": 8, "language": "es"}

        # Mock an error in the safety check
        with patch.object(safety_service, '_check_inappropriate_content') as mock_check:
            mock_check.side_effect = Exception("Test error")

            result = await safety_service.check_content_safety(
                content="test content",
                child_profile=child_profile,
                context={},
                language="es"
            )

            # Should default to safe on error
            assert result.is_safe
            assert len(result.violations) == 0
            assert result.confidence == 0.5
            assert "error" in result.metadata

    @patch('services.api.routers.conversation.get_db')
    @patch('services.api.routers.conversation.safety_service')
    def test_conversation_safety_error_handling(self, mock_safety, mock_get_db, client):
        """Test that conversation flow handles safety errors gracefully"""
        # Mock database
        mock_db = Mock()
        mock_db.conversations.find_one.return_value = {
            "conversation_id": "test_conv_123",
            "child_id": "test_child_123",
            "topic": "hobbies",
            "level": 3,
            "language": "es"
        }
        mock_db.messages.insert_one.return_value = Mock()
        mock_db.conversations.update_one.return_value = Mock()
        mock_get_db.return_value = mock_db

        # Mock safety service to raise an exception
        mock_safety.check_content_safety.side_effect = Exception("Safety check failed")
        mock_safety.get_service_status.return_value = {"status": "error"}

        conversation_next = {
            "conversation_id": "test_conv_123",
            "user_sentence": "hola",
            "end": False
        }

        # Should still return a response (fallback behavior)
        response = client.post("/conv/next", json=conversation_next)

        assert response.status_code == 200
        data = response.json()
        assert "reply" in data


class TestSafetyLoggingAndMonitoring:
    """Test safety logging and monitoring capabilities"""

    @pytest.mark.asyncio
    async def test_safety_violation_logging(self, safety_service, sample_child_profile):
        """Test that safety violations are properly logged"""
        content_with_violations = "quiero matar al monstruo feo y estúpido, mi email es test@ejemplo.com"
        context = {"topic": "juegos", "level": 3}

        await safety_service.check_content_safety(
            content=content_with_violations,
            child_profile=sample_child_profile,
            context=context,
            language="es"
        )

        # Check that violations were logged
        assert len(safety_service.safety_log) > 0

        latest_log = safety_service.safety_log[-1]
        assert latest_log["is_safe"] is False
        assert latest_log["violation_count"] > 0
        assert latest_log["child_id"] == sample_child_profile["child_id"]
        assert latest_log["max_severity"] in ["medium", "high", "critical"]

    @pytest.mark.asyncio
    async def test_critical_violation_immediate_logging(self, safety_service, sample_child_profile):
        """Test that critical violations trigger immediate logging"""
        content_with_critical_violation = "mi email es niño@ejemplo.com y mi teléfono es 1234567890"
        context = {"topic": "juegos", "level": 3}

        # Mock logger to capture critical violations
        with patch('services.api.services.safety_service.logger') as mock_logger:
            await safety_service.check_content_safety(
                content=content_with_critical_violation,
                child_profile=sample_child_profile,
                context=context,
                language="es"
            )

            # Should have logged a warning for critical violation
            mock_logger.warning.assert_called()
            call_args = mock_logger.warning.call_args[0][0]
            assert "CRITICAL SAFETY VIOLATION" in call_args

    @pytest.mark.asyncio
    async def test_safety_statistics_tracking(self, safety_service, sample_child_profile):
        """Test that safety statistics are tracked correctly"""
        # Perform multiple safety checks
        safe_contents = [
            "me gusta jugar en el parque",
            "los dibujos son divertidos",
            "la escuela está bien"
        ]

        unsafe_contents = [
            "quiero golpear al monstruo",
            "estúpido y feo",
            "mi email es test@ejemplo.com"
        ]

        for content in safe_contents:
            await safety_service.check_content_safety(
                content=content,
                child_profile=sample_child_profile,
                context={},
                language="es"
            )

        for content in unsafe_contents:
            await safety_service.check_content_safety(
                content=content,
                child_profile=sample_child_profile,
                context={},
                language="es"
            )

        stats = await safety_service.get_safety_statistics()

        assert stats["total_safety_checks"] == 6
        assert stats["safe_checks"] == 3
        assert stats["unsafe_checks"] == 3
        assert stats["safety_rate"] == 0.5
        assert len(stats["violation_counts"]) > 0
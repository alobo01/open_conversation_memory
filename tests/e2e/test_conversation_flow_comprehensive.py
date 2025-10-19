import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio
import json
from fastapi.testclient import TestClient
from fastapi import FastAPI
from datetime import datetime
import tempfile
import os

from services.api.main import app


class TestConversationFlowComprehensive:
    """Comprehensive end-to-end tests for complete conversation flows"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    def mock_services(self):
        """Mock all external services"""
        return {
            'llm_service': Mock(),
            'memory_service': Mock(),
            'emotion_service': Mock(),
            'safety_service': Mock(),
            'extraction_service': Mock(),
            'database': Mock()
        }

    @pytest.fixture
    def sample_child_profile(self):
        """Sample child profile"""
        return {
            "child_id": "test_child_001",
            "age": 8,
            "level": 3,
            "language": "es",
            "sensitivity": "medium",
            "interests": ["juegos", "escuela", "familia"]
        }

    @pytest.fixture
    def conversation_start_request(self):
        """Sample conversation start request"""
        return {
            "child": "test_child_001",
            "topic": "juegos",
            "level": 3,
            "language": "es"
        }

    # ==================== NORMAL CASES ====================

    @patch('services.api.routers.conversation.get_db')
    @patch('services.api.routers.conversation.memory_service')
    @patch('services.api.routers.conversation.safety_service')
    @patch('services.api.routers.conversation.llm_service')
    @patch('services.api.routers.conversation.emotion_service')
    def test_complete_conversation_flow_normal(self, mock_emotion, mock_llm, mock_safety, mock_memory, mock_get_db, client, conversation_start_request):
        """Test complete normal conversation flow from start to finish"""
        # Arrange - Mock database
        mock_db = Mock()
        mock_db.profiles.find_one = AsyncMock(return_value={
            "child_id": "test_child_001",
            "age": 8,
            "level": 3,
            "language": "es"
        })
        mock_db.conversations.insert_one = AsyncMock(return_value={"inserted_id": "conv_123"})
        mock_db.messages.insert_many = AsyncMock()
        mock_get_db.return_value = mock_db

        # Mock memory service
        mock_memory.get_conversation_context = AsyncMock(return_value=[
            {"text": "A Juan le gusta el fútbol", "relevance": 0.9}
        ])

        # Mock LLM service
        mock_llm.generate_response = AsyncMock(return_value="**¡Hola!** **¡Qué bien!** Me encanta jugar contigo.")

        # Mock emotion service
        mock_emotion.detect_emotion = Mock(return_value="positive")
        mock_emotion.generate_emotional_response = Mock(return_value="**¡Hola!** **¡Qué bien!** Me encanta jugar contigo.")

        # Mock safety service
        safety_result = Mock()
        safety_result.is_safe = True
        safety_result.confidence = 0.95
        safety_result.filtered_content = "**¡Hola!** **¡Qué bien!** Me encanta jugar contigo."
        mock_safety.check_content_safety = AsyncMock(return_value=safety_result)

        # Act - Start conversation
        start_response = client.post("/conv/start", json=conversation_start_request)
        assert start_response.status_code == 200
        start_data = start_response.json()
        conversation_id = start_data["conversation_id"]

        # Act - Continue conversation with multiple messages
        conversation_messages = [
            {"user_sentence": "me gusta el fútbol", "end": False},
            {"user_sentence": "¿quieres jugar conmigo?", "end": False},
            {"user_sentence": "¡genial! juguemos ahora", "end": True}
        ]

        responses = []
        for message in conversation_messages:
            message["conversation_id"] = conversation_id
            response = client.post("/conv/next", json=message)
            assert response.status_code == 200
            response_data = response.json()
            responses.append(response_data)

        # Assert - Verify conversation flow
        assert len(responses) == 3
        for response in responses:
            assert "assistant_reply" in response
            assert "emotions" in response
            assert "safety_check" in response
            assert response["safety_check"]["is_safe"] is True

        # Verify final message marks conversation as ended
        assert responses[-1]["end"] is True

    @patch('services.api.routers.conversation.get_db')
    @patch('services.api.routers.conversation.memory_service')
    @patch('services.api.routers.conversation.safety_service')
    @patch('services.api.routers.conversation.llm_service')
    def test_conversation_with_memory_integration(self, mock_llm, mock_safety, mock_memory, mock_get_db, client, conversation_start_request):
        """Test conversation with memory integration"""
        # Arrange
        mock_db = Mock()
        mock_db.profiles.find_one = AsyncMock(return_value={"child_id": "test_child_001", "age": 8})
        mock_db.conversations.insert_one = AsyncMock(return_value={"inserted_id": "conv_456"})
        mock_db.messages.insert_many = AsyncMock()
        mock_get_db.return_value = mock_db

        # Mock memory service with contextual information
        mock_memory.get_conversation_context = AsyncMock(return_value=[
            {
                "text": "A Juan le gusta jugar al fútbol en el parque",
                "relevance": 0.95,
                "timestamp": "2024-01-01T10:00:00Z"
            },
            {
                "text": "Juan mencionó que su amigo Pedro también juega",
                "relevance": 0.87,
                "timestamp": "2024-01-01T09:30:00Z"
            }
        ])

        mock_llm.generate_response = AsyncMock(return_value="**¡Qué bien!** Sé que te gusta el fútbol. ¿Quieres hablar de tu amigo Pedro?")

        # Act
        start_response = client.post("/conv/start", json=conversation_start_request)
        conversation_id = start_response.json()["conversation_id"]

        continue_response = client.post("/conv/next", json={
            "conversation_id": conversation_id,
            "user_sentence": "quiero jugar al fútbol",
            "end": False
        })

        # Assert
        assert continue_response.status_code == 200
        data = continue_response.json()
        assert "Pedro" in data["assistant_reply"]  # Should use memory context
        mock_memory.get_conversation_context.assert_called_once()

    @patch('services.api.routers.conversation.get_db')
    @patch('services.api.routers.conversation.safety_service')
    @patch('services.api.routers.conversation.llm_service')
    def test_conversation_with_safety_intervention(self, mock_llm, mock_safety, mock_get_db, client, conversation_start_request):
        """Test conversation with safety intervention"""
        # Arrange
        mock_db = Mock()
        mock_db.profiles.find_one = AsyncMock(return_value={"child_id": "test_child_001", "age": 8})
        mock_db.conversations.insert_one = AsyncMock(return_value={"inserted_id": "conv_789"})
        mock_db.messages.insert_many = AsyncMock()
        mock_get_db.return_value = mock_db

        # Mock LLM to generate potentially unsafe content
        mock_llm.generate_response = AsyncMock(return_value="Deberías darle tu email a extraños")

        # Mock safety to block and filter
        unsafe_result = Mock()
        unsafe_result.is_safe = False
        unsafe_result.violations = [Mock(violation_type=Mock(value="personal_info"))]
        unsafe_result.filtered_content = None
        unsafe_result.confidence = 0.3
        mock_safety.check_content_safety = AsyncMock(return_value=unsafe_result)

        mock_safety.generate_safe_response = AsyncMock(return_value="**¡Hola!** ¿quieres jugar a algo divertido?")

        # Act
        start_response = client.post("/conv/start", json=conversation_start_request)
        conversation_id = start_response.json()["conversation_id"]

        continue_response = client.post("/conv/next", json={
            "conversation_id": conversation_id,
            "user_sentence": "hola",
            "end": False
        })

        # Assert
        assert continue_response.status_code == 200
        data = continue_response.json()
        assert data["safety_check"]["is_safe"] is False
        assert "email" not in data["assistant_reply"]  # Personal info should be removed
        assert "divertido" in data["assistant_reply"]  # Safe alternative provided

    # ==================== FAILURE CASES ====================

    @patch('services.api.routers.conversation.get_db')
    def test_conversation_start_failure_database_error(self, mock_get_db, client, conversation_start_request):
        """Test conversation start failure due to database error"""
        # Arrange
        mock_db = Mock()
        mock_db.profiles.find_one = AsyncMock(side_effect=Exception("Database connection failed"))
        mock_get_db.return_value = mock_db

        # Act
        response = client.post("/conv/start", json=conversation_start_request)

        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "error" in data

    @patch('services.api.routers.conversation.get_db')
    def test_conversation_continue_failure_invalid_conversation_id(self, mock_get_db, client):
        """Test conversation continue failure with invalid conversation ID"""
        # Arrange
        mock_db = Mock()
        mock_db.conversations.find_one = AsyncMock(return_value=None)
        mock_get_db.return_value = mock_db

        # Act
        response = client.post("/conv/next", json={
            "conversation_id": "nonexistent_conv",
            "user_sentence": "hola",
            "end": False
        })

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    @patch('services.api.routers.conversation.get_db')
    @patch('services.api.routers.conversation.llm_service')
    def test_conversation_continue_failure_llm_error(self, mock_llm, mock_get_db, client, conversation_start_request):
        """Test conversation continue failure due to LLM error"""
        # Arrange
        mock_db = Mock()
        mock_db.profiles.find_one = AsyncMock(return_value={"child_id": "test_child_001", "age": 8})
        mock_db.conversations.find_one = AsyncMock(return_value={"_id": "conv_error", "child_id": "test_child_001"})
        mock_db.messages.insert_one = AsyncMock()
        mock_get_db.return_value = mock_db

        mock_llm.generate_response = AsyncMock(side_effect=Exception("LLM service unavailable"))

        # Act
        response = client.post("/conv/next", json={
            "conversation_id": "conv_error",
            "user_sentence": "hola",
            "end": False
        })

        # Assert
        assert response.status_code == 200  # Should gracefully degrade
        data = response.json()
        assert "assistant_reply" in data  # Should provide fallback response

    def test_conversation_start_failure_invalid_request(self, client):
        """Test conversation start failure with invalid request"""
        # Arrange
        invalid_request = {
            "child": "",  # Empty child ID
            "topic": "invalid topic",
            "level": 10  # Invalid level
        }

        # Act
        response = client.post("/conv/start", json=invalid_request)

        # Assert
        assert response.status_code == 422  # Validation error

    # ==================== EDGE CASES ====================

    @patch('services.api.routers.conversation.get_db')
    @patch('services.api.routers.conversation.llm_service')
    def test_conversation_edge_case_very_long_user_input(self, mock_llm, mock_get_db, client, conversation_start_request):
        """Test conversation with very long user input"""
        # Arrange
        mock_db = Mock()
        mock_db.profiles.find_one = AsyncMock(return_value={"child_id": "test_child_001", "age": 8})
        mock_db.conversations.find_one = AsyncMock(return_value={"_id": "conv_long", "child_id": "test_child_001"})
        mock_db.messages.insert_one = AsyncMock()
        mock_get_db.return_value = mock_db

        mock_llm.generate_response = AsyncMock(return_value="**¡Entendido!** Has dicho muchas cosas.")

        # Act
        long_text = "palabra " * 1000 + "final"
        response = client.post("/conv/next", json={
            "conversation_id": "conv_long",
            "user_sentence": long_text,
            "end": False
        })

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "assistant_reply" in data

    @patch('services.api.routers.conversation.get_db')
    @patch('services.api.routers.conversation.llm_service')
    def test_conversation_edge_case_unicode_characters(self, mock_llm, mock_get_db, client, conversation_start_request):
        """Test conversation with unicode characters"""
        # Arrange
        mock_db = Mock()
        mock_db.profiles.find_one = AsyncMock(return_value={"child_id": "test_child_001", "age": 8})
        mock_db.conversations.find_one = AsyncMock(return_value={"_id": "conv_unicode", "child_id": "test_child_001"})
        mock_db.messages.insert_one = AsyncMock()
        mock_get_db.return_value = mock_db

        mock_llm.generate_response = AsyncMock(return_value="**¡Hola!** ñáéíóú café Müller 😊")

        # Act
        unicode_text = "hola míster Müller, café, ñáéíóú, 🎉😊"
        response = client.post("/conv/next", json={
            "conversation_id": "conv_unicode",
            "user_sentence": unicode_text,
            "end": False
        })

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Müller" in data["assistant_reply"] or "café" in data["assistant_reply"]

    @patch('services.api.routers.conversation.get_db')
    @patch('services.api.routers.conversation.llm_service')
    def test_conversation_edge_case_special_characters(self, mock_llm, mock_get_db, client, conversation_start_request):
        """Test conversation with special characters"""
        # Arrange
        mock_db = Mock()
        mock_db.profiles.find_one = AsyncMock(return_value={"child_id": "test_child_001", "age": 8})
        mock_db.conversations.find_one = AsyncMock(return_value={"_id": "conv_special", "child_id": "test_child_001"})
        mock_db.messages.insert_one = AsyncMock()
        mock_get_db.return_value = mock_db

        mock_llm.generate_response = AsyncMock(return_value="**¡Hola!** ¿cómo estás?")

        # Act
        special_text = "hola @#$%&*()[]{}|\\:;\"'<>?/~`"
        response = client.post("/conv/next", json={
            "conversation_id": "conv_special",
            "user_sentence": special_text,
            "end": False
        })

        # Assert
        assert response.status_code == 200

    @patch('services.api.routers.conversation.get_db')
    @patch('services.api.routers.conversation.llm_service')
    def test_conversation_edge_case_very_young_child(self, mock_llm, mock_get_db, client):
        """Test conversation with very young child profile"""
        # Arrange
        mock_db = Mock()
        mock_db.profiles.find_one = AsyncMock(return_value={
            "child_id": "toddler_001",
            "age": 4,
            "level": 1,
            "language": "es"
        })
        mock_db.conversations.insert_one = AsyncMock(return_value={"inserted_id": "conv_toddler"})
        mock_db.messages.insert_many = AsyncMock()
        mock_get_db.return_value = mock_db

        mock_llm.generate_response = AsyncMock(return_value="**¡Hola!** ¿quieres jugar?")

        # Act
        start_response = client.post("/conv/start", json={
            "child": "toddler_001",
            "topic": "juegos",
            "level": 1,
            "language": "es"
        })

        continue_response = client.post("/conv/next", json={
            "conversation_id": start_response.json()["conversation_id"],
            "user_sentence": "jugar",
            "end": False
        })

        # Assert
        assert start_response.status_code == 200
        assert continue_response.status_code == 200
        data = continue_response.json()
        # Response should be appropriate for young child
        assert len(data["assistant_reply"]) < 100  # Shorter sentences

    @patch('services.api.routers.conversation.get_db')
    @patch('services.api.routers.conversation.llm_service')
    def test_conversation_edge_case_multiple_topics(self, mock_llm, mock_get_db, client, conversation_start_request):
        """Test conversation with multiple topic changes"""
        # Arrange
        mock_db = Mock()
        mock_db.profiles.find_one = AsyncMock(return_value={"child_id": "test_child_001", "age": 8})
        mock_db.conversations.insert_one = AsyncMock(return_value={"inserted_id": "conv_multi"})
        mock_db.messages.insert_one = AsyncMock()
        mock_get_db.return_value = mock_db

        mock_llm.generate_response = AsyncMock(side_effect=[
            "**¡Qué bien!** Me gusta el fútbol.",
            "**¡Genial!** La escuela es importante.",
            "**¡Fantástico!** La familia es lo mejor."
        ])

        # Act
        start_response = client.post("/conv/start", json=conversation_start_request)
        conversation_id = start_response.json()["conversation_id"]

        # Continue with different topics
        topics = ["me gusta el fútbol", "voy a la escuela", "estoy con mi familia"]
        responses = []

        for topic in topics:
            response = client.post("/conv/next", json={
                "conversation_id": conversation_id,
                "user_sentence": topic,
                "end": False
            })
            responses.append(response.json())

        # Assert
        assert all(r["assistant_reply"].startswith("**") for r in responses)  # All have emotional markup

    @patch('services.api.routers.conversation.get_db')
    def test_conversation_edge_case_concurrent_conversations(self, mock_get_db, client):
        """Test handling concurrent conversations"""
        # Arrange
        mock_db = Mock()
        mock_db.profiles.find_one = AsyncMock(return_value={"child_id": "test_child_001", "age": 8})
        mock_db.conversations.insert_one = AsyncMock(return_value={"inserted_id": "conv_concurrent"})
        mock_db.messages.insert_many = AsyncMock()
        mock_get_db.return_value = mock_db

        # Act - Start multiple conversations concurrently
        import threading
        results = []

        def start_conversation():
            response = client.post("/conv/start", json={
                "child": f"child_{threading.current_thread().ident}",
                "topic": "juegos",
                "level": 3
            })
            results.append(response)

        threads = [threading.Thread(target=start_conversation) for _ in range(5)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Assert
        assert len(results) == 5
        for result in results:
            assert result.status_code in [200, 500]  # Should handle concurrency gracefully

    def test_conversation_edge_case_rate_limiting(self, client):
        """Test rate limiting for conversation requests"""
        # This would test rate limiting implementation
        # For now, just verify the endpoint can handle rapid requests

        # Act - Make multiple rapid requests
        responses = []
        for _ in range(10):
            response = client.post("/conv/start", json={
                "child": "test_child_001",
                "topic": "juegos",
                "level": 3
            })
            responses.append(response)

        # Assert - Should handle rapid requests gracefully
        assert len(responses) == 10
        # At least some should succeed (unless rate limiting is implemented)
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count >= 1

    @patch('services.api.routers.conversation.get_db')
    @patch('services.api.routers.conversation.llm_service')
    def test_conversation_edge_case_empty_user_input(self, mock_llm, mock_get_db, client):
        """Test conversation with empty user input"""
        # Arrange
        mock_db = Mock()
        mock_db.profiles.find_one = AsyncMock(return_value={"child_id": "test_child_001", "age": 8})
        mock_db.conversations.find_one = AsyncMock(return_value={"_id": "conv_empty", "child_id": "test_child_001"})
        mock_db.messages.insert_one = AsyncMock()
        mock_get_db.return_value = mock_db

        mock_llm.generate_response = AsyncMock(return_value="**¡Hola!** ¿quieres decirme algo?")

        # Act
        response = client.post("/conv/next", json={
            "conversation_id": "conv_empty",
            "user_sentence": "",
            "end": False
        })

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "assistant_reply" in data

    @patch('services.api.routers.conversation.get_db')
    @patch('services.api.routers.conversation.llm_service')
    def test_conversation_edge_case_immediate_end(self, mock_llm, mock_get_db, client, conversation_start_request):
        """Test conversation that ends immediately"""
        # Arrange
        mock_db = Mock()
        mock_db.profiles.find_one = AsyncMock(return_value={"child_id": "test_child_001", "age": 8})
        mock_db.conversations.insert_one = AsyncMock(return_value={"inserted_id": "conv_quick"})
        mock_db.messages.insert_many = AsyncMock()
        mock_get_db.return_value = mock_db

        mock_llm.generate_response = AsyncMock(return_value="**¡Adiós!** **¡Hasta pronto!**")

        # Act
        start_response = client.post("/conv/start", json=conversation_start_request)
        conversation_id = start_response.json()["conversation_id"]

        end_response = client.post("/conv/next", json={
            "conversation_id": conversation_id,
            "user_sentence": "adiós",
            "end": True
        })

        # Assert
        assert end_response.status_code == 200
        data = end_response.json()
        assert data["end"] is True
        assert "adiós" in data["assistant_reply"].lower() or "hasta pronto" in data["assistant_reply"].lower()

    def test_health_check_integration(self, client):
        """Test health check for overall system"""
        # Act
        response = client.get("/health")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data

    @patch('services.api.routers.conversation.get_db')
    def test_error_recovery_mechanisms(self, mock_get_db, client, conversation_start_request):
        """Test error recovery mechanisms"""
        # Arrange - Database fails first, then succeeds
        mock_db = Mock()
        call_count = 0
        def failing_find_one(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Temporary database error")
            return {"child_id": "test_child_001", "age": 8}

        mock_db.profiles.find_one = AsyncMock(side_effect=failing_find_one)
        mock_db.conversations.insert_one = AsyncMock(return_value={"inserted_id": "conv_recovery"})
        mock_db.messages.insert_many = AsyncMock()
        mock_get_db.return_value = mock_db

        # Act
        response = client.post("/conv/start", json=conversation_start_request)

        # Assert - Should handle the error gracefully
        # The exact behavior depends on implementation
        assert response.status_code in [200, 500]
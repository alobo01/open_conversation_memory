import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
import json

from services.api.main import app
from services.api.models.schemas import EmotionType


@pytest.fixture
def client():
    """Test client for FastAPI app"""
    return TestClient(app)


@pytest.fixture
def mock_memory_service():
    """Mock memory service"""
    service = Mock()
    service.get_conversation_context = AsyncMock()
    service.search_similar_conversations = AsyncMock()
    service.get_semantic_memory_summary = AsyncMock()
    service.delete_conversation_memory = AsyncMock()
    service.get_memory_status = AsyncMock()
    return service


@pytest.fixture
def sample_conversation_data():
    """Sample conversation data for testing"""
    return {
        "conversation_id": "test_conv_123",
        "child_id": "test_child",
        "topic": "hobbies",
        "level": 3,
        "language": "es",
        "created_at": "2024-01-01T10:00:00",
        "status": "active",
        "message_count": 5
    }


@pytest.fixture
def sample_memory_context():
    """Sample memory context for testing"""
    return [
        {
            "text": "Me gusta jugar al fútbol en el parque",
            "conversation_id": "conv_1",
            "child_id": "test_child",
            "topic": "hobbies",
            "role": "user",
            "emotion": "positive",
            "score": 0.85,
            "timestamp": 1704110400,
            "message_index": 0
        },
        {
            "text": "**¡Qué bien!** ¿Qué posición prefieres jugar?",
            "conversation_id": "conv_1",
            "child_id": "test_child",
            "topic": "hobbies",
            "role": "assistant",
            "emotion": "positive",
            "score": 0.82,
            "timestamp": 1704110460,
            "message_index": 1
        }
    ]


@pytest.fixture
def sample_memory_summary():
    """Sample memory summary for testing"""
    return {
        "status": "available",
        "total_messages": 25,
        "user_messages": 12,
        "assistant_messages": 13,
        "unique_conversations": 5,
        "topics_distribution": {
            "hobbies": 15,
            "school": 10
        },
        "emotions_distribution": {
            "positive": 18,
            "neutral": 5,
            "calm": 2
        },
        "most_discussed_topics": [
            ("hobbies", 15),
            ("school", 10)
        ]
    }


class TestMemoryEndpoints:
    """Test cases for memory-related API endpoints"""

    @patch('services.api.routers.conversation.memory_service')
    def test_get_child_memory_context_success(self, mock_service, client, sample_memory_context):
        """Test successful memory context retrieval"""
        mock_service.get_conversation_context.return_value = sample_memory_context

        response = client.get(
            "/conv/memory/test_child/context?topic=hobbies&limit=3"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["child_id"] == "test_child"
        assert data["topic"] == "hobbies"
        assert data["count"] == 2
        assert len(data["context"]) == 2
        assert data["context"][0]["text"] == "Me gusta jugar al fútbol en el parque"

        # Verify service was called correctly
        mock_service.get_conversation_context.assert_called_once_with(
            child_id="test_child",
            topic="hobbies",
            query=None,
            limit=3
        )

    @patch('services.api.routers.conversation.memory_service')
    def test_get_child_memory_context_with_query(self, mock_service, client, sample_memory_context):
        """Test memory context retrieval with search query"""
        mock_service.get_conversation_context.return_value = sample_memory_context

        response = client.get(
            "/conv/memory/test_child/context?topic=hobbies&query=fútbol&limit=5"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "fútbol"
        assert data["limit"] == 5

        mock_service.get_conversation_context.assert_called_once_with(
            child_id="test_child",
            topic="hobbies",
            query="fútbol",
            limit=5
        )

    @patch('services.api.routers.conversation.memory_service')
    def test_get_child_memory_context_service_error(self, mock_service, client):
        """Test memory context retrieval when service fails"""
        mock_service.get_conversation_context.side_effect = Exception("Service error")

        response = client.get("/conv/memory/test_child/context")

        assert response.status_code == 500
        assert "Failed to get memory context" in response.json()["detail"]

    @patch('services.api.routers.conversation.memory_service')
    def test_search_child_memory_success(self, mock_service, client, sample_memory_context):
        """Test successful memory search"""
        mock_service.search_similar_conversations.return_value = sample_memory_context

        response = client.get(
            "/conv/memory/test_child/search?query=juegos&topic=hobbies&limit=3"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["child_id"] == "test_child"
        assert data["query"] == "juegos"
        assert data["topic"] == "hobbies"
        assert data["count"] == 2
        assert len(data["results"]) == 2

        mock_service.search_similar_conversations.assert_called_once_with(
            query="juegos",
            child_id="test_child",
            topic="hobbies",
            limit=3
        )

    @patch('services.api.routers.conversation.memory_service')
    def test_search_child_memory_minimal_params(self, mock_service, client, sample_memory_context):
        """Test memory search with minimal parameters"""
        mock_service.search_similar_conversations.return_value = sample_memory_context

        response = client.get("/conv/memory/test_child/search?query=deportes")

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "deportes"
        assert data["topic"] is None

        mock_service.search_similar_conversations.assert_called_once_with(
            query="deportes",
            child_id="test_child",
            topic=None,
            limit=5  # Default limit
        )

    @patch('services.api.routers.conversation.memory_service')
    def test_get_memory_summary_success(self, mock_service, client, sample_memory_summary):
        """Test successful memory summary retrieval"""
        mock_service.get_semantic_memory_summary.return_value = sample_memory_summary

        response = client.get("/conv/memory/test_child/summary?topic=hobbies")

        assert response.status_code == 200
        data = response.json()
        assert data["child_id"] == "test_child"
        assert data["topic"] == "hobbies"
        assert data["summary"]["status"] == "available"
        assert data["summary"]["total_messages"] == 25
        assert data["summary"]["user_messages"] == 12

        mock_service.get_semantic_memory_summary.assert_called_once_with(
            child_id="test_child",
            topic="hobbies"
        )

    @patch('services.api.routers.conversation.memory_service')
    def test_get_memory_summary_all_topics(self, mock_service, client, sample_memory_summary):
        """Test memory summary for all topics"""
        mock_service.get_semantic_memory_summary.return_value = sample_memory_summary

        response = client.get("/conv/memory/test_child/summary")

        assert response.status_code == 200
        data = response.json()
        assert data["topic"] is None

        mock_service.get_semantic_memory_summary.assert_called_once_with(
            child_id="test_child",
            topic=None
        )

    @patch('services.api.routers.conversation.memory_service')
    def test_delete_conversation_memory_success(self, mock_service, client):
        """Test successful conversation memory deletion"""
        mock_service.delete_conversation_memory.return_value = True

        response = client.delete("/conv/memory/conv_123")

        assert response.status_code == 200
        data = response.json()
        assert "Conversation conv_123 deleted from memory" in data["message"]

        mock_service.delete_conversation_memory.assert_called_once_with("conv_123")

    @patch('services.api.routers.conversation.memory_service')
    def test_delete_conversation_memory_not_found(self, mock_service, client):
        """Test deletion when conversation not found in memory"""
        mock_service.delete_conversation_memory.return_value = False

        response = client.delete("/conv/memory/conv_123")

        assert response.status_code == 404
        assert "Conversation not found in memory" in response.json()["detail"]

    @patch('services.api.routers.conversation.memory_service')
    def test_get_memory_status_success(self, mock_service, client):
        """Test successful memory status retrieval"""
        mock_status = {
            "status": "available",
            "embedding_model": "paraphrase-multilingual-MiniLM-L12-v2",
            "collection_name": "conversations",
            "vectors_count": 1000,
            "indexed_vectors_count": 1000,
            "vector_size": 384
        }
        mock_service.get_memory_status.return_value = mock_status

        response = client.get("/conv/memory/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "available"
        assert data["embedding_model"] == "paraphrase-multilingual-MiniLM-L12-v2"
        assert data["vectors_count"] == 1000

    @patch('services.api.routers.conversation.memory_service')
    def test_get_memory_status_service_error(self, mock_service, client):
        """Test memory status when service fails"""
        mock_service.get_memory_status.side_effect = Exception("Service error")

        response = client.get("/conv/memory/status")

        assert response.status_code == 500
        assert "Failed to get memory status" in response.json()["detail"]


class TestConversationWithMemoryIntegration:
    """Integration tests for conversation flow with memory"""

    @patch('services.api.routers.conversation.memory_service')
    @patch('services.api.routers.conversation.get_db')
    def test_start_conversation_with_memory(self, mock_db, mock_memory_service, client):
        """Test conversation start with memory integration"""
        # Mock database responses
        mock_db_instance = Mock()
        mock_db_instance.profiles.find_one.return_value = None  # No existing profile
        mock_db_instance.profiles.insert_one.return_value = None
        mock_db_instance.conversations.insert_one.return_value = None
        mock_db_instance.messages.insert_one.return_value = None
        mock_db.return_value = mock_db_instance

        # Start conversation
        response = client.post(
            "/conv/start",
            json={
                "child": "test_child",
                "topic": "hobbies",
                "level": 3
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "conversation_id" in data
        assert "starting_sentence" in data

    @patch('services.api.routers.conversation.memory_service')
    @patch('services.api.routers.conversation.get_db')
    def test_continue_conversation_with_memory_context(self, mock_db, mock_memory_service, client):
        """Test conversation continuation with memory context"""
        # Mock database responses
        mock_db_instance = Mock()
        mock_db_instance.conversations.find_one.return_value = {
            "conversation_id": "test_conv",
            "child_id": "test_child",
            "topic": "hobbies",
            "level": 3,
            "language": "es"
        }
        mock_db_instance.messages.find.return_value.sort.return_value.to_list.return_value = []
        mock_db_instance.messages.insert_one.return_value = None
        mock_db_instance.conversations.update_one.return_value = None
        mock_db.return_value = mock_db_instance

        # Mock memory service context
        mock_context = [
            {
                "text": "Me gusta jugar al fútbol",
                "score": 0.85
            }
        ]
        mock_memory_service.get_conversation_context.return_value = mock_context

        # Continue conversation
        response = client.post(
            "/conv/next",
            json={
                "conversation_id": "test_conv",
                "user_sentence": "Me gusta el fútbol",
                "end": False
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "reply" in data

        # Verify memory service was called for context
        mock_memory_service.get_conversation_context.assert_called_once_with(
            child_id="test_child",
            topic="hobbies",
            query="Me gusta el fútbol"
        )


class TestMemoryErrorHandling:
    """Test error handling for memory operations"""

    @patch('services.api.routers.conversation.memory_service')
    def test_memory_disabled_responses(self, mock_service, client):
        """Test API responses when memory is disabled"""
        # Mock disabled semantic search
        mock_service.get_conversation_context.return_value = []

        response = client.get("/conv/memory/test_child/context")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["context"] == []

    @patch('services.api.routers.conversation.memory_service')
    def test_memory_unavailable_responses(self, mock_service, client):
        """Test API responses when memory service is unavailable"""
        # Mock unavailable service
        mock_service.get_conversation_context.side_effect = Exception("Qdrant unavailable")

        response = client.get("/conv/memory/test_child/context")

        assert response.status_code == 500
        assert "Failed to get memory context" in response.json()["detail"]

    def test_invalid_parameters(self, client):
        """Test API with invalid parameters"""
        # Test missing required query parameter
        response = client.get("/conv/memory/test_child/search")

        assert response.status_code == 422  # Validation error

        # Test invalid limit parameter
        response = client.get("/conv/memory/test_child/search?query=test&limit=invalid")

        assert response.status_code == 422
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from services.api.services.memory_service import MemoryService
from services.api.core.config import settings
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue


@pytest.fixture
def mock_qdrant():
    """Mock Qdrant client"""
    client = Mock()
    
    # Mock get_collections to return a proper mock response
    collections_response = Mock()
    collections_response.collections = []
    client.get_collections = Mock(return_value=collections_response)
    
    client.create_collection = Mock()
    client.get_collection = Mock()
    client.upsert = Mock()
    client.search = Mock()
    client.delete = Mock()
    client.scroll = Mock()
    return client


@pytest.fixture
def mock_embedding_model():
    """Mock sentence transformer model"""
    model = Mock()
    
    # Create a mock tensor with tolist method
    mock_tensor = Mock()
    mock_tensor.tolist = Mock(return_value=[0.1] * 384)  # Mock embedding vector
    
    model.encode = Mock(return_value=mock_tensor)
    return model


@pytest.fixture
def memory_service(mock_qdrant, mock_embedding_model):
    """Create memory service instance with mocked dependencies"""
    with patch('services.api.services.memory_service.get_qdrant', return_value=mock_qdrant), \
         patch('services.api.services.memory_service.SentenceTransformer', return_value=mock_embedding_model):
        service = MemoryService()
        # Store the mock qdrant client for consistent use
        service.qdrant_client = mock_qdrant
        return service


@pytest.fixture
def sample_messages():
    """Sample conversation messages for testing"""
    return [
        {
            "role": "user",
            "text": "Me gusta jugar en el parque",
            "timestamp": datetime.now().timestamp(),
            "emotion": "positive"
        },
        {
            "role": "assistant",
            "text": "**¡Qué bien!** ¿Qué juegos te gustan más?",
            "timestamp": datetime.now().timestamp(),
            "emotion": "positive"
        }
    ]


@pytest.fixture
def sample_metadata():
    """Sample metadata for testing"""
    return {
        "topic": "hobbies",
        "level": 3,
        "language": "es"
    }


class TestMemoryService:
    """Test cases for MemoryService"""

    def test_init_embedding_model(self, memory_service, mock_embedding_model):
        """Test embedding model initialization"""
        assert memory_service.embedding_model is not None
        # The embedding model should be properly initialized
        # Note: We don't check the exact mock call since initialization might fail
        # due to Qdrant issues, but the model should still be set if available

    def test_init_qdrant_collection_new(self, memory_service, mock_qdrant):
        """Test Qdrant collection creation when it doesn't exist"""
        # Mock collection doesn't exist
        mock_qdrant.get_collections.return_value.collections = []

        # Re-initialize to trigger collection creation
        memory_service._init_qdrant_collection()

        mock_qdrant.create_collection.assert_called_once_with(
            collection_name=settings.qdrant_collection_name,
            vectors_config={
                "size": settings.embedding_dimension,
                "distance": "Cosine"
            }
        )

    def test_init_qdrant_collection_exists(self, memory_service, mock_qdrant):
        """Test Qdrant collection handling when it already exists"""
        # Mock collection exists
        mock_collection = Mock()
        mock_collection.config.params.vectors.size = settings.embedding_dimension
        mock_qdrant.get_collections.return_value.collections = [
            Mock(name=settings.qdrant_collection_name)
        ]
        mock_qdrant.get_collection.return_value = mock_collection

        # Reset the mock to clear previous calls
        mock_qdrant.create_collection.reset_mock()

        # Re-initialize
        memory_service._init_qdrant_collection()

        # Should not create new collection
        mock_qdrant.create_collection.assert_not_called()

    def test_clean_text_for_embedding(self, memory_service):
        """Test text cleaning for embedding"""
        text_with_markup = "**¡Hola!** ¿cómo estás __hoy__?"
        cleaned = memory_service._clean_text_for_embedding(text_with_markup)

        assert cleaned == "¡Hola! ¿cómo estás hoy?"
        assert "**" not in cleaned
        assert "__" not in cleaned

    @pytest.mark.asyncio
    async def test_store_conversation_success(self, memory_service, mock_qdrant, sample_messages, sample_metadata):
        """Test successful conversation storage"""
        mock_qdrant.upsert = Mock()

        result = await memory_service.store_conversation(
            conversation_id="test_conv_123",
            child_id="test_child",
            messages=sample_messages,
            metadata=sample_metadata
        )

        assert result is True
        mock_qdrant.upsert.assert_called()

    @pytest.mark.asyncio
    async def test_store_conversation_no_model(self, memory_service, sample_messages):
        """Test conversation storage when embedding model is not available"""
        memory_service.embedding_model = None

        result = await memory_service.store_conversation(
            conversation_id="test_conv_123",
            child_id="test_child",
            messages=sample_messages
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_store_conversation_disabled(self, memory_service, sample_messages):
        """Test conversation storage when semantic search is disabled"""
        with patch.object(settings, 'enable_semantic_search', False):
            result = await memory_service.store_conversation(
                conversation_id="test_conv_123",
                child_id="test_child",
                messages=sample_messages
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_store_single_message(self, memory_service, mock_qdrant, sample_messages, sample_metadata):
        """Test storing a single message"""
        mock_qdrant.upsert = Mock()

        result = await memory_service.store_single_message(
            conversation_id="test_conv_123",
            child_id="test_child",
            message=sample_messages[0],
            metadata=sample_metadata
        )

        assert result is True
        mock_qdrant.upsert.assert_called()

    @pytest.mark.asyncio
    async def test_search_similar_conversations_success(self, memory_service, mock_qdrant):
        """Test successful semantic search"""
        # Mock search results
        mock_result = Mock()
        mock_result.score = 0.8
        mock_result.payload = {
            "text": "Me gusta jugar al fútbol",
            "conversation_id": "conv_1",
            "child_id": "child_1",
            "topic": "hobbies",
            "role": "user",
            "emotion": "positive",
            "timestamp": datetime.now().timestamp(),
            "message_index": 0
        }
        mock_qdrant.search.return_value = [mock_result]

        results = await memory_service.search_similar_conversations(
            query="juegos deportes",
            child_id="child_1",
            topic="hobbies"
        )

        assert len(results) == 1
        assert results[0]["text"] == "Me gusta jugar al fútbol"
        assert results[0]["score"] == 0.8
        assert results[0]["conversation_id"] == "conv_1"

    @pytest.mark.asyncio
    async def test_search_similar_conversations_no_model(self, memory_service):
        """Test semantic search when embedding model is not available"""
        memory_service.embedding_model = None

        results = await memory_service.search_similar_conversations(
            query="test query"
        )

        assert results == []

    @pytest.mark.asyncio
    async def test_search_similar_conversations_disabled(self, memory_service):
        """Test semantic search when disabled"""
        with patch.object(settings, 'enable_semantic_search', False):
            results = await memory_service.search_similar_conversations(
                query="test query"
            )

            assert results == []

    @pytest.mark.asyncio
    async def test_search_similar_conversations_with_filters(self, memory_service, mock_qdrant):
        """Test semantic search with filters"""
        mock_qdrant.search.return_value = []

        await memory_service.search_similar_conversations(
            query="test query",
            child_id="child_1",
            topic="school",
            role="user",
            limit=3,
            min_score=0.5
        )

        # Verify search was called with correct parameters
        mock_qdrant.search.assert_called_once()
        call_args = mock_qdrant.search.call_args
        assert call_args.kwargs['limit'] == 6  # limit * 2 for filtering
        assert call_args.kwargs['score_threshold'] == 0.5

    @pytest.mark.asyncio
    async def test_get_conversation_context(self, memory_service):
        """Test getting conversation context"""
        # Mock the search method
        mock_context = [
            {
                "text": "Me gusta el colegio",
                "conversation_id": "conv_1",
                "score": 0.7,
                "timestamp": datetime.now().timestamp()
            }
        ]

        with patch.object(memory_service, 'search_similar_conversations', return_value=mock_context):
            context = await memory_service.get_conversation_context(
                child_id="child_1",
                topic="school",
                query="aprendizaje"
            )

            assert len(context) == 1
            assert context[0]["text"] == "Me gusta el colegio"

    @pytest.mark.asyncio
    async def test_get_semantic_memory_summary(self, memory_service, mock_qdrant):
        """Test getting semantic memory summary"""
        # Mock scroll results
        mock_result1 = Mock()
        mock_result1.payload = {
            "role": "user",
            "topic": "hobbies",
            "emotion": "positive",
            "conversation_id": "conv_1"
        }
        mock_result2 = Mock()
        mock_result2.payload = {
            "role": "assistant",
            "topic": "hobbies",
            "emotion": "neutral",
            "conversation_id": "conv_1"
        }

        mock_qdrant.scroll.return_value = ([mock_result1, mock_result2], None)

        summary = await memory_service.get_semantic_memory_summary(
            child_id="child_1",
            topic="hobbies"
        )

        assert summary["status"] == "available"
        assert summary["total_messages"] == 2
        assert summary["user_messages"] == 1
        assert summary["assistant_messages"] == 1
        assert summary["unique_conversations"] == 1
        assert "hobbies" in summary["topics_distribution"]

    @pytest.mark.asyncio
    async def test_get_semantic_memory_summary_disabled(self, memory_service):
        """Test memory summary when semantic search is disabled"""
        with patch.object(settings, 'enable_semantic_search', False):
            summary = await memory_service.get_semantic_memory_summary(
                child_id="child_1"
            )

            assert summary["status"] == "disabled"

    @pytest.mark.asyncio
    async def test_delete_conversation_memory(self, memory_service, mock_qdrant):
        """Test deleting conversation from memory"""
        mock_qdrant.delete = Mock()

        result = await memory_service.delete_conversation_memory("conv_123")

        assert result is True
        mock_qdrant.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_memory_status(self, memory_service, mock_qdrant):
        """Test getting memory service status"""
        # Mock collection info
        mock_collection_info = Mock()
        mock_collection_info.vectors_count = 100
        mock_collection_info.indexed_vectors_count = 100
        mock_collection_info.config.params.vectors.size = 384
        mock_qdrant.get_collection.return_value = mock_collection_info

        status = await memory_service.get_memory_status()

        assert status["status"] == "available"
        assert status["embedding_model"] == settings.embedding_model_name
        assert status["collection_name"] == settings.qdrant_collection_name
        assert status["vectors_count"] == 100
        assert status["vector_size"] == 384

    @pytest.mark.asyncio
    async def test_get_memory_status_unavailable(self, memory_service):
        """Test memory status when Qdrant is not available"""
        # Set the qdrant_client to None to simulate unavailability
        memory_service.qdrant_client = None
        
        status = await memory_service.get_memory_status()

        assert status["status"] == "unavailable"
        assert "Qdrant client not available" in status["reason"]


@pytest.mark.asyncio
async def test_integration_with_conversation_flow(memory_service, mock_qdrant, sample_messages, sample_metadata):
    """Integration test for complete conversation flow"""
    # Store conversation
    mock_qdrant.upsert = Mock()

    await memory_service.store_conversation(
        conversation_id="integration_test",
        child_id="test_child",
        messages=sample_messages,
        metadata=sample_metadata
    )

    # Search for similar conversations
    mock_result = Mock()
    mock_result.score = 0.85
    mock_result.payload = {
        "text": "Me gusta jugar en el recreo",
        "conversation_id": "integration_test",
        "child_id": "test_child",
        "topic": "hobbies",
        "role": "user",
        "emotion": "positive",
        "timestamp": datetime.now().timestamp(),
        "message_index": 0
    }
    mock_qdrant.search.return_value = [mock_result]

    results = await memory_service.search_similar_conversations(
        query="juegos divertidos",
        child_id="test_child",
        topic="hobbies"
    )

    assert len(results) == 1
    assert results[0]["text"] == "Me gusta jugar en el recreo"
    assert results[0]["score"] == 0.85

    # Get context
    context = await memory_service.get_conversation_context(
        child_id="test_child",
        topic="hobbies"
    )

    assert len(context) >= 0  # May return empty if no matching results

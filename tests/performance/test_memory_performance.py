import pytest
import asyncio
import time
import statistics
from unittest.mock import Mock, AsyncMock, patch
from typing import List

from services.api.services.memory_service import MemoryService
from services.api.core.config import settings


@pytest.fixture
def mock_qdrant():
    """Mock Qdrant client with timing capabilities"""
    client = Mock()
    client.get_collections = Mock(return_value=Mock(collections=[]))
    client.create_collection = Mock()
    client.get_collection = Mock()
    client.upsert = AsyncMock()
    client.search = AsyncMock()
    client.delete = AsyncMock()
    client.scroll = AsyncMock()
    return client


@pytest.fixture
def mock_embedding_model():
    """Mock sentence transformer model with realistic timing"""
    model = Mock()
    # Simulate embedding computation time
    async def mock_encode(text, **kwargs):
        await asyncio.sleep(0.01)  # 10ms for encoding
        return [0.1] * settings.embedding_dimension

    model.encode = Mock(side_effect=mock_encode)
    return model


@pytest.fixture
def memory_service(mock_qdrant, mock_embedding_model):
    """Create memory service instance with mocked dependencies"""
    with patch('services.api.services.memory_service.get_qdrant', return_value=mock_qdrant), \
         patch('services.api.services.memory_service.SentenceTransformer', return_value=mock_embedding_model):
        service = MemoryService()
        return service


def generate_test_messages(count: int) -> List[dict]:
    """Generate test messages for performance testing"""
    messages = []
    for i in range(count):
        messages.append({
            "role": "user" if i % 2 == 0 else "assistant",
            "text": f"Este es un mensaje de prueba número {i} con contenido variado para probar embeddings.",
            "timestamp": time.time() + i,
            "emotion": "positive" if i % 3 == 0 else "neutral"
        })
    return messages


class TestMemoryPerformance:
    """Performance tests for memory operations"""

    @pytest.mark.asyncio
    async def test_embedding_performance_single_message(self, memory_service):
        """Test embedding performance for a single message"""
        messages = [{"role": "user", "text": "Mensaje de prueba", "timestamp": time.time()}]

        start_time = time.time()
        await memory_service.store_conversation(
            conversation_id="perf_test_1",
            child_id="test_child",
            messages=messages
        )
        end_time = time.time()

        processing_time = end_time - start_time

        # Should complete within 100ms for single message
        assert processing_time < 0.1, f"Single message took {processing_time:.3f}s, expected <0.1s"
        print(f"Single message processing time: {processing_time:.3f}s")

    @pytest.mark.asyncio
    async def test_embedding_performance_batch_messages(self, memory_service):
        """Test embedding performance for batch messages"""
        message_counts = [10, 50, 100]
        results = {}

        for count in message_counts:
            messages = generate_test_messages(count)

            start_time = time.time()
            await memory_service.store_conversation(
                conversation_id=f"perf_test_batch_{count}",
                child_id="test_child",
                messages=messages
            )
            end_time = time.time()

            processing_time = end_time - start_time
            messages_per_second = count / processing_time
            results[count] = {
                "time": processing_time,
                "messages_per_second": messages_per_second
            }

            # Performance targets
            if count <= 10:
                assert processing_time < 0.5, f"{count} messages took {processing_time:.3f}s, expected <0.5s"
            elif count <= 50:
                assert processing_time < 2.0, f"{count} messages took {processing_time:.3f}s, expected <2.0s"
            else:
                assert processing_time < 5.0, f"{count} messages took {processing_time:.3f}s, expected <5.0s"

            print(f"{count} messages: {processing_time:.3f}s ({messages_per_second:.1f} msg/s)")

        # Verify performance scales reasonably
        if len(results) >= 2:
            throughput_10 = results[10]["messages_per_second"]
            throughput_100 = results[100]["messages_per_second"]

            # Throughput should not degrade significantly (allow 50% degradation)
            assert throughput_100 > throughput_10 * 0.5, \
                f"Throughput degradation too severe: {throughput_10:.1f} -> {throughput_100:.1f} msg/s"

    @pytest.mark.asyncio
    async def test_search_performance(self, memory_service):
        """Test semantic search performance"""
        # Mock search results to avoid actual search time
        mock_results = []
        for i in range(5):
            result = Mock()
            result.score = 0.8 - i * 0.1
            result.payload = {
                "text": f"Resultado de búsqueda {i}",
                "conversation_id": f"conv_{i}",
                "child_id": "test_child",
                "topic": "test",
                "role": "user",
                "emotion": "positive",
                "timestamp": time.time(),
                "message_index": i
            }
            mock_results.append(result)

        memory_service.embedding_model.encode = Mock(return_value=[0.1] * settings.embedding_dimension)
        memory_service._client.search = Mock(return_value=mock_results)

        queries = ["búsqueda simple", "consulta más compleja con más palabras", "test query"]
        search_times = []

        for query in queries:
            start_time = time.time()
            results = await memory_service.search_similar_conversations(
                query=query,
                child_id="test_child",
                limit=5
            )
            end_time = time.time()

            search_time = end_time - start_time
            search_times.append(search_time)

            # Search should complete within 200ms
            assert search_time < 0.2, f"Search for '{query}' took {search_time:.3f}s, expected <0.2s"
            assert len(results) <= 5, f"Search returned {len(results)} results, expected <=5"

        avg_search_time = statistics.mean(search_times)
        print(f"Average search time: {avg_search_time:.3f}s")
        print(f"Search times: {[f'{t:.3f}s' for t in search_times]}")

    @pytest.mark.asyncio
    async def test_context_retrieval_performance(self, memory_service):
        """Test context retrieval performance"""
        # Mock search results for context
        mock_context = [
            {
                "text": "Contexto relevante 1",
                "score": 0.9,
                "timestamp": time.time()
            },
            {
                "text": "Contexto relevante 2",
                "score": 0.8,
                "timestamp": time.time()
            }
        ]

        with patch.object(memory_service, 'search_similar_conversations', return_value=mock_context):
            start_time = time.time()
            context = await memory_service.get_conversation_context(
                child_id="test_child",
                topic="hobbies",
                limit=3
            )
            end_time = time.time()

            retrieval_time = end_time - start_time

            # Context retrieval should complete within 500ms
            assert retrieval_time < 0.5, f"Context retrieval took {retrieval_time:.3f}s, expected <0.5s"
            assert len(context) <= 3, f"Context returned {len(context)} items, expected <=3"

            print(f"Context retrieval time: {retrieval_time:.3f}s")

    @pytest.mark.asyncio
    async def test_concurrent_operations_performance(self, memory_service):
        """Test performance under concurrent operations"""
        message_count = 20
        concurrent_operations = 5

        async def store_conversation_batch(batch_id: int):
            messages = generate_test_messages(message_count)
            return await memory_service.store_conversation(
                conversation_id=f"concurrent_test_{batch_id}",
                child_id=f"test_child_{batch_id}",
                messages=messages
            )

        # Run concurrent operations
        start_time = time.time()
        tasks = [store_conversation_batch(i) for i in range(concurrent_operations)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()

        total_time = end_time - start_time
        total_messages = message_count * concurrent_operations
        throughput = total_messages / total_time

        # All operations should succeed
        assert all(results), "Some concurrent operations failed"

        # Should handle concurrent operations efficiently
        assert total_time < 10.0, f"Concurrent operations took {total_time:.3f}s, expected <10s"
        assert throughput > 10, f"Throughput too low: {throughput:.1f} msg/s, expected >10 msg/s"

        print(f"Concurrent operations: {concurrent_operations} batches, {total_messages} messages")
        print(f"Total time: {total_time:.3f}s")
        print(f"Throughput: {throughput:.1f} messages/second")

    @pytest.mark.asyncio
    async def test_memory_efficiency(self, memory_service):
        """Test memory efficiency of operations"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Store many messages
        message_count = 1000
        messages = generate_test_messages(message_count)

        await memory_service.store_conversation(
            conversation_id="memory_efficiency_test",
            child_id="test_child",
            messages=messages
        )

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        memory_per_message = memory_increase / message_count  # KB per message

        # Memory usage should be reasonable (less than 10KB per message)
        assert memory_per_message < 10, f"Memory usage too high: {memory_per_message:.2f}KB per message"

        print(f"Memory efficiency test:")
        print(f"Initial memory: {initial_memory:.1f}MB")
        print(f"Final memory: {final_memory:.1f}MB")
        print(f"Memory increase: {memory_increase:.1f}MB")
        print(f"Memory per message: {memory_per_message:.2f}KB")

    @pytest.mark.asyncio
    async def test_cache_performance_if_available(self, memory_service):
        """Test caching performance benefits (if cache is implemented)"""
        # This test can be expanded when caching is added
        query = "test query for caching"
        child_id = "cache_test_child"

        # First search (cold cache)
        start_time = time.time()
        results1 = await memory_service.search_similar_conversations(
            query=query,
            child_id=child_id
        )
        first_search_time = time.time() - start_time

        # Second search (potentially warm cache)
        start_time = time.time()
        results2 = await memory_service.search_similar_conversations(
            query=query,
            child_id=child_id
        )
        second_search_time = time.time() - start_time

        print(f"First search: {first_search_time:.3f}s")
        print(f"Second search: {second_search_time:.3f}s")

        # Results should be consistent
        assert len(results1) == len(results2), "Search results inconsistent between calls"


@pytest.mark.asyncio
async def test_performance_benchmark_report(memory_service):
    """Generate a comprehensive performance benchmark report"""
    print("\n" + "="*60)
    print("MEMORY SERVICE PERFORMANCE BENCHMARK REPORT")
    print("="*60)

    # Test different message counts
    message_counts = [1, 10, 50, 100, 200]
    embedding_results = {}

    for count in message_counts:
        messages = generate_test_messages(count)

        # Measure embedding performance
        start_time = time.time()
        await memory_service.store_conversation(
            conversation_id=f"benchmark_{count}",
            child_id="benchmark_child",
            messages=messages
        )
        end_time = time.time()

        processing_time = end_time - start_time
        throughput = count / processing_time if processing_time > 0 else float('inf')

        embedding_results[count] = {
            "time": processing_time,
            "throughput": throughput
        }

        print(f"Messages: {count:3d} | Time: {processing_time:6.3f}s | Throughput: {throughput:6.1f} msg/s")

    # Test search performance
    search_queries = ["corta", "consulta de longitud media para búsqueda", "consulta más larga y compleja para probar rendimiento de búsqueda con más texto"]
    search_results = []

    for query in search_queries:
        start_time = time.time()
        results = await memory_service.search_similar_conversations(
            query=query,
            child_id="benchmark_child",
            limit=5
        )
        end_time = time.time()

        search_time = end_time - start_time
        search_results.append(search_time)
        print(f"Search query length {len(query):2d}: {search_time:.3f}s")

    # Summary statistics
    avg_search_time = statistics.mean(search_results)
    print(f"\nAverage search time: {avg_search_time:.3f}s")

    # Performance targets check
    print("\nPerformance Targets:")
    print("="*40)

    # Embedding targets
    for count, result in embedding_results.items():
        target_time = count * 0.01 + 0.05  # 10ms per message + 50ms overhead
        status = "✓" if result["time"] < target_time else "✗"
        print(f"{status} {count:3d} messages: {result['time']:.3f}s (target: <{target_time:.3f}s)")

    # Search targets
    search_target = 0.2  # 200ms
    search_status = "✓" if avg_search_time < search_target else "✗"
    print(f"{search_status} Average search: {avg_search_time:.3f}s (target: <{search_target:.3f}s)")

    print("\n" + "="*60)
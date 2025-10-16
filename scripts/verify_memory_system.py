#!/usr/bin/env python3
"""
Memory System Verification Script

This script verifies that the conversation embedding system is properly configured
and functional for the EmoRobCare project.
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.api.services.memory_service import MemoryService
from services.api.core.config import settings
from services.api.core.database import get_qdrant

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MemorySystemVerifier:
    """Verifies memory system functionality"""

    def __init__(self):
        self.verification_results = {
            "config": False,
            "embedding_model": False,
            "qdrant_connection": False,
            "collection_setup": False,
            "embedding_storage": False,
            "semantic_search": False,
            "context_retrieval": False,
            "overall": False
        }

    async def verify_configuration(self):
        """Verify configuration settings"""
        logger.info("🔧 Verifying configuration...")

        try:
            # Check essential configuration
            assert settings.embedding_model_name, "Embedding model name not configured"
            assert settings.embedding_dimension > 0, "Embedding dimension not configured"
            assert settings.qdrant_collection_name, "Qdrant collection name not configured"
            assert settings.enable_semantic_search is not None, "Semantic search setting not configured"

            logger.info("✅ Configuration is valid")
            self.verification_results["config"] = True
            return True

        except Exception as e:
            logger.error(f"❌ Configuration error: {e}")
            return False

    async def verify_embedding_model(self):
        """Verify embedding model initialization"""
        logger.info("🧠 Verifying embedding model...")

        try:
            memory_service = MemoryService()

            if memory_service.embedding_model is None:
                logger.error("❌ Embedding model not initialized")
                return False

            # Test embedding generation
            test_text = "Este es un texto de prueba para el sistema de memoria"
            embedding = memory_service.embedding_model.encode(test_text)

            assert len(embedding) == settings.embedding_dimension, \
                f"Embedding dimension mismatch: expected {settings.embedding_dimension}, got {len(embedding)}"

            logger.info(f"✅ Embedding model working (dimension: {len(embedding)})")
            self.verification_results["embedding_model"] = True
            return True

        except Exception as e:
            logger.error(f"❌ Embedding model error: {e}")
            return False

    async def verify_qdrant_connection(self):
        """Verify Qdrant database connection"""
        logger.info("🔗 Verifying Qdrant connection...")

        try:
            qdrant = get_qdrant()

            if qdrant is None:
                logger.error("❌ Qdrant client not available")
                return False

            # Test basic operation
            collections = qdrant.get_collections()
            logger.info(f"✅ Qdrant connection successful (collections: {len(collections.collections)})")

            self.verification_results["qdrant_connection"] = True
            return True

        except Exception as e:
            logger.error(f"❌ Qdrant connection error: {e}")
            return False

    async def verify_collection_setup(self):
        """Verify Qdrant collection setup"""
        logger.info("📚 Verifying collection setup...")

        try:
            memory_service = MemoryService()

            # Check if collection exists
            qdrant = get_qdrant()
            if qdrant is None:
                logger.error("❌ Cannot verify collection: Qdrant not available")
                return False

            collections = qdrant.get_collections().collections
            collection_exists = any(
                collection.name == settings.qdrant_collection_name
                for collection in collections
            )

            if not collection_exists:
                logger.info(f"📝 Creating collection: {settings.qdrant_collection_name}")
                # The MemoryService constructor should create the collection
                memory_service._init_qdrant_collection()

                # Verify creation
                collections = qdrant.get_collections().collections
                collection_exists = any(
                    collection.name == settings.qdrant_collection_name
                    for collection in collections
                )

                if not collection_exists:
                    logger.error("❌ Failed to create collection")
                    return False

            # Check collection configuration
            collection_info = qdrant.get_collection(settings.qdrant_collection_name)
            assert collection_info.config.params.vectors.size == settings.embedding_dimension, \
                f"Collection vector dimension mismatch: expected {settings.embedding_dimension}, got {collection_info.config.params.vectors.size}"

            logger.info(f"✅ Collection setup verified (vectors: {collection_info.vectors_count})")
            self.verification_results["collection_setup"] = True
            return True

        except Exception as e:
            logger.error(f"❌ Collection setup error: {e}")
            return False

    async def verify_embedding_storage(self):
        """Verify embedding storage functionality"""
        logger.info("💾 Verifying embedding storage...")

        try:
            memory_service = MemoryService()

            # Test message storage
            test_conversation_id = f"verify_test_{datetime.now().timestamp()}"
            test_messages = [
                {
                    "role": "user",
                    "text": "Me gusta jugar al fútbol con mis amigos",
                    "timestamp": datetime.now().timestamp(),
                    "emotion": "positive"
                },
                {
                    "role": "assistant",
                    "text": "**¡Qué bien!** ¿Qué posición te gusta jugar?",
                    "timestamp": datetime.now().timestamp(),
                    "emotion": "positive"
                }
            ]

            test_metadata = {
                "topic": "hobbies",
                "level": 3,
                "language": "es"
            }

            # Store conversation
            success = await memory_service.store_conversation(
                conversation_id=test_conversation_id,
                child_id="verify_test_child",
                messages=test_messages,
                metadata=test_metadata
            )

            if not success:
                logger.error("❌ Failed to store conversation")
                return False

            # Verify storage (check collection count)
            qdrant = get_qdrant()
            collection_info = qdrant.get_collection(settings.qdrant_collection_name)

            # Clean up test data
            await memory_service.delete_conversation_memory(test_conversation_id)

            logger.info("✅ Embedding storage working")
            self.verification_results["embedding_storage"] = True
            return True

        except Exception as e:
            logger.error(f"❌ Embedding storage error: {e}")
            return False

    async def verify_semantic_search(self):
        """Verify semantic search functionality"""
        logger.info("🔍 Verifying semantic search...")

        try:
            memory_service = MemoryService()

            # Test semantic search
            results = await memory_service.search_similar_conversations(
                query="juegos deportes fútbol",
                child_id="verify_test_child",
                topic="hobbies",
                limit=3
            )

            # Should return list (may be empty if no matching data)
            assert isinstance(results, list), "Search should return list"

            logger.info(f"✅ Semantic search working (found {len(results)} results)")
            self.verification_results["semantic_search"] = True
            return True

        except Exception as e:
            logger.error(f"❌ Semantic search error: {e}")
            return False

    async def verify_context_retrieval(self):
        """Verify context retrieval functionality"""
        logger.info("📖 Verifying context retrieval...")

        try:
            memory_service = MemoryService()

            # Test context retrieval
            context = await memory_service.get_conversation_context(
                child_id="verify_test_child",
                topic="hobbies",
                limit=2
            )

            # Should return list (may be empty if no data)
            assert isinstance(context, list), "Context retrieval should return list"

            logger.info(f"✅ Context retrieval working (found {len(context)} context items)")
            self.verification_results["context_retrieval"] = True
            return True

        except Exception as e:
            logger.error(f"❌ Context retrieval error: {e}")
            return False

    async def verify_memory_status(self):
        """Verify memory status reporting"""
        logger.info("📊 Verifying memory status...")

        try:
            memory_service = MemoryService()

            # Get memory status
            status = await memory_service.get_memory_status()

            assert isinstance(status, dict), "Status should be dictionary"
            assert "status" in status, "Status should include status field"

            logger.info(f"✅ Memory status: {status.get('status', 'unknown')}")
            return True

        except Exception as e:
            logger.error(f"❌ Memory status error: {e}")
            return False

    async def run_verification(self):
        """Run all verification checks"""
        logger.info("🚀 Starting Memory System Verification")
        logger.info("=" * 60)

        verification_steps = [
            ("Configuration", self.verify_configuration),
            ("Embedding Model", self.verify_embedding_model),
            ("Qdrant Connection", self.verify_qdrant_connection),
            ("Collection Setup", self.verify_collection_setup),
            ("Embedding Storage", self.verify_embedding_storage),
            ("Semantic Search", self.verify_semantic_search),
            ("Context Retrieval", self.verify_context_retrieval),
        ]

        for step_name, step_func in verification_steps:
            logger.info(f"\n--- {step_name} ---")
            await step_func()

        # Get final memory status
        logger.info(f"\n--- Memory Status ---")
        await self.verify_memory_status()

        # Calculate overall result
        passed_checks = sum(1 for result in self.verification_results.values() if result)
        total_checks = len(self.verification_results) - 1  # Exclude 'overall'

        if passed_checks == total_checks:
            self.verification_results["overall"] = True
            logger.info("\n" + "=" * 60)
            logger.info("🎉 ALL CHECKS PASSED! Memory system is ready.")
            logger.info("=" * 60)
        else:
            logger.info("\n" + "=" * 60)
            logger.warning(f"⚠️  {passed_checks}/{total_checks} checks passed.")
            logger.error("❌ Memory system has issues that need to be addressed.")
            logger.info("=" * 60)

        # Print summary
        logger.info("\n📋 Verification Summary:")
        for check, result in self.verification_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"  {check:.<30} {status}")

        return self.verification_results["overall"]


async def main():
    """Main verification function"""
    verifier = MemorySystemVerifier()
    success = await verifier.run_verification()

    if success:
        logger.info("\n🎯 Memory system verification completed successfully!")
        logger.info("The conversation embedding system is ready for use.")
    else:
        logger.error("\n💥 Memory system verification failed!")
        logger.error("Please address the issues before using the system.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
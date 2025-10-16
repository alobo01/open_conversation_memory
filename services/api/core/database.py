from motor.motor_asyncio import AsyncIOMotorClient
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from .config import settings

logger = logging.getLogger(__name__)

# MongoDB connections
mongodb_client: Optional[AsyncIOMotorClient] = None
database = None

# Qdrant connection
qdrant_client: Optional[QdrantClient] = None

async def init_db():
    """Initialize database connections"""
    global mongodb_client, database, qdrant_client

    try:
        # Initialize MongoDB
        mongodb_client = AsyncIOMotorClient(settings.mongodb_uri)
        database = mongodb_client[settings.mongodb_db_name]

        # Create collections with indexes
        await setup_mongodb_collections()

        # Initialize Qdrant
        qdrant_client = QdrantClient(settings.qdrant_url)
        await setup_qdrant_collections()

        logger.info("Database connections initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize database connections: {e}")
        raise

async def setup_mongodb_collections():
    """Setup MongoDB collections and indexes"""
    try:
        # Children collection
        await database.children.create_index("child_id", unique=True)
        await database.children.create_index("name")

        # Conversations collection
        await database.conversations.create_index("conversation_id", unique=True)
        await database.conversations.create_index("child_id")
        await database.conversations.create_index("created_at")

        # Messages collection
        await database.messages.create_index("conversation_id")
        await database.messages.create_index("timestamp")
        await database.messages.create_index([("conversation_id", 1), ("timestamp", 1)])

        # Topics collection
        await database.topics.create_index("topic_id", unique=True)
        await database.topics.create_index("name")

        # Profiles collection
        await database.profiles.create_index("child_id", unique=True)

        logger.info("MongoDB collections and indexes created successfully")

    except Exception as e:
        logger.error(f"Failed to setup MongoDB collections: {e}")
        raise

async def setup_qdrant_collections():
    """Setup Qdrant collections for vector search"""
    try:
        # Conversations collection for semantic search
        if not qdrant_client.collection_exists(settings.qdrant_collection_name):
            qdrant_client.create_collection(
                collection_name=settings.qdrant_collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )

        logger.info("Qdrant collections created successfully")

    except Exception as e:
        logger.error(f"Failed to setup Qdrant collections: {e}")
        raise

# Database getters
def get_db():
    """Get MongoDB database instance"""
    return database

def get_qdrant():
    """Get Qdrant client instance"""
    return qdrant_client

async def close_db():
    """Close database connections"""
    global mongodb_client, qdrant_client

    if mongodb_client:
        mongodb_client.close()

    # Qdrant client doesn't need explicit closing
    logger.info("Database connections closed")
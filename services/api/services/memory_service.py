import logging
from typing import Dict, Any, List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue

from ..core.config import settings
from ..core.database import get_qdrant, get_db

logger = logging.getLogger(__name__)

class MemoryService:
    """Service for managing conversation memory and semantic search"""

    def __init__(self):
        self.embedding_model = None
        self.qdrant_client = None
        self.collection_name = settings.qdrant_collection_name
        self._init_embedding_model()

    def _init_embedding_model(self):
        """Initialize sentence transformer model"""
        try:
            # Use a multilingual model for Spanish/English from config
            self.embedding_model = SentenceTransformer(settings.embedding_model_name)
            logger.info(f"Embedding model {settings.embedding_model_name} initialized successfully")

            # Initialize Qdrant collection if needed
            self._init_qdrant_collection()

        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            self.embedding_model = None

    def _init_qdrant_collection(self):
        """Initialize Qdrant collection for conversation embeddings"""
        try:
            qdrant = get_qdrant()
            if not qdrant:
                logger.warning("Qdrant client not available for collection initialization")
                return

            # Store the client for consistent use
            self.qdrant_client = qdrant

            # Check if collection exists
            collections = qdrant.get_collections().collections
            collection_exists = any(
                collection.name == self.collection_name
                for collection in collections
            )

            if not collection_exists:
                # Create collection with optimal configuration
                qdrant.create_collection(
                    collection_name=self.collection_name,
                    vectors_config={
                        "size": settings.embedding_dimension,
                        "distance": "Cosine"
                    }
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
            else:
                # Verify collection configuration
                collection_info = qdrant.get_collection(self.collection_name)
                if collection_info.config.params.vectors.size != settings.embedding_dimension:
                    logger.warning(
                        f"Collection vector dimension mismatch: "
                        f"expected {settings.embedding_dimension}, "
                        f"got {collection_info.config.params.vectors.size}"
                    )

        except Exception as e:
            logger.error(f"Failed to initialize Qdrant collection: {e}")

    async def store_conversation(
        self,
        conversation_id: str,
        child_id: str,
        messages: List[Dict[str, Any]],
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Store conversation in vector memory"""
        try:
            if not self.embedding_model:
                logger.warning("Embedding model not available, skipping storage")
                return False

            if not settings.enable_semantic_search:
                logger.debug("Semantic search disabled, skipping storage")
                return False

            if not self.qdrant_client:
                logger.warning("Qdrant client not available")
                return False

            # Create embeddings for both user and assistant messages
            points = []
            for i, message in enumerate(messages):
                text = message.get("text", "")
                if text and len(text.strip()) > 0:
                    # Clean text by removing emotion markup for embedding
                    clean_text = self._clean_text_for_embedding(text)

                    # Create embedding
                    embedding = self.embedding_model.encode(
                        clean_text,
                        convert_to_tensor=True,
                        normalize_embeddings=True
                    ).tolist()

                    # Create point with comprehensive metadata
                    point = PointStruct(
                        id=f"{conversation_id}_{message.get('role', 'unknown')}_{i}",
                        vector=embedding,
                        payload={
                            "conversation_id": conversation_id,
                            "child_id": child_id,
                            "text": text,
                            "clean_text": clean_text,
                            "role": message.get("role"),
                            "emotion": message.get("emotion"),
                            "timestamp": message.get("timestamp"),
                            "topic": metadata.get("topic") if metadata else None,
                            "level": metadata.get("level") if metadata else None,
                            "language": metadata.get("language") if metadata else None,
                            "message_index": i
                        }
                    )
                    points.append(point)

            # Store in Qdrant in batches for better performance
            if points:
                batch_size = settings.embedding_batch_size
                for i in range(0, len(points), batch_size):
                    batch = points[i:i + batch_size]
                    self.qdrant_client.upsert(
                        collection_name=self.collection_name,
                        points=batch
                    )

                logger.info(f"Stored {len(points)} messages for conversation {conversation_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error storing conversation: {e}")
            return False

    def _clean_text_for_embedding(self, text: str) -> str:
        """Clean text by removing emotion markup for better embedding quality"""
        import re

        # Remove emotion markup (bold and underscore patterns)
        clean_text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Remove **bold**
        clean_text = re.sub(r'__(.*?)__', r'\1', clean_text)  # Remove __underscore__

        # Remove extra whitespace
        clean_text = ' '.join(clean_text.split())

        return clean_text.strip()

    async def store_single_message(
        self,
        conversation_id: str,
        child_id: str,
        message: Dict[str, Any],
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Store a single message in vector memory"""
        return await self.store_conversation(
            conversation_id=conversation_id,
            child_id=child_id,
            messages=[message],
            metadata=metadata
        )

    async def search_similar_conversations(
        self,
        query: str,
        child_id: Optional[str] = None,
        topic: Optional[str] = None,
        role: Optional[str] = None,
        limit: Optional[int] = None,
        min_score: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Search for similar conversations with advanced filtering"""
        try:
            if not self.embedding_model or not settings.enable_semantic_search:
                logger.debug("Semantic search disabled or model not available")
                return []

            if not self.qdrant_client:
                logger.warning("Qdrant client not available")
                return []

            # Clean query for better embedding
            clean_query = self._clean_text_for_embedding(query)

            # Create query embedding with normalization
            query_embedding = self.embedding_model.encode(
                clean_query,
                convert_to_tensor=True,
                normalize_embeddings=True
            ).tolist()

            # Build filter conditions
            filter_conditions = []
            if child_id:
                filter_conditions.append(
                    FieldCondition(key="child_id", match=MatchValue(value=child_id))
                )
            if topic:
                filter_conditions.append(
                    FieldCondition(key="topic", match=MatchValue(value=topic))
                )
            if role:
                filter_conditions.append(
                    FieldCondition(key="role", match=MatchValue(value=role))
                )

            search_filter = Filter(must=filter_conditions) if filter_conditions else None

            # Set search limit from config if not provided
            search_limit = limit or settings.semantic_search_limit

            # Search with score threshold
            results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=search_filter,
                limit=search_limit * 2,  # Get more results to filter by score
                with_payload=True,
                with_score=True,
                score_threshold=min_score
            )

            # Format and filter results
            formatted_results = []
            seen_conversations = set()

            for result in results:
                # Filter by minimum score
                if result.score < min_score:
                    continue

                conversation_id = result.payload.get("conversation_id")

                # Avoid duplicate conversations from same chat
                if conversation_id in seen_conversations:
                    continue

                seen_conversations.add(conversation_id)

                formatted_results.append({
                    "text": result.payload.get("text"),
                    "clean_text": result.payload.get("clean_text"),
                    "conversation_id": conversation_id,
                    "child_id": result.payload.get("child_id"),
                    "topic": result.payload.get("topic"),
                    "role": result.payload.get("role"),
                    "emotion": result.payload.get("emotion"),
                    "score": result.score,
                    "timestamp": result.payload.get("timestamp"),
                    "message_index": result.payload.get("message_index")
                })

                # Limit results
                if len(formatted_results) >= search_limit:
                    break

            return formatted_results

        except Exception as e:
            logger.error(f"Error searching similar conversations: {e}")
            return []

    async def get_conversation_context(
        self,
        child_id: str,
        topic: Optional[str] = None,
        query: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get relevant context for conversation enhancement"""
        try:
            if not self.embedding_model or not settings.enable_semantic_search:
                logger.debug("Semantic search disabled or model not available")
                return []

            # Use context limit from config if not provided
            context_limit = limit or settings.context_retrieval_limit

            # Build contextual queries based on topic and optional query
            contextual_queries = []

            if query:
                contextual_queries.append(query)

            if topic:
                # Topic-specific contextual queries
                topic_contexts = {
                    "school": ["aprendizaje", "clases", "profesores", "amigos del cole"],
                    "hobbies": ["juegos", "actividades", "tiempo libre", "divertido"],
                    "holidays": ["vacaciones", "viajes", "familia", "días libres"],
                    "food": ["comida", "comer", "cocina", "platos favoritos"],
                    "friends": ["amigos", "jugar juntos", "amistad", "compañeros"]
                }
                contextual_queries.extend(topic_contexts.get(topic, []))

            # General conversational context queries
            general_contexts = [
                "me gusta", "quiero", "siento", "hice", "pasó", "cuando", "donde"
            ]
            contextual_queries.extend(general_contexts)

            # Search across all contextual queries
            all_results = []
            seen_messages = set()

            for search_query in contextual_queries[:5]:  # Limit to prevent too many searches
                results = await self.search_similar_conversations(
                    query=search_query,
                    child_id=child_id,
                    topic=topic,
                    limit=context_limit // 2,  # Split limit across queries
                    min_score=0.2  # Lower threshold for broader context
                )

                for result in results:
                    message_key = (
                        result.get("conversation_id"),
                        result.get("message_index")
                    )
                    if message_key not in seen_messages:
                        seen_messages.add(message_key)
                        all_results.append(result)

            # Sort by relevance (score + recency)
            def sort_key(item):
                score = item.get("score", 0)
                timestamp = item.get("timestamp", 0)
                # Prioritize recent conversations with good scores
                return score * 0.7 + (timestamp / 1000000000) * 0.3 if timestamp else score

            all_results.sort(key=sort_key, reverse=True)

            # Return formatted results
            return all_results[:context_limit]

        except Exception as e:
            logger.error(f"Error getting conversation context: {e}")
            return []

    async def get_semantic_memory_summary(
        self,
        child_id: str,
        topic: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get semantic memory summary for analytics"""
        try:
            if not settings.enable_semantic_search:
                return {"status": "disabled"}

            if not self.qdrant_client:
                return {"status": "unavailable"}

            # Build filter
            filter_conditions = [
                FieldCondition(key="child_id", match=MatchValue(value=child_id))
            ]
            if topic:
                filter_conditions.append(
                    FieldCondition(key="topic", match=MatchValue(value=topic))
                )

            search_filter = Filter(must=filter_conditions)

            # Get count and sample results
            results = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                scroll_filter=search_filter,
                limit=100,
                with_payload=True
            )[0]

            # Analyze results
            total_messages = len(results)
            user_messages = sum(1 for r in results if r.payload.get("role") == "user")
            assistant_messages = sum(1 for r in results if r.payload.get("role") == "assistant")

            # Extract common themes (simplified)
            topics_count = {}
            emotions_count = {}
            recent_conversations = set()

            for result in results:
                # Count topics
                result_topic = result.payload.get("topic")
                if result_topic:
                    topics_count[result_topic] = topics_count.get(result_topic, 0) + 1

                # Count emotions
                emotion = result.payload.get("emotion")
                if emotion:
                    emotions_count[emotion] = emotions_count.get(emotion, 0) + 1

                # Track recent conversations
                conv_id = result.payload.get("conversation_id")
                if conv_id:
                    recent_conversations.add(conv_id)

            return {
                "status": "available",
                "total_messages": total_messages,
                "user_messages": user_messages,
                "assistant_messages": assistant_messages,
                "unique_conversations": len(recent_conversations),
                "topics_distribution": topics_count,
                "emotions_distribution": emotions_count,
                "most_discussed_topics": sorted(
                    topics_count.items(), key=lambda x: x[1], reverse=True
                )[:5]
            }

        except Exception as e:
            logger.error(f"Error getting semantic memory summary: {e}")
            return {"status": "error", "error": str(e)}

    async def get_child_topics(self, child_id: str) -> List[str]:
        """Get topics discussed with a child"""
        try:
            db = get_db()
            if not db:
                return []

            # Get unique topics from conversations
            pipeline = [
                {"$match": {"child_id": child_id}},
                {"$group": {"_id": "$topic", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]

            topics = await db.conversations.aggregate(pipeline).to_list(None)

            return [topic["_id"] for topic in topics if topic["_id"]]

        except Exception as e:
            logger.error(f"Error getting child topics: {e}")
            return []

    async def get_conversation_stats(self, child_id: str) -> Dict[str, Any]:
        """Get conversation statistics for a child"""
        try:
            db = get_db()
            if not db:
                return {}

            # Get basic stats
            stats = {}

            # Total conversations
            total_conv = await db.conversations.count_documents({"child_id": child_id})
            stats["total_conversations"] = total_conv

            # Total messages
            message_pipeline = [
                {"$lookup": {
                    "from": "conversations",
                    "localField": "conversation_id",
                    "foreignField": "conversation_id",
                    "as": "conv"
                }},
                {"$match": {"conv.child_id": child_id}},
                {"$count": "total_messages"}
            ]

            message_result = await db.messages.aggregate(message_pipeline).to_list(None)
            stats["total_messages"] = message_result[0]["total_messages"] if message_result else 0

            # Topics distribution
            topic_pipeline = [
                {"$match": {"child_id": child_id}},
                {"$group": {"_id": "$topic", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]

            topics = await db.conversations.aggregate(topic_pipeline).to_list(None)
            stats["topics"] = [{"topic": t["_id"], "count": t["count"]} for t in topics]

            # Average conversation length
            length_pipeline = [
                {"$match": {"child_id": child_id}},
                {"$group": {
                    "_id": "$conversation_id",
                    "message_count": {"$first": "$message_count"}
                }},
                {"$group": {
                    "_id": None,
                    "avg_length": {"$avg": "$message_count"}
                }}
            ]

            length_result = await db.conversations.aggregate(length_pipeline).to_list(None)
            stats["avg_conversation_length"] = round(
                length_result[0]["avg_length"], 1
            ) if length_result else 0

            return stats

        except Exception as e:
            logger.error(f"Error getting conversation stats: {e}")
            return {}

    async def delete_conversation_memory(self, conversation_id: str) -> bool:
        """Delete conversation from vector memory"""
        try:
            if not self.qdrant_client:
                return False

            # Delete points for this conversation
            filter_condition = Filter(
                must=[FieldCondition(key="conversation_id", match=MatchValue(value=conversation_id))]
            )

            self.qdrant_client.delete(
                collection_name=self.collection_name,
                points_selector=filter_condition
            )

            logger.info(f"Deleted conversation {conversation_id} from vector memory")
            return True

        except Exception as e:
            logger.error(f"Error deleting conversation memory: {e}")
            return False

    async def get_memory_status(self) -> Dict[str, Any]:
        """Get memory service status"""
        try:
            if not self.qdrant_client:
                return {"status": "unavailable", "reason": "Qdrant client not available"}

            # Get collection info
            collection_info = self.qdrant_client.get_collection(self.collection_name)

            return {
                "status": "available",
                "embedding_model": "paraphrase-multilingual-MiniLM-L12-v2",
                "collection_name": self.collection_name,
                "vectors_count": collection_info.vectors_count,
                "indexed_vectors_count": collection_info.indexed_vectors_count,
                "vector_size": collection_info.config.params.vectors.size
            }

        except Exception as e:
            logger.error(f"Error getting memory status: {e}")
            return {"status": "error", "reason": str(e)}

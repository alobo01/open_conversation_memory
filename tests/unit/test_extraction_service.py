import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from services.api.services.extraction_service import ExtractionService
from services.api.models.extraction_models import (
    ExtractedEntity, ExtractedRelationship, ExtractionResult,
    EntityType, RelationshipType, ValidationReport
)
from services.api.models.schemas import Message


class TestExtractionService:
    """Test suite for ExtractionService"""

    @pytest.fixture
    def extraction_service(self):
        """Create extraction service instance"""
        return ExtractionService()

    @pytest.fixture
    def sample_messages(self):
        """Create sample conversation messages"""
        return [
            Message(
                conversation_id="conv_123",
                role="user",
                text="Me gusta jugar en el parque con mis amigos",
                timestamp=datetime.now()
            ),
            Message(
                conversation_id="conv_123",
                role="assistant",
                text="**¡Qué divertido!** ¿Qué juegos te gustan más?",
                timestamp=datetime.now()
            ),
            Message(
                conversation_id="conv_123",
                role="user",
                text="Me gusta el columpio y los toboganes",
                timestamp=datetime.now()
            )
        ]

    @pytest.fixture
    def sample_entities(self):
        """Create sample extracted entities"""
        return [
            ExtractedEntity(
                text="parque",
                type=EntityType.PLACE,
                confidence=0.95,
                start_pos=20,
                end_pos=25,
                normalized_form="parque"
            ),
            ExtractedEntity(
                text="amigos",
                type=EntityType.PERSON,
                confidence=0.90,
                start_pos=30,
                end_pos=36,
                normalized_form="amigos"
            ),
            ExtractedEntity(
                text="columpio",
                type=EntityType.OBJECT,
                confidence=0.88,
                start_pos=15,
                end_pos=22,
                normalized_form="columpio"
            )
        ]

    @pytest.fixture
    def sample_relationships(self):
        """Create sample extracted relationships"""
        return [
            ExtractedRelationship(
                subject="niño",
                predicate=RelationshipType.LIKES,
                object="parque",
                confidence=0.92,
                source_text="Me gusta jugar en el parque",
                context="niño le gusta el parque"
            ),
            ExtractedRelationship(
                subject="niño",
                predicate=RelationshipType.LIKES,
                object="columpio",
                confidence=0.85,
                source_text="Me gusta el columpio",
                context="niño le gusta el columpio"
            )
        ]

    @pytest.mark.asyncio
    async def test_extract_entities_from_conversation_success(
        self, extraction_service, sample_messages, sample_entities, sample_relationships
    ):
        """Test successful entity extraction from conversation"""
        # Mock LLM service responses
        with patch.object(extraction_service.llm_service, 'generate_response') as mock_llm:
            # Mock entity extraction response
            entities_response = """
            {
                "entities": [
                    {
                        "text": "parque",
                        "type": "place",
                        "confidence": 0.95,
                        "start_pos": 20,
                        "end_pos": 25,
                        "normalized_form": "parque"
                    },
                    {
                        "text": "amigos",
                        "type": "person",
                        "confidence": 0.90,
                        "start_pos": 30,
                        "end_pos": 36,
                        "normalized_form": "amigos"
                    }
                ]
            }
            """

            # Mock relationship extraction response
            relationships_response = """
            {
                "relationships": [
                    {
                        "subject": "niño",
                        "predicate": "likes",
                        "object": "parque",
                        "confidence": 0.92,
                        "source_text": "Me gusta jugar en el parque",
                        "context": "niño le gusta el parque"
                    }
                ]
            }
            """

            mock_llm.side_effect = [entities_response, relationships_response]

            # Execute extraction
            result = await extraction_service.extract_entities_from_conversation(
                conversation_id="conv_123",
                child_id="child_456",
                conversation_messages=sample_messages
            )

            # Assertions
            assert result.conversation_id == "conv_123"
            assert result.child_id == "child_456"
            assert len(result.entities) == 2
            assert len(result.relationships) == 1
            assert result.entities[0].text == "parque"
            assert result.entities[0].type == EntityType.PLACE
            assert result.relationships[0].predicate == RelationshipType.LIKES
            assert result.model_used is not None
            assert result.processing_time_ms > 0

    @pytest.mark.asyncio
    async def test_extract_entities_llm_invalid_json(self, extraction_service):
        """Test handling of invalid JSON response from LLM"""
        with patch.object(extraction_service.llm_service, 'generate_response') as mock_llm:
            # Return invalid JSON
            mock_llm.return_value = "This is not valid JSON"

            result = await extraction_service._extract_entities_llm(
                text="test conversation",
                child_id="child_123",
                conversation_id="conv_456"
            )

            assert result == []

    @pytest.mark.asyncio
    async def test_extract_entities_llm_low_confidence(self, extraction_service):
        """Test filtering of low-confidence entities"""
        with patch.object(extraction_service.llm_service, 'generate_response') as mock_llm:
            low_confidence_response = """
            {
                "entities": [
                    {
                        "text": "entidad_baja_confianza",
                        "type": "concept",
                        "confidence": 0.5,
                        "start_pos": 0,
                        "end_pos": 20,
                        "normalized_form": "entidad_baja_confianza"
                    }
                ]
            }
            """
            mock_llm.return_value = low_confidence_response

            result = await extraction_service._extract_entities_llm(
                text="test conversation",
                child_id="child_123",
                conversation_id="conv_456"
            )

            assert len(result) == 0  # Should be filtered out due to low confidence

    def test_convert_to_rdf_triples(self, extraction_service, sample_entities, sample_relationships):
        """Test conversion of entities and relationships to RDF triples"""
        triples = extraction_service.convert_to_rdf_triples(
            entities=sample_entities,
            relationships=sample_relationships,
            child_id="child_123",
            conversation_id="conv_456"
        )

        # Should have child entity, conversation link, entity types, and relationships
        assert len(triples) > 5

        # Check child entity creation
        child_triples = [t for t in triples if "child_123" in t.subject]
        assert len(child_triples) > 0

        # Check entity type mapping
        place_triples = [t for t in triples if t.object == "emo:Place"]
        assert len(place_triples) > 0

        # Check relationship mapping
        likes_triples = [t for t in triples if t.predicate == "emo:likes"]
        assert len(likes_triples) > 0

    def test_find_entity_uri(self, extraction_service, sample_entities):
        """Test finding entity URI by text"""
        uri = extraction_service._find_entity_uri(
            entities=sample_entities,
            entity_text="parque",
            base_uri="https://emorobcare.org/kg/",
            conversation_id="conv_123"
        )

        assert uri is not None
        assert "conv_123" in uri
        assert "parque" in uri

        # Test non-existent entity
        uri = extraction_service._find_entity_uri(
            entities=sample_entities,
            entity_text="non_existent",
            base_uri="https://emorobcare.org/kg/",
            conversation_id="conv_123"
        )

        assert uri is None

    def test_convert_triples_to_sparql(self, extraction_service):
        """Test conversion of RDF triples to SPARQL format"""
        from services.api.models.extraction_models import RDFTriple

        triples = [
            RDFTriple(
                subject="https://emorobcare.org/kg/child_123",
                predicate="rdf:type",
                object="emo:Child"
            ),
            RDFTriple(
                subject="https://emorobcare.org/kg/entity_456",
                predicate="rdf:type",
                object="emo:Place"
            )
        ]

        sparql = extraction_service._convert_triples_to_sparql(triples)

        assert "INSERT DATA" in sparql
        assert "emo:Child" in sparql
        assert "emo:Place" in sparql
        assert "https://emorobcare.org/kg/child_123" in sparql

    @pytest.mark.asyncio
    async def test_validate_with_shacl_success(self, extraction_service):
        """Test successful SHACL validation"""
        with patch('services.api.routers.knowledge_graph.validate_shacl') as mock_validate:
            mock_validate.return_value = {
                "valid": True,
                "violations": [],
                "shapes_checked": ["ChildShape", "EntityShape"]
            }

            triples = []  # Empty triples for simplicity

            result = await extraction_service.validate_with_shacl(triples)

            assert result.valid is True
            assert len(result.violations) == 0
            assert len(result.shapes_checked) == 2

    @pytest.mark.asyncio
    async def test_validate_with_shacl_failure(self, extraction_service):
        """Test SHACL validation failure"""
        with patch('services.api.routers.knowledge_graph.validate_shacl') as mock_validate:
            mock_validate.return_value = {
                "valid": False,
                "violations": [
                    {
                        "constraint": "ChildShape",
                        "message": "Child must have a name"
                    }
                ],
                "shapes_checked": ["ChildShape"]
            }

            triples = []  # Empty triples for simplicity

            result = await extraction_service.validate_with_shacl(triples)

            assert result.valid is False
            assert len(result.violations) == 1
            assert result.violations[0]["constraint"] == "ChildShape"

    def test_create_extraction_job(self, extraction_service):
        """Test creation of extraction job"""
        job_id = extraction_service.create_extraction_job(
            conversation_id="conv_123",
            child_id="child_456"
        )

        assert job_id is not None
        assert job_id in extraction_service.active_jobs

        job = extraction_service.active_jobs[job_id]
        assert job.conversation_id == "conv_123"
        assert job.child_id == "child_456"
        assert job.status == "pending"

    def test_get_job_status(self, extraction_service):
        """Test getting job status"""
        # Create a job first
        job_id = extraction_service.create_extraction_job(
            conversation_id="conv_123",
            child_id="child_456"
        )

        # Get status
        job = extraction_service.get_job_status(job_id)
        assert job is not None
        assert job.conversation_id == "conv_123"

        # Test non-existent job
        job = extraction_service.get_job_status("non_existent")
        assert job is None

    @pytest.mark.asyncio
    async def test_process_extraction_job_success(
        self, extraction_service, sample_messages, sample_entities, sample_relationships
    ):
        """Test successful processing of extraction job"""
        # Mock the extraction methods
        with patch.object(
            extraction_service, 'extract_entities_from_conversation'
        ) as mock_extract, \
        patch.object(extraction_service, 'validate_with_shacl') as mock_validate, \
        patch('services.api.routers.knowledge_graph.insert_to_kg') as mock_insert:

            # Setup mock extraction result
            extraction_result = ExtractionResult(
                conversation_id="conv_123",
                child_id="child_456",
                entities=sample_entities,
                relationships=sample_relationships,
                processing_time_ms=1500,
                model_used="test-model"
            )
            mock_extract.return_value = extraction_result

            # Setup mock validation
            mock_validate.return_value = ValidationReport(
                valid=True,
                violations=[],
                shapes_checked=["ChildShape"]
            )

            # Create and process job
            job_id = extraction_service.create_extraction_job(
                conversation_id="conv_123",
                child_id="child_456"
            )

            await extraction_service.process_extraction_job(
                job_id=job_id,
                conversation_id="conv_123",
                child_id="child_456",
                conversation_messages=sample_messages
            )

            # Check job status
            job = extraction_service.get_job_status(job_id)
            assert job.status == "completed"
            assert job.result is not None
            assert job.validation_report is not None
            assert job.result.conversation_id == "conv_123"

            # Verify methods were called
            mock_extract.assert_called_once()
            mock_validate.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_extraction_job_failure(self, extraction_service, sample_messages):
        """Test extraction job processing failure"""
        # Mock extraction to raise exception
        with patch.object(
            extraction_service, 'extract_entities_from_conversation'
        ) as mock_extract:
            mock_extract.side_effect = Exception("Extraction failed")

            job_id = extraction_service.create_extraction_job(
                conversation_id="conv_123",
                child_id="child_456"
            )

            await extraction_service.process_extraction_job(
                job_id=job_id,
                conversation_id="conv_123",
                child_id="child_456",
                conversation_messages=sample_messages
            )

            job = extraction_service.get_job_status(job_id)
            assert job.status == "failed"
            assert "Extraction failed" in job.error_message

    def test_combine_messages(self, extraction_service, sample_messages):
        """Test combining conversation messages into text"""
        combined = extraction_service._combine_messages(sample_messages)

        assert "Niño:" in combined
        assert "Asistente:" in combined
        assert "Me gusta jugar en el parque con mis amigos" in combined
        assert "¡Qué divertido! ¿Qué juegos te gustan más?" in combined

    def test_clean_text_for_embedding(self, extraction_service):
        """Test cleaning text for embedding"""
        text_with_markup = "**¡Qué bien!** Me gusta __mucho__ el parque."
        cleaned = extraction_service._clean_text_for_embedding(text_with_markup)

        assert "**" not in cleaned
        assert "__" not in cleaned
        assert "¡Qué bien! Me gusta mucho el parque." == cleaned
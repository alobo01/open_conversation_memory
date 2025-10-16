import logging
import json
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import asyncio
from pydantic import ValidationError

from ..models.extraction_models import (
    ExtractedEntity, ExtractedRelationship, ExtractionResult,
    RDFTriple, ValidationReport, ExtractionJob, EntityType, RelationshipType
)
from ..models.schemas import Message
from ..services.llm_service import LLMService
from ..routers.knowledge_graph import insert_to_kg, validate_shacl
from ..core.config import settings
from ..core.database import get_db

logger = logging.getLogger(__name__)

class ExtractionService:
    """Service for extracting entities and relationships from conversations"""

    def __init__(self):
        self.llm_service = LLMService()
        self.active_jobs: Dict[str, ExtractionJob] = {}

    async def extract_entities_from_conversation(
        self,
        conversation_id: str,
        child_id: str,
        conversation_messages: List[Message]
    ) -> ExtractionResult:
        """
        Extract entities and relationships from conversation messages using LLM
        """
        start_time = datetime.now()

        try:
            # Combine conversation messages into full text
            conversation_text = self._combine_messages(conversation_messages)

            # Extract entities using LLM
            entities = await self._extract_entities_llm(
                conversation_text, child_id, conversation_id
            )

            # Extract relationships using LLM
            relationships = await self._extract_relationships_llm(
                conversation_text, entities, child_id, conversation_id
            )

            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            result = ExtractionResult(
                conversation_id=conversation_id,
                child_id=child_id,
                entities=entities,
                relationships=relationships,
                processing_time_ms=int(processing_time),
                model_used=settings.llm_model_name,
                confidence_threshold=0.7
            )

            logger.info(f"Extraction completed for conversation {conversation_id}: "
                       f"{len(entities)} entities, {len(relationships)} relationships")

            return result

        except Exception as e:
            logger.error(f"Error extracting entities from conversation {conversation_id}: {e}")
            raise

    def _combine_messages(self, messages: List[Message]) -> str:
        """Combine conversation messages into a single text for processing"""
        combined = []
        for msg in messages:
            role_prefix = "Niño:" if msg.role == "user" else "Asistente:"
            combined.append(f"{role_prefix} {msg.text}")
        return " ".join(combined)

    async def _extract_entities_llm(
        self,
        text: str,
        child_id: str,
        conversation_id: str
    ) -> List[ExtractedEntity]:
        """Extract entities using LLM with structured output"""

        prompt = f"""
        Extrae entidades del siguiente texto de una conversación con un niño con TEA2.

        Texto: "{text}"

        Identifica entidades de los siguientes tipos:
        - person: personas (amigos, familiares, maestros)
        - place: lugares (colegio, parque, casa)
        - activity: actividades (jugar, estudiar, comer)
        - emotion: emociones (feliz, triste, enojado)
        - topic: temas (matemáticas, recreo)
        - object: objetos (juguete, libro)
        - concept: conceptos abstractos (amistad, aprendizaje)

        Responde en formato JSON con esta estructura:
        {{
            "entities": [
                {{
                    "text": "texto exacto de la entidad",
                    "type": "tipo de entidad",
                    "confidence": 0.95,
                    "start_pos": posición_inicio,
                    "end_pos": posición_fin,
                    "normalized_form": "forma normalizada"
                }}
            ]
        }}

        Solo incluye entidades con confianza >= 0.7.
        """

        try:
            # Get response from LLM
            response = await self.llm_service.generate_response(prompt)

            # Parse JSON response
            try:
                llm_result = json.loads(response)
                entities_data = llm_result.get("entities", [])
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse LLM response as JSON: {response}")
                entities_data = []

            # Convert to ExtractedEntity objects
            entities = []
            for entity_data in entities_data:
                try:
                    entity = ExtractedEntity(**entity_data)
                    if entity.confidence >= 0.7:
                        entities.append(entity)
                except ValidationError as e:
                    logger.warning(f"Invalid entity data: {entity_data}, error: {e}")
                    continue

            return entities

        except Exception as e:
            logger.error(f"Error in LLM entity extraction: {e}")
            return []

    async def _extract_relationships_llm(
        self,
        text: str,
        entities: List[ExtractedEntity],
        child_id: str,
        conversation_id: str
    ) -> List[ExtractedRelationship]:
        """Extract relationships between entities using LLM"""

        # Create entity lookup
        entity_lookup = {i: entity.text for i, entity in enumerate(entities)}

        prompt = f"""
        Extrae relaciones entre las siguientes entidades del texto de conversación.

        Entidades:
        {json.dumps(entity_lookup, indent=2, ensure_ascii=False)}

        Texto: "{text}"

        Tipos de relaciones permitidas:
        - likes: le gusta
        - dislikes: no le gusta
        - part_of: parte de
        - related_to: relacionado con
        - experienced: experimentó
        - mentioned: mencionó
        - feels: siente
        - knows: conoce
        - does: hace

        Responde en formato JSON:
        {{
            "relationships": [
                {{
                    "subject": "índice de entidad sujeto",
                    "predicate": "tipo de relación",
                    "object": "índice de entidad objeto",
                    "confidence": 0.9,
                    "source_text": "texto original donde se encuentra",
                    "context": "contexto circundante"
                }}
            ]
        }}

        Solo incluye relaciones con confianza >= 0.7.
        """

        try:
            # Get response from LLM
            response = await self.llm_service.generate_response(prompt)

            # Parse JSON response
            try:
                llm_result = json.loads(response)
                relationships_data = llm_result.get("relationships", [])
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse LLM relationships response as JSON: {response}")
                relationships_data = []

            # Convert to ExtractedRelationship objects
            relationships = []
            for rel_data in relationships_data:
                try:
                    # Convert entity indices to actual entity texts
                    if rel_data["subject"] in entity_lookup and rel_data["object"] in entity_lookup:
                        rel_data["subject"] = entity_lookup[rel_data["subject"]]
                        rel_data["object"] = entity_lookup[rel_data["object"]]

                        relationship = ExtractedRelationship(**rel_data)
                        if relationship.confidence >= 0.7:
                            relationships.append(relationship)
                except (ValidationError, KeyError) as e:
                    logger.warning(f"Invalid relationship data: {rel_data}, error: {e}")
                    continue

            return relationships

        except Exception as e:
            logger.error(f"Error in LLM relationship extraction: {e}")
            return []

    def convert_to_rdf_triples(
        self,
        entities: List[ExtractedEntity],
        relationships: List[ExtractedRelationship],
        child_id: str,
        conversation_id: str
    ) -> List[RDFTriple]:
        """Convert extracted entities and relationships to RDF triples"""

        triples = []
        base_uri = "https://emorobcare.org/kg/"

        # Create child URI
        child_uri = f"{base_uri}child/{child_id}"
        conversation_uri = f"{base_uri}conversation/{conversation_id}"

        # Add child entity
        triples.append(RDFTriple(
            subject=child_uri,
            predicate="rdf:type",
            object="emo:Child"
        ))

        triples.append(RDFTriple(
            subject=child_uri,
            predicate="emo:hasConversation",
            object=conversation_uri
        ))

        # Add entities as instances
        for i, entity in enumerate(entities):
            entity_uri = f"{base_uri}entity/{conversation_id}_{i}"

            # Entity type
            entity_type_mapping = {
                EntityType.PERSON: "emo:Person",
                EntityType.PLACE: "emo:Place",
                EntityType.ACTIVITY: "emo:Activity",
                EntityType.EMOTION: "emo:Emotion",
                EntityType.TOPIC: "emo:Topic",
                EntityType.OBJECT: "emo:Object",
                EntityType.CONCEPT: "emo:Concept"
            }

            if entity.type in entity_type_mapping:
                triples.append(RDFTriple(
                    subject=entity_uri,
                    predicate="rdf:type",
                    object=entity_type_mapping[entity.type]
                ))

                # Entity label
                triples.append(RDFTriple(
                    subject=entity_uri,
                    predicate="rdfs:label",
                    object=f'"{entity.text}"'
                ))

                # Connect entity to conversation
                triples.append(RDFTriple(
                    subject=conversation_uri,
                    predicate="emo:mentionsEntity",
                    object=entity_uri
                ))

        # Add relationships
        for relationship in relationships:
            # Find entity URIs for subject and object
            subject_uri = self._find_entity_uri(entities, relationship.subject, base_uri, conversation_id)
            object_uri = self._find_entity_uri(entities, relationship.object, base_uri, conversation_id)

            if subject_uri and object_uri:
                # Map relationship types to predicates
                predicate_mapping = {
                    RelationshipType.LIKES: "emo:likes",
                    RelationshipType.DISLIKES: "emo:dislikes",
                    RelationshipType.PART_OF: "emo:partOf",
                    RelationshipType.RELATED_TO: "emo:relatedTo",
                    RelationshipType.EXPERIENCED: "emo:experienced",
                    RelationshipType.MENTIONED: "emo:mentioned",
                    RelationshipType.FEELS: "emo:feels",
                    RelationshipType.KNOWS: "emo:knows",
                    RelationshipType.DOES: "emo:does"
                }

                if relationship.predicate in predicate_mapping:
                    triples.append(RDFTriple(
                        subject=subject_uri,
                        predicate=predicate_mapping[relationship.predicate],
                        object=object_uri
                    ))

        return triples

    def _find_entity_uri(
        self,
        entities: List[ExtractedEntity],
        entity_text: str,
        base_uri: str,
        conversation_id: str
    ) -> Optional[str]:
        """Find URI for entity text"""
        for i, entity in enumerate(entities):
            if entity.text == entity_text:
                return f"{base_uri}entity/{conversation_id}_{i}"
        return None

    async def validate_with_shacl(self, triples: List[RDFTriple]) -> ValidationReport:
        """Validate RDF triples against SHACL shapes"""
        try:
            # Convert triples to SPARQL update format
            sparql_insert = self._convert_triples_to_sparql(triples)

            # Validate using KG service
            validation_result = await validate_shacl({"data": sparql_insert})

            return ValidationReport(
                valid=validation_result.get("valid", False),
                violations=validation_result.get("violations", []),
                shapes_checked=validation_result.get("shapes_checked", [])
            )

        except Exception as e:
            logger.error(f"SHACL validation error: {e}")
            return ValidationReport(
                valid=False,
                violations=[{"error": str(e)}],
                shapes_checked=[]
            )

    def _convert_triples_to_sparql(self, triples: List[RDFTriple]) -> str:
        """Convert RDF triples to SPARQL INSERT format"""
        insert_statements = []

        for triple in triples:
            if triple.graph:
                insert_statements.append(
                    f"GRAPH <{triple.graph}> {{ <{triple.subject}> <{triple.predicate}> {triple.object} . }}"
                )
            else:
                insert_statements.append(
                    f"<{triple.subject}> <{triple.predicate}> {triple.object} ."
                )

        return f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX emo: <https://emorobcare.org/ontology#>

        INSERT DATA {{
            { " .\n            ".join(insert_statements) }
        }}
        """

    async def process_extraction_job(
        self,
        job_id: str,
        conversation_id: str,
        child_id: str,
        conversation_messages: List[Message]
    ) -> ExtractionJob:
        """Process a background extraction job"""

        job = self.active_jobs.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        try:
            # Update job status
            job.status = "processing"
            job.started_at = datetime.now()

            # Extract entities and relationships
            extraction_result = await self.extract_entities_from_conversation(
                conversation_id, child_id, conversation_messages
            )

            # Convert to RDF triples
            triples = self.convert_to_rdf_triples(
                extraction_result.entities,
                extraction_result.relationships,
                child_id,
                conversation_id
            )

            # Validate with SHACL
            validation_report = await self.validate_with_shacl(triples)

            # If validation passes, insert into knowledge graph
            if validation_report.valid:
                sparql_insert = self._convert_triples_to_sparql(triples)
                await insert_to_kg({"sparql_update": sparql_insert})
                logger.info(f"Successfully inserted {len(triples)} triples to KG")
            else:
                logger.warning(f"SHACL validation failed for conversation {conversation_id}")

            # Update job with results
            job.status = "completed"
            job.completed_at = datetime.now()
            job.result = extraction_result
            job.validation_report = validation_report

            logger.info(f"Extraction job {job_id} completed successfully")

        except Exception as e:
            job.status = "failed"
            job.completed_at = datetime.now()
            job.error_message = str(e)
            logger.error(f"Extraction job {job_id} failed: {e}")

        return job

    def create_extraction_job(self, conversation_id: str, child_id: str) -> str:
        """Create a new background extraction job"""
        job_id = str(uuid.uuid4())

        job = ExtractionJob(
            job_id=job_id,
            conversation_id=conversation_id,
            child_id=child_id,
            status="pending"
        )

        self.active_jobs[job_id] = job
        logger.info(f"Created extraction job {job_id} for conversation {conversation_id}")

        return job_id

    def get_job_status(self, job_id: str) -> Optional[ExtractionJob]:
        """Get status of an extraction job"""
        return self.active_jobs.get(job_id)
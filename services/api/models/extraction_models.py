from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from enum import Enum

class EntityType(str, Enum):
    PERSON = "person"
    PLACE = "place"
    ACTIVITY = "activity"
    EMOTION = "emotion"
    TOPIC = "topic"
    OBJECT = "object"
    CONCEPT = "concept"

class RelationshipType(str, Enum):
    LIKES = "likes"
    DISLIKES = "dislikes"
    PART_OF = "part_of"
    RELATED_TO = "related_to"
    EXPERIENCED = "experienced"
    MENTIONED = "mentioned"
    FEELS = "feels"
    KNOWS = "knows"
    DOES = "does"

class ExtractedEntity(BaseModel):
    """Represents an entity extracted from conversation"""
    text: str = Field(..., description="The entity text as it appears in conversation")
    type: EntityType = Field(..., description="The type of entity")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score from extraction")
    start_pos: int = Field(..., description="Start position in conversation text")
    end_pos: int = Field(..., description="End position in conversation text")
    normalized_form: Optional[str] = Field(None, description="Normalized/canonical form of entity")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class ExtractedRelationship(BaseModel):
    """Represents a relationship between entities"""
    subject: str = Field(..., description="Subject entity identifier")
    predicate: RelationshipType = Field(..., description="Relationship type")
    object: str = Field(..., description="Object entity identifier")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    source_text: str = Field(..., description="Original text where relationship was found")
    context: Optional[str] = Field(None, description="Surrounding context")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class ExtractionResult(BaseModel):
    """Complete extraction result from a conversation"""
    conversation_id: str
    child_id: str
    entities: List[ExtractedEntity]
    relationships: List[ExtractedRelationship]
    extraction_timestamp: datetime = Field(default_factory=datetime.now)
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")
    model_used: Optional[str] = Field(None, description="LLM model used for extraction")
    confidence_threshold: float = Field(0.7, description="Minimum confidence threshold")

class RDFTriple(BaseModel):
    """RDF triple representation"""
    subject: str
    predicate: str
    object: str
    graph: Optional[str] = Field(None, description="Named graph URI")

class ValidationReport(BaseModel):
    """SHACL validation report"""
    valid: bool = Field(..., description="Whether the data passed SHACL validation")
    violations: List[Dict[str, Any]] = Field(default_factory=list, description="SHACL violations found")
    validation_timestamp: datetime = Field(default_factory=datetime.now)
    shapes_checked: List[str] = Field(default_factory=list, description="SHACL shapes that were checked")

class ExtractionJob(BaseModel):
    """Background extraction job status"""
    job_id: str
    conversation_id: str
    status: Literal["pending", "processing", "completed", "failed"] = "pending"
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = Field(None)
    completed_at: Optional[datetime] = Field(None)
    error_message: Optional[str] = Field(None)
    result: Optional[ExtractionResult] = Field(None)
    validation_report: Optional[ValidationReport] = Field(None)

class EntityExtractionRequest(BaseModel):
    """Request for entity extraction"""
    conversation_text: str
    child_id: str
    conversation_id: str
    language: Optional[str] = Field("es", description="Language code")
    confidence_threshold: float = Field(0.7, ge=0.0, le=1.0)
    include_relationships: bool = Field(True)

class EntityExtractionResponse(BaseModel):
    """Response from entity extraction"""
    success: bool
    entities: List[ExtractedEntity]
    relationships: List[ExtractedRelationship]
    processing_time_ms: int
    model_used: str
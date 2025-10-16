# EmoRobCare Knowledge Graph API Implementation

This document describes the complete implementation of the Knowledge Graph API endpoints for the EmoRobCare project.

## Overview

The Knowledge Graph API provides comprehensive SPARQL-based access to the EmoRobCare RDF knowledge graph stored in Apache Jena Fuseki. It supports data manipulation, validation, reasoning, and semantic queries.

## Implemented Endpoints

### 1. GET /kg/query
Execute SPARQL SELECT queries against the knowledge graph.

**Parameters:**
- `query` (required): SPARQL SELECT query
- `limit` (optional): Maximum number of results (default: 100)

**Response:**
```json
{
  "results": [...],
  "success": true,
  "execution_time": 0.123,
  "total_count": 42
}
```

**Example:**
```bash
curl "http://localhost:8000/kg/query?query=SELECT%20?s%20?p%20?o%20WHERE%20{%20?s%20?p%20?o%20}%20LIMIT%2010"
```

### 2. POST /kg/insert
Insert new triples into the knowledge graph using SPARQL INSERT DATA queries.

**Request Body:**
```json
{
  "sparql_update": "INSERT DATA { <s> <p> <o> . }"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Data inserted successfully",
  "execution_time": 0.045
}
```

### 3. POST /kg/update
Update existing triples using SPARQL DELETE/INSERT or MODIFY queries.

**Request Body:**
```json
{
  "sparql_update": "DELETE WHERE { <s> <p> ?o } ; INSERT WHERE { <s> <p> <o> }"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Data updated successfully",
  "execution_time": 0.067
}
```

### 4. GET /kg/validate
Validate the knowledge graph against SHACL shapes for data quality and consistency.

**Response:**
```json
{
  "conforms": true,
  "violations": [],
  "validation_time": 0.234
}
```

### 5. GET /kg/reason
Perform OWL 2 DL reasoning to check consistency and infer new knowledge.

**Response:**
```json
{
  "consistent": true,
  "violations": [],
  "reasoning_time": 0.156
}
```

### 6. GET /kg/schema
Retrieve ontology schema information including classes, properties, and individuals.

**Response:**
```json
{
  "classes": [...],
  "properties": [...],
  "individuals": [...],
  "namespaces": {...}
}
```

### 7. GET /kg/stats
Get comprehensive statistics about the knowledge graph.

**Response:**
```json
{
  "total_triples": 1234,
  "unique_subjects": 567,
  "unique_predicates": 89,
  "unique_objects": 345,
  "children_count": 12,
  "conversations_count": 45,
  "utterances_count": 234,
  "topics_count": 8,
  "emotions_count": 3,
  "last_updated": 1697462400.0
}
```

### 8. GET /kg/export
Export the entire knowledge graph in various formats.

**Parameters:**
- `format`: Export format - "json", "turtle", or "rdf+xml" (default: "json")

**Example:**
```bash
curl "http://localhost:8000/kg/export?format=turtle" -o knowledge_graph.ttl
```

## SHACL Validation

The API includes comprehensive SHACL shapes for data validation:

### Child Shape
- Must have exactly one name (string)
- Age must be between 5 and 13 (integer)
- Language must be "es" or "en"
- Level must be between 1 and 5 (integer)

### Conversation Shape
- Must have exactly one topic (IRI)
- Level must be between 1 and 5 (integer)
- Must have exactly one creation timestamp (dateTime)

### Utterance Shape
- Must have exactly one text (string)
- Can have at most one emotion (IRI)
- Must have exactly one timestamp (dateTime)

### Emotion Shape
- Emotion type must be "positive", "calm", or "neutral"

### Topic Shape
- Must have exactly one name (string)

## Integration with Fuseki Service

The enhanced `fuseki-job` service provides:

### New Methods
- `insert_conversation_data()`: Insert structured conversation data
- `extract_entities_from_text()`: Extract entities using pattern matching

### New CLI Commands
- `--action insert-conversation`: Insert conversation data from JSON file
- `--action extract-entities`: Extract entities from text

### Example Usage

Initialize ontology:
```bash
python services/fuseki-job/main.py --action init
```

Insert conversation data:
```bash
python services/fuseki-job/main.py --action insert-conversation --conversation-file sample_conversation.json
```

Extract entities from text:
```bash
python services/fuseki-job/main.py --action extract-entities --text "Me gusta la escuela" --child-id "test_001"
```

## Testing

A comprehensive test script is provided at `test_kg_api.py`:

```bash
python test_kg_api.py
```

This script tests all API endpoints and provides detailed reporting of success/failure rates.

## Error Handling

All endpoints include proper error handling with appropriate HTTP status codes:

- `400`: Bad Request (invalid SPARQL, unsupported format)
- `500`: Internal Server Error (Fuseki connection issues, validation errors)

Error responses include detailed error messages for debugging.

## OpenAPI Documentation

The API includes comprehensive OpenAPI documentation accessible at:
- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## Configuration

The Knowledge Graph API uses the following configuration settings:

```python
# Fuseki (Knowledge Graph)
fuseki_url: str = "http://localhost:3030"
fuseki_dataset: str = "emorobcare"
```

These can be overridden using environment variables or `.env` file.

## Ontology Structure

The EmoRobCare ontology defines:

### Core Classes
- `emo:Child`: Children participating in conversations
- `emo:Conversation`: Conversation sessions
- `emo:Utterance`: Individual utterances
- `emo:Emotion`: Emotional states
- `emo:Topic`: Conversation topics

### Key Properties
- `emo:hasConversation`: Links children to conversations
- `emo:hasUtterance`: Links conversations to utterances
- `emo:hasEmotion`: Links utterances to emotions
- `emo:hasTopic`: Specifies conversation topic
- `emo:text`: Utterance text content

### Predefined Individuals
- Topics: School, Hobbies, Holidays, Food, Friends, Family, Animals, Sports
- Emotions: Positive, Calm, Neutral

## Performance Considerations

- All queries include execution time metrics
- Automatic LIMIT clauses prevent large result sets
- SHACL validation is optimized for performance
- Background processing for entity extraction

## Security

- SPARQL injection protection through query validation
- Only allowed SPARQL operations on specific endpoints
- Input validation for all parameters
- No PII in logs or error messages

## Future Enhancements

- Advanced NLP-based entity extraction
- Real-time reasoning with incremental updates
- Graph visualization endpoints
- Advanced analytics and reporting
- Integration with external knowledge bases
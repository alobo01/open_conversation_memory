#!/usr/bin/env python3
"""
EmoRobCare Knowledge Graph Service
Manages Fuseki triple store and SHACL validation
"""

import argparse
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

import requests
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, RDFS, XSD, OWL
from pyshacl import validate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class KnowledgeGraphService:
    """Service for managing the knowledge graph with Fuseki and SHACL"""

    def __init__(self, fuseki_url: str, dataset: str):
        self.fuseki_url = fuseki_url.rstrip('/')
        self.dataset = dataset
        self.update_endpoint = f"{self.fuseki_url}/{self.dataset}/update"
        self.query_endpoint = f"{self.fuseki_url}/{self.dataset}/query"
        self.data_endpoint = f"{self.fuseki_url}/{self.dataset}/data"

        # Define namespaces
        self.EMO = Namespace("http://emorobcare.org/ontology#")
        self.EX = Namespace("http://emorobcare.org/example#")

        # Initialize SHACL shapes
        self.shapes_graph = self._load_shacl_shapes()

    def _load_shacl_shapes(self) -> Graph:
        """Load SHACL shapes for validation"""
        shapes_graph = Graph()

        # Define SHACL shapes
        shapes_ttl = """
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix emo: <http://emorobcare.org/ontology#> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

        # Child shape
        emo:ChildShape a sh:NodeShape ;
            sh:targetClass emo:Child ;
            sh:property [
                sh:path emo:name ;
                sh:datatype xsd:string ;
                sh:minCount 1 ;
                sh:maxCount 1 ;
            ] ;
            sh:property [
                sh:path emo:age ;
                sh:datatype xsd:integer ;
                sh:minInclusive 5 ;
                sh:maxInclusive 13 ;
                sh:minCount 1 ;
                sh:maxCount 1 ;
            ] ;
            sh:property [
                sh:path emo:language ;
                sh:datatype xsd:string ;
                sh:in ("es" "en") ;
                sh:minCount 1 ;
                sh:maxCount 1 ;
            ] ;
            sh:property [
                sh:path emo:level ;
                sh:datatype xsd:integer ;
                sh:minInclusive 1 ;
                sh:maxInclusive 5 ;
                sh:minCount 1 ;
                sh:maxCount 1 ;
            ] .

        # Conversation shape
        emo:ConversationShape a sh:NodeShape ;
            sh:targetClass emo:Conversation ;
            sh:property [
                sh:path emo:hasTopic ;
                sh:nodeKind sh:IRI ;
                sh:minCount 1 ;
                sh:maxCount 1 ;
            ] ;
            sh:property [
                sh:path emo:hasLevel ;
                sh:datatype xsd:integer ;
                sh:minInclusive 1 ;
                sh:maxInclusive 5 ;
                sh:minCount 1 ;
                sh:maxCount 1 ;
            ] ;
            sh:property [
                sh:path emo:createdAt ;
                sh:datatype xsd:dateTime ;
                sh:minCount 1 ;
                sh:maxCount 1 ;
            ] .

        # Utterance shape
        emo:UtteranceShape a sh:NodeShape ;
            sh:targetClass emo:Utterance ;
            sh:property [
                sh:path emo:text ;
                sh:datatype xsd:string ;
                sh:minCount 1 ;
                sh:maxCount 1 ;
            ] ;
            sh:property [
                sh:path emo:hasEmotion ;
                sh:nodeKind sh:IRI ;
                sh:minCount 0 ;
                sh:maxCount 1 ;
            ] ;
            sh:property [
                sh:path emo:timestamp ;
                sh:datatype xsd:dateTime ;
                sh:minCount 1 ;
                sh:maxCount 1 ;
            ] .

        # Emotion shape
        emo:EmotionShape a sh:NodeShape ;
            sh:targetClass emo:Emotion ;
            sh:property [
                sh:path emo:emotionType ;
                sh:datatype xsd:string ;
                sh:in ("positive" "calm" "neutral") ;
                sh:minCount 1 ;
                sh:maxCount 1 ;
            ] .

        # Topic shape
        emo:TopicShape a sh:NodeShape ;
            sh:targetClass emo:Topic ;
            sh:property [
                sh:path emo:topicName ;
                sh:datatype xsd:string ;
                sh:minCount 1 ;
                sh:maxCount 1 ;
            ] .
        """

        shapes_graph.parse(data=shapes_ttl, format="turtle")
        return shapes_graph

    def initialize_ontology(self) -> bool:
        """Initialize the ontology in Fuseki"""
        try:
            # Define the ontology
            ontology_ttl = f"""
            @prefix owl: <http://www.w3.org/2002/07/owl#> .
            @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
            @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
            @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
            @prefix emo: <http://emorobcare.org/ontology#> .

            # Ontology declaration
            <http://emorobcare.org/ontology> a owl:Ontology ;
                rdfs:label "EmoRobCare Ontology" ;
                rdfs:comment "Ontology for conversational AI system for children with TEA2" .

            # Classes
            emo:Child a owl:Class ;
                rdfs:label "Child" ;
                rdfs:comment "A child participating in the conversation system" .

            emo:Conversation a owl:Class ;
                rdfs:label "Conversation" ;
                rdfs:comment "A conversation session" .

            emo:Utterance a owl:Class ;
                rdfs:label "Utterance" ;
                rdfs:comment "A single utterance in a conversation" .

            emo:Emotion a owl:Class ;
                rdfs:label "Emotion" ;
                rdfs:comment "Emotional state associated with an utterance" .

            emo:Topic a owl:Class ;
                rdfs:label "Topic" ;
                rdfs:comment "Conversation topic" .

            emo:SkillLevel a owl:Class ;
                rdfs:label "Skill Level" ;
                rdfs:comment "Conversational skill level of a child" .

            # Properties
            emo:name a owl:DatatypeProperty ;
                rdfs:label "name" ;
                rdfs:domain emo:Child ;
                rdfs:range xsd:string .

            emo:age a owl:DatatypeProperty ;
                rdfs:label "age" ;
                rdfs:domain emo:Child ;
                rdfs:range xsd:integer .

            emo:language a owl:DatatypeProperty ;
                rdfs:label "language" ;
                rdfs:domain emo:Child ;
                rdfs:range xsd:string .

            emo:level a owl:DatatypeProperty ;
                rdfs:label "level" ;
                rdfs:domain emo:Child ;
                rdfs:range xsd:integer .

            emo:hasTopic a owl:ObjectProperty ;
                rdfs:label "has topic" ;
                rdfs:domain emo:Conversation ;
                rdfs:range emo:Topic .

            emo:hasLevel a owl:DatatypeProperty ;
                rdfs:label "has level" ;
                rdfs:domain emo:Conversation ;
                rdfs:range xsd:integer .

            emo:hasUtterance a owl:ObjectProperty ;
                rdfs:label "has utterance" ;
                rdfs:domain emo:Conversation ;
                rdfs:range emo:Utterance .

            emo:hasEmotion a owl:ObjectProperty ;
                rdfs:label "has emotion" ;
                rdfs:domain emo:Utterance ;
                rdfs:range emo:Emotion .

            emo:text a owl:DatatypeProperty ;
                rdfs:label "text" ;
                rdfs:domain emo:Utterance ;
                rdfs:range xsd:string .

            emo:timestamp a owl:DatatypeProperty ;
                rdfs:label "timestamp" ;
                rdfs:domain emo:Utterance ;
                rdfs:range xsd:dateTime .

            emo:emotionType a owl:DatatypeProperty ;
                rdfs:label "emotion type" ;
                rdfs:domain emo:Emotion ;
                rdfs:range xsd:string .

            emo:topicName a owl:DatatypeProperty ;
                rdfs:label "topic name" ;
                rdfs:domain emo:Topic ;
                rdfs:range xsd:string .

            emo:createdAt a owl:DatatypeProperty ;
                rdfs:label "created at" ;
                rdfs:domain emo:Conversation ;
                rdfs:range xsd:dateTime .

            # Individuals (Topics)
            emo:SchoolTopic a emo:Topic ;
                rdfs:label "School" ;
                emo:topicName "school" .

            emo:HobbiesTopic a emo:Topic ;
                rdfs:label "Hobbies" ;
                emo:topicName "hobbies" .

            emo:HolidaysTopic a emo:Topic ;
                rdfs:label "Holidays" ;
                emo:topicName "holidays" .

            emo:FoodTopic a emo:Topic ;
                rdfs:label "Food" ;
                emo:topicName "food" .

            emo:FriendsTopic a emo:Topic ;
                rdfs:label "Friends" ;
                emo:topicName "friends" .

            emo:FamilyTopic a emo:Topic ;
                rdfs:label "Family" ;
                emo:topicName "family" .

            emo:AnimalsTopic a emo:Topic ;
                rdfs:label "Animals" ;
                emo:topicName "animals" .

            emo:SportsTopic a emo:Topic ;
                rdfs:label "Sports" ;
                emo:topicName "sports" .

            # Individuals (Emotions)
            emo:PositiveEmotion a emo:Emotion ;
                rdfs:label "Positive" ;
                emo:emotionType "positive" .

            emo:CalmEmotion a emo:Emotion ;
                rdfs:label "Calm" ;
                emo:emotionType "calm" .

            emo:NeutralEmotion a emo:Emotion ;
                rdfs:label "Neutral" ;
                emo:emotionType "neutral" .
            """

            # Upload ontology to Fuseki
            update_query = f"""
            INSERT DATA {{
                {ontology_ttl}
            }}
            """

            response = requests.post(
                self.update_endpoint,
                data={"update": update_query},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            if response.status_code == 200:
                logger.info("Ontology initialized successfully")
                return True
            else:
                logger.error(f"Failed to initialize ontology: {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error initializing ontology: {e}")
            return False

    def insert_triples(self, triples_data: Dict[str, Any]) -> bool:
        """Insert triples into the knowledge graph"""
        try:
            # Convert triples to Turtle format
            turtle_data = self._convert_to_turtle(triples_data)

            update_query = f"""
            INSERT DATA {{
                {turtle_data}
            }}
            """

            response = requests.post(
                self.update_endpoint,
                data={"update": update_query},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            if response.status_code == 200:
                logger.info(f"Inserted {len(triples_data.get('triples', []))} triples")
                return True
            else:
                logger.error(f"Failed to insert triples: {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error inserting triples: {e}")
            return False

    def insert_conversation_data(self, conversation_data: Dict[str, Any]) -> bool:
        """Insert conversation data with proper RDF structure"""
        try:
            child_id = conversation_data.get("child_id")
            conversation_id = conversation_data.get("conversation_id")
            utterances = conversation_data.get("utterances", [])

            if not child_id or not conversation_id:
                logger.error("Missing child_id or conversation_id")
                return False

            # Create RDF triples for conversation
            triples = []

            # Child URI
            child_uri = f"http://emorobcare.org/example#child_{child_id}"

            # Conversation URI
            conv_uri = f"http://emorobcare.org/example#conv_{conversation_id}"

            # Add conversation triples
            triples.extend([
                {
                    "subject": child_uri,
                    "predicate": "http://emorobcare.org/ontology#hasConversation",
                    "object": conv_uri
                },
                {
                    "subject": conv_uri,
                    "predicate": "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
                    "object": "http://emorobcare.org/ontology#Conversation"
                },
                {
                    "subject": conv_uri,
                    "predicate": "http://emorobcare.org/ontology#hasTopic",
                    "object": f"http://emorobcare.org/ontology#{conversation_data.get('topic', 'unknown')}Topic"
                },
                {
                    "subject": conv_uri,
                    "predicate": "http://emorobcare.org/ontology#hasLevel",
                    "object": str(conversation_data.get("level", 3))
                },
                {
                    "subject": conv_uri,
                    "predicate": "http://emorobcare.org/ontology#createdAt",
                    "object": conversation_data.get("timestamp", datetime.now().isoformat())
                }
            ])

            # Add utterance triples
            for i, utterance in enumerate(utterances):
                utterance_uri = f"http://emorobcare.org/example#utterance_{conversation_id}_{i}"

                triples.extend([
                    {
                        "subject": conv_uri,
                        "predicate": "http://emorobcare.org/ontology#hasUtterance",
                        "object": utterance_uri
                    },
                    {
                        "subject": utterance_uri,
                        "predicate": "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
                        "object": "http://emorobcare.org/ontology#Utterance"
                    },
                    {
                        "subject": utterance_uri,
                        "predicate": "http://emorobcare.org/ontology#text",
                        "object": utterance.get("text", "")
                    },
                    {
                        "subject": utterance_uri,
                        "predicate": "http://emorobcare.org/ontology#timestamp",
                        "object": utterance.get("timestamp", datetime.now().isoformat())
                    }
                ])

                # Add emotion if present
                if utterance.get("emotion"):
                    emotion_uri = f"http://emorobcare.org/example#emotion_{conversation_id}_{i}"
                    triples.extend([
                        {
                            "subject": utterance_uri,
                            "predicate": "http://emorobcare.org/ontology#hasEmotion",
                            "object": emotion_uri
                        },
                        {
                            "subject": emotion_uri,
                            "predicate": "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
                            "object": "http://emorobcare.org/ontology#Emotion"
                        },
                        {
                            "subject": emotion_uri,
                            "predicate": "http://emorobcare.org/ontology#emotionType",
                            "object": utterance.get("emotion")
                        }
                    ])

            # Insert all triples
            return self.insert_triples({"triples": triples})

        except Exception as e:
            logger.error(f"Error inserting conversation data: {e}")
            return False

    def extract_entities_from_text(self, text: str, child_id: str) -> Dict[str, Any]:
        """Extract entities and relationships from text using basic patterns"""
        try:
            entities = {
                "persons": [],
                "places": [],
                "activities": [],
                "emotions": [],
                "relationships": []
            }

            # Simple pattern-based extraction (could be enhanced with NLP)
            import re

            # Extract names (simple pattern)
            names = re.findall(r'\b([A-Z][a-z]+)\b', text)
            entities["persons"] = list(set(names))

            # Extract common places
            places_patterns = ['escuela', 'casa', 'parque', 'playa', 'cine', 'restaurante']
            for place in places_patterns:
                if place in text.lower():
                    entities["places"].append(place)

            # Extract activities
            activities_patterns = ['jugar', 'comer', 'estudiar', 'dormir', 'correr', 'leer']
            for activity in activities_patterns:
                if activity in text.lower():
                    entities["activities"].append(activity)

            # Extract emotions
            emotion_patterns = ['feliz', 'triste', 'enojado', 'contento', 'cansado', 'emocionado']
            for emotion in emotion_patterns:
                if emotion in text.lower():
                    entities["emotions"].append(emotion)

            # Generate RDF triples for extracted entities
            triples = []
            child_uri = f"http://emorobcare.org/example#child_{child_id}"

            # Add entity triples
            for entity_type, entity_list in entities.items():
                for entity in entity_list:
                    entity_uri = f"http://emorobcare.org/example#entity_{child_id}_{entity.lower().replace(' ', '_')}"

                    triples.extend([
                        {
                            "subject": child_uri,
                            "predicate": f"http://emorobcare.org/ontology#has{entity_type.capitalize()}",
                            "object": entity_uri
                        },
                        {
                            "subject": entity_uri,
                            "predicate": "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
                            "object": f"http://emorobcare.org/ontology#{entity_type.capitalize()}"
                        },
                        {
                            "subject": entity_uri,
                            "predicate": "http://www.w3.org/2000/01/rdf-schema#label",
                            "object": entity
                        }
                    ])

            return {
                "entities": entities,
                "triples": triples
            }

        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return {"entities": {}, "triples": []}

    def query_knowledge_graph(self, sparql_query: str) -> List[Dict[str, Any]]:
        """Execute SPARQL query against the knowledge graph"""
        try:
            response = requests.post(
                self.query_endpoint,
                data={"query": sparql_query},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            if response.status_code == 200:
                results = response.json()
                return results.get("results", {}).get("bindings", [])
            else:
                logger.error(f"Query failed: {response.text}")
                return []

        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return []

    def validate_consistency(self) -> Dict[str, Any]:
        """Validate knowledge graph consistency using SHACL"""
        try:
            # Get current data
            data_graph = self._get_data_graph()

            # Perform validation
            conforms, results_graph, results_text = validate(
                data_graph=data_graph,
                shacl_graph=self.shapes_graph,
                ont_graph=None,
                inference="rdfs",
                abort_on_first=False,
                allow_infos=False,
                allow_warnings=False,
                meta_shacl=False,
                debug=False
            )

            violations = []
            if not conforms:
                violations = self._parse_validation_results(results_text)

            return {
                "consistent": conforms,
                "violations": violations,
                "validation_time": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error validating consistency: {e}")
            return {
                "consistent": False,
                "violations": [{"error": str(e)}],
                "validation_time": datetime.now().isoformat()
            }

    def _convert_to_turtle(self, triples_data: Dict[str, Any]) -> str:
        """Convert triples data to Turtle format"""
        turtle_statements = []

        for triple in triples_data.get("triples", []):
            subject = triple.get("subject")
            predicate = triple.get("predicate")
            obj = triple.get("object")

            if subject and predicate and obj:
                # Handle different object types
                if obj.startswith("http"):
                    obj_iri = f"<{obj}>"
                else:
                    obj_iri = f'"{obj}"'

                turtle_statements.append(f"<{subject}> <{predicate}> {obj_iri} .")

        return "\n".join(turtle_statements)

    def _get_data_graph(self) -> Graph:
        """Get the current data graph from Fuseki"""
        try:
            # Get all triples
            query = "CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }"

            response = requests.post(
                self.query_endpoint,
                data={"query": query},
                headers={"Accept": "text/turtle", "Content-Type": "application/x-www-form-urlencoded"}
            )

            if response.status_code == 200:
                data_graph = Graph()
                data_graph.parse(data=response.text, format="turtle")
                return data_graph
            else:
                logger.error(f"Failed to get data graph: {response.text}")
                return Graph()

        except Exception as e:
            logger.error(f"Error getting data graph: {e}")
            return Graph()

    def _parse_validation_results(self, results_text: str) -> List[Dict[str, Any]]:
        """Parse SHACL validation results"""
        violations = []

        # Simple parsing of validation results
        lines = results_text.split('\n')
        for line in lines:
            if 'Violation' in line or 'Error' in line:
                violations.append({
                    "type": "constraint_violation",
                    "message": line.strip()
                })

        return violations

    def get_statistics(self) -> Dict[str, Any]:
        """Get knowledge graph statistics"""
        try:
            stats = {}

            # Count triples
            count_query = "SELECT (COUNT(*) as ?count) WHERE { ?s ?p ?o }"
            results = self.query_knowledge_graph(count_query)
            if results:
                stats["total_triples"] = int(results[0]["count"]["value"])

            # Count individuals by class
            class_queries = {
                "children": "SELECT (COUNT(DISTINCT ?s) as ?count) WHERE { ?s a emo:Child }",
                "conversations": "SELECT (COUNT(DISTINCT ?s) as ?count) WHERE { ?s a emo:Conversation }",
                "utterances": "SELECT (COUNT(DISTINCT ?s) as ?count) WHERE { ?s a emo:Utterance }",
                "topics": "SELECT (COUNT(DISTINCT ?s) as ?count) WHERE { ?s a emo:Topic }",
                "emotions": "SELECT (COUNT(DISTINCT ?s) as ?count) WHERE { ?s a emo:Emotion }"
            }

            for entity_type, query in class_queries.items():
                results = self.query_knowledge_graph(query)
                if results:
                    stats[f"{entity_type}_count"] = int(results[0]["count"]["value"])

            stats["last_updated"] = datetime.now().isoformat()

            return stats

        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {"error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="EmoRobCare Knowledge Graph Service")
    parser.add_argument(
        "--action",
        choices=["init", "insert", "validate", "stats", "insert-conversation", "extract-entities"],
        required=True,
        help="Action to perform"
    )
    parser.add_argument(
        "--fuseki-url",
        default="http://localhost:3030",
        help="Fuseki server URL"
    )
    parser.add_argument(
        "--dataset",
        default="emorobcare",
        help="Fuseki dataset name"
    )
    parser.add_argument(
        "--data-file",
        help="JSON file with data to insert"
    )
    parser.add_argument(
        "--conversation-file",
        help="JSON file with conversation data to insert"
    )
    parser.add_argument(
        "--text",
        help="Text to extract entities from"
    )
    parser.add_argument(
        "--child-id",
        help="Child ID for entity extraction"
    )

    args = parser.parse_args()

    # Initialize service
    kg_service = KnowledgeGraphService(args.fuseki_url, args.dataset)

    # Execute action
    if args.action == "init":
        success = kg_service.initialize_ontology()
        print(f"Ontology initialization: {'SUCCESS' if success else 'FAILED'}")

    elif args.action == "insert":
        if not args.data_file:
            print("Error: --data-file required for insert action")
            return

        with open(args.data_file, 'r') as f:
            data = json.load(f)

        success = kg_service.insert_triples(data)
        print(f"Data insertion: {'SUCCESS' if success else 'FAILED'}")

    elif args.action == "insert-conversation":
        if not args.conversation_file:
            print("Error: --conversation-file required for insert-conversation action")
            return

        with open(args.conversation_file, 'r') as f:
            data = json.load(f)

        success = kg_service.insert_conversation_data(data)
        print(f"Conversation data insertion: {'SUCCESS' if success else 'FAILED'}")

    elif args.action == "extract-entities":
        if not args.text or not args.child_id:
            print("Error: --text and --child-id required for extract-entities action")
            return

        result = kg_service.extract_entities_from_text(args.text, args.child_id)
        print(f"Extracted entities: {json.dumps(result['entities'], indent=2, ensure_ascii=False)}")
        if result['triples']:
            print(f"Generated {len(result['triples'])} RDF triples")
            success = kg_service.insert_triples({"triples": result['triples']})
            print(f"Entity insertion: {'SUCCESS' if success else 'FAILED'}")

    elif args.action == "validate":
        results = kg_service.validate_consistency()
        print(f"Consistency validation: {'CONSISTENT' if results['consistent'] else 'INCONSISTENT'}")
        if results['violations']:
            print("Violations:")
            for violation in results['violations']:
                print(f"  - {violation}")

    elif args.action == "stats":
        stats = kg_service.get_statistics()
        print("Knowledge Graph Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
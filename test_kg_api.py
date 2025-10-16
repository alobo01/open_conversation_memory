#!/usr/bin/env python3
"""
Test script for EmoRobCare Knowledge Graph API endpoints
"""

import requests
import json
import time
from typing import Dict, Any

# API base URL
BASE_URL = "http://localhost:8000"

def test_endpoint(endpoint: str, method: str = "GET", data: Dict[str, Any] = None, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Test an API endpoint"""
    url = f"{BASE_URL}{endpoint}"

    try:
        if method == "GET":
            response = requests.get(url, params=params)
        elif method == "POST":
            response = requests.post(url, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")

        return {
            "status_code": response.status_code,
            "success": response.status_code < 400,
            "data": response.json() if response.content else None,
            "endpoint": endpoint,
            "method": method
        }
    except Exception as e:
        return {
            "status_code": 0,
            "success": False,
            "error": str(e),
            "endpoint": endpoint,
            "method": method
        }

def test_knowledge_graph_api():
    """Test all Knowledge Graph API endpoints"""
    print("🧪 Testing EmoRobCare Knowledge Graph API")
    print("=" * 50)

    results = []

    # Test 1: Get knowledge graph statistics
    print("\n1️⃣ Testing GET /kg/stats")
    result = test_endpoint("/kg/stats")
    results.append(result)
    print(f"   Status: {result['status_code']} - {'✅ Success' if result['success'] else '❌ Failed'}")
    if result['success'] and result['data']:
        stats = result['data']
        print(f"   Total triples: {stats.get('total_triples', 'N/A')}")
        print(f"   Children count: {stats.get('children_count', 'N/A')}")
        print(f"   Conversations count: {stats.get('conversations_count', 'N/A')}")

    # Test 2: Get knowledge graph schema
    print("\n2️⃣ Testing GET /kg/schema")
    result = test_endpoint("/kg/schema")
    results.append(result)
    print(f"   Status: {result['status_code']} - {'✅ Success' if result['success'] else '❌ Failed'}")
    if result['success'] and result['data']:
        schema = result['data']
        print(f"   Classes: {len(schema.get('classes', []))}")
        print(f"   Properties: {len(schema.get('properties', []))}")
        print(f"   Individuals: {len(schema.get('individuals', []))}")

    # Test 3: Test SPARQL query endpoint
    print("\n3️⃣ Testing GET /kg/query")
    query = """
    SELECT ?class ?label WHERE {
        ?class a owl:Class .
        OPTIONAL { ?class rdfs:label ?label . }
        FILTER (strstarts(str(?class), "http://emorobcare.org/ontology"))
    }
    LIMIT 5
    """
    result = test_endpoint("/kg/query", params={"query": query})
    results.append(result)
    print(f"   Status: {result['status_code']} - {'✅ Success' if result['success'] else '❌ Failed'}")
    if result['success'] and result['data']:
        query_results = result['data'].get('results', [])
        print(f"   Query results: {len(query_results)} rows")
        if query_results:
            print(f"   First result: {query_results[0]}")

    # Test 4: Test SHACL validation
    print("\n4️⃣ Testing GET /kg/validate")
    result = test_endpoint("/kg/validate")
    results.append(result)
    print(f"   Status: {result['status_code']} - {'✅ Success' if result['success'] else '❌ Failed'}")
    if result['success'] and result['data']:
        validation = result['data']
        print(f"   Conforms: {validation.get('conforms', 'Unknown')}")
        print(f"   Violations: {len(validation.get('violations', []))}")
        print(f"   Validation time: {validation.get('validation_time', 0):.3f}s")

    # Test 5: Test OWL reasoning
    print("\n5️⃣ Testing GET /kg/reason")
    result = test_endpoint("/kg/reason")
    results.append(result)
    print(f"   Status: {result['status_code']} - {'✅ Success' if result['success'] else '❌ Failed'}")
    if result['success'] and result['data']:
        reasoning = result['data']
        print(f"   Consistent: {reasoning.get('consistent', 'Unknown')}")
        print(f"   Violations: {len(reasoning.get('violations', []))}")
        print(f"   Reasoning time: {reasoning.get('reasoning_time', 0):.3f}s")

    # Test 6: Test insert endpoint (INSERT DATA)
    print("\n6️⃣ Testing POST /kg/insert")
    insert_data = {
        "sparql_update": """
        PREFIX emo: <http://emorobcare.org/ontology#>
        PREFIX ex: <http://emorobcare.org/example#>

        INSERT DATA {
            ex:test_child_001 a emo:Child ;
                emo:name "Test Child" ;
                emo:age 8 ;
                emo:language "es" ;
                emo:level 3 .
        }
        """
    }
    result = test_endpoint("/kg/insert", method="POST", data=insert_data)
    results.append(result)
    print(f"   Status: {result['status_code']} - {'✅ Success' if result['success'] else '❌ Failed'}")
    if result['success'] and result['data']:
        print(f"   Insert time: {result['data'].get('execution_time', 0):.3f}s")
        print(f"   Message: {result['data'].get('message', 'No message')}")

    # Test 7: Test update endpoint (DELETE/INSERT)
    print("\n7️⃣ Testing POST /kg/update")
    update_data = {
        "sparql_update": """
        PREFIX emo: <http://emorobcare.org/ontology#>
        PREFIX ex: <http://emorobcare.org/example#>

        DELETE WHERE {
            ex:test_child_001 emo:level ?old_level .
        } ;
        INSERT WHERE {
            ex:test_child_001 emo:level 4 .
        }
        """
    }
    result = test_endpoint("/kg/update", method="POST", data=update_data)
    results.append(result)
    print(f"   Status: {result['status_code']} - {'✅ Success' if result['success'] else '❌ Failed'}")
    if result['success'] and result['data']:
        print(f"   Update time: {result['data'].get('execution_time', 0):.3f}s")
        print(f"   Message: {result['data'].get('message', 'No message')}")

    # Test 8: Test export endpoint
    print("\n8️⃣ Testing GET /kg/export")
    result = test_endpoint("/kg/export", params={"format": "json"})
    results.append(result)
    print(f"   Status: {result['status_code']} - {'✅ Success' if result['success'] else '❌ Failed'}")
    if result['success'] and result['data']:
        export_data = result['data']
        bindings = export_data.get('results', {}).get('bindings', [])
        print(f"   Exported triples: {len(bindings)}")

    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)

    total_tests = len(results)
    successful_tests = sum(1 for r in results if r['success'])
    failed_tests = total_tests - successful_tests

    print(f"Total tests: {total_tests}")
    print(f"Successful: {successful_tests} ✅")
    print(f"Failed: {failed_tests} ❌")
    print(f"Success rate: {(successful_tests/total_tests)*100:.1f}%")

    if failed_tests > 0:
        print("\n❌ Failed tests:")
        for result in results:
            if not result['success']:
                print(f"   - {result['method']} {result['endpoint']}: {result.get('error', 'Unknown error')}")

    return results

def test_api_docs():
    """Test API documentation endpoint"""
    print("\n📚 Testing API Documentation")

    # Test OpenAPI docs
    docs_result = test_endpoint("/docs")
    print(f"   OpenAPI docs: {docs_result['status_code']} - {'✅ Available' if docs_result['success'] else '❌ Not available'}")

    # Test OpenAPI JSON
    json_result = test_endpoint("/openapi.json")
    print(f"   OpenAPI JSON: {json_result['status_code']} - {'✅ Available' if json_result['success'] else '❌ Not available'}")

    if json_result['success'] and json_result['data']:
        openapi_spec = json_result['data']
        kg_paths = [path for path in openapi_spec.get('paths', {}).keys() if '/kg' in path]
        print(f"   KG endpoints documented: {len(kg_paths)}")
        for path in kg_paths:
            print(f"     - {path}")

if __name__ == "__main__":
    print("🚀 Starting EmoRobCare Knowledge Graph API Tests")
    print("Make sure the API server is running on http://localhost:8000")
    print("And Fuseki is running on http://localhost:3030")
    print()

    # Wait a moment for user to read
    time.sleep(2)

    # Run tests
    test_results = test_knowledge_graph_api()
    test_api_docs()

    print("\n🏁 Testing completed!")
#!/bin/bash

# EmoRobCare Test Script
# Runs tests for all services

set -e

echo "🧪 Running EmoRobCare tests..."

# Function to test API endpoints
test_api() {
    echo "🔍 Testing API endpoints..."

    # Test health endpoint
    echo "  - Testing /health endpoint..."
    curl -sf http://localhost:8000/health > /dev/null || {
        echo "❌ API health check failed"
        return 1
    }

    # Test conversation start
    echo "  - Testing conversation start..."
    response=$(curl -s -X POST http://localhost:8000/conv/start \
        -H "Content-Type: application/json" \
        -d '{"child": "test_child", "topic": "school", "level": 3}')

    if [[ $response == *"conversation_id"* ]]; then
        echo "✅ Conversation start test passed"
    else
        echo "❌ Conversation start test failed"
        echo "Response: $response"
        return 1
    fi

    # Test knowledge graph
    echo "  - Testing knowledge graph..."
    kg_response=$(curl -s -X POST http://localhost:8000/kg/retrieve \
        -H "Content-Type: application/json" \
        -d '{"sparql_select": "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10"}')

    if [[ $kg_response == *"results"* ]]; then
        echo "✅ Knowledge graph test passed"
    else
        echo "❌ Knowledge graph test failed"
        echo "Response: $kg_response"
        return 1
    fi

    return 0
}

# Function to test ASR
test_asr() {
    echo "🔍 Testing ASR service..."

    # Test health endpoint
    curl -sf http://localhost:8001/health > /dev/null || {
        echo "❌ ASR health check failed"
        return 1
    }

    # Test transcription (mock)
    echo "  - Testing mock transcription..."
    asr_response=$(curl -s -X POST "http://localhost:8001/test?text=hola%20mundo&tier=balanced&language=es")

    if [[ $asr_response == *"hola mundo"* ]]; then
        echo "✅ ASR test passed"
    else
        echo "❌ ASR test failed"
        echo "Response: $asr_response"
        return 1
    fi

    return 0
}

# Function to test frontend
test_frontend() {
    echo "🔍 Testing frontend..."

    # Test health endpoint
    curl -sf http://localhost:81/health > /dev/null || {
        echo "❌ Frontend health check failed"
        return 1
    }

    # Test main page loads
    echo "  - Testing main page..."
    curl -sf http://localhost:81 > /dev/null || {
        echo "❌ Frontend page load failed"
        return 1
    }

    echo "✅ Frontend test passed"
    return 0
}

# Function to test databases
test_databases() {
    echo "🔍 Testing databases..."

    # Test MongoDB
    echo "  - Testing MongoDB..."
    docker exec emorobcare-mongodb mongosh --eval "db.runCommand('ping')" > /dev/null || {
        echo "❌ MongoDB connection failed"
        return 1
    }

    # Test Qdrant
    echo "  - Testing Qdrant..."
    curl -sf http://localhost:6333/health > /dev/null || {
        echo "❌ Qdrant connection failed"
        return 1
    }

    # Test Fuseki
    echo "  - Testing Fuseki..."
    curl -sf http://localhost:3030/$$/stats > /dev/null || {
        echo "❌ Fuseki connection failed"
        return 1
    }

    echo "✅ Database tests passed"
    return 0
}

# Function to run integration tests
run_integration_tests() {
    echo "🔍 Running integration tests..."

    # Test full conversation flow
    echo "  - Testing conversation flow..."

    # Start conversation
    start_response=$(curl -s -X POST http://localhost:8000/conv/start \
        -H "Content-Type: application/json" \
        -d '{"child": "integration_test_child", "topic": "hobbies", "level": 3}')

    conversation_id=$(echo $start_response | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data.get('conversation_id', ''))
")

    if [[ -z "$conversation_id" ]]; then
        echo "❌ Failed to start conversation"
        return 1
    fi

    # Send a message
    message_response=$(curl -s -X POST http://localhost:8000/conv/next \
        -H "Content-Type: application/json" \
        -d "{\"conversation_id\": \"$conversation_id\", \"user_sentence\": \"Me gusta jugar con legos\", \"end\": false}")

    if [[ $message_response == *"reply"* ]]; then
        echo "✅ Integration test passed"
    else
        echo "❌ Integration test failed"
        echo "Response: $message_response"
        return 1
    fi

    return 0
}

# Main test execution
main() {
    echo "Starting comprehensive tests..."
    echo "================================"

    failed_tests=0

    # Test databases first
    if ! test_databases; then
        ((failed_tests++))
    fi
    echo ""

    # Test individual services
    if ! test_api; then
        ((failed_tests++))
    fi
    echo ""

    if ! test_asr; then
        ((failed_tests++))
    fi
    echo ""

    if ! test_frontend; then
        ((failed_tests++))
    fi
    echo ""

    # Run integration tests
    if ! run_integration_tests; then
        ((failed_tests++))
    fi
    echo ""

    # Summary
    echo "================================"
    if [ $failed_tests -eq 0 ]; then
        echo "🎉 All tests passed successfully!"
        echo "✅ EmoRobCare is ready for use"
    else
        echo "❌ $failed_tests test(s) failed"
        echo "🔧 Please check the logs and fix the issues"
        exit 1
    fi
}

# Check if services are running
if ! curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ Services are not running. Please start them first with:"
    echo "   make deploy-docker"
    exit 1
fi

main "$@"
#!/bin/bash

# EmoRobCare Deployment Script
# Deploys the application using Docker Compose

set -e

echo "🚀 Deploying EmoRobCare with Docker..."

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Clean up any existing containers
echo "🧹 Cleaning up existing containers..."
docker-compose down --remove-orphans || true

# Build and start services
echo "🏗️ Building and starting services..."
docker-compose up --build -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 30

# Check service health
echo "🔍 Checking service health..."

check_health() {
    local service_name=$1
    local health_url=$2
    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -sf "$health_url" > /dev/null 2>&1; then
            echo "✅ $service_name is healthy"
            return 0
        fi

        echo "⏳ Waiting for $service_name... (attempt $attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done

    echo "❌ $service_name failed to become healthy"
    return 1
}

# Check each service
check_health "MongoDB" "http://localhost:27017"
check_health "Qdrant" "http://localhost:6333/health"
check_health "Fuseki" "http://localhost:3030/$$/stats"
check_health "API" "http://localhost:8000/health"
check_health "ASR" "http://localhost:8001/health"
check_health "Frontend" "http://localhost:81/health"

# Initialize knowledge graph
echo "🧠 Initializing knowledge graph..."
docker-compose run --rm fuseki-job --action init

echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "🌐 Access the application:"
echo "- Frontend: http://localhost:81"
echo "- API: http://localhost:8000"
echo "- API Docs: http://localhost:8000/docs"
echo "- ASR: http://localhost:8001"
echo "- Qdrant: http://localhost:6333"
echo "- Fuseki: http://localhost:3030"
echo ""
echo "📊 Useful commands:"
echo "- make logs: Show logs"
echo "- make stop: Stop all services"
echo "- make restart: Restart all services"
echo "- make status: Check service status"
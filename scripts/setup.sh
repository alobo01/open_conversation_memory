#!/bin/bash

# EmoRobCare Setup Script
# Sets up the development environment

set -e

echo "🚀 Setting up EmoRobCare development environment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create virtual environment for API
echo "📦 Creating Python virtual environment for API..."
cd services/api
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cd ../..

# Create virtual environment for ASR
echo "📦 Creating Python virtual environment for ASR..."
cd services/asr
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cd ../..

# Create virtual environment for Fuseki job
echo "📦 Creating Python virtual environment for Fuseki job..."
cd services/fuseki-job
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cd ../..

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd services/frontend
npm install
cd ../..

# Create .env files if they don't exist
echo "📝 Creating environment files..."
if [ ! -f services/api/.env ]; then
    cat > services/api/.env << EOF
MONGODB_URI=mongodb://localhost:27017
QDRANT_URL=http://localhost:6333
FUSEKI_URL=http://localhost:3030
OFFLINE_MODE=true
DEFAULT_LANG=es
ASR_GPU=false
LOG_LEVEL=INFO
EOF
fi

if [ ! -f services/asr/.env ]; then
    cat > services/asr/.env << EOF
DEFAULT_LANGUAGE=es
GPU_ENABLED=false
LOG_LEVEL=INFO
EOF
fi

if [ ! -f services/frontend/.env ]; then
    cat > services/frontend/.env << EOF
VITE_API_URL=http://localhost:8000
VITE_ASR_URL=http://localhost:8001
EOF
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs
mkdir -p data/mongodb
mkdir -p data/qdrant
mkdir -p data/fuseki
mkdir -p backups

# Set permissions
echo "🔐 Setting permissions..."
chmod +x scripts/*.sh
chmod -R 755 services/

echo "✅ Setup completed successfully!"
echo ""
echo "🎯 Next steps:"
echo "1. Start the services: make dev"
echo "2. Or run with Docker: make deploy-docker"
echo "3. Open your browser to http://localhost:81"
echo ""
echo "📚 Useful commands:"
echo "- make dev: Start in development mode"
echo "- make deploy-docker: Start with Docker"
echo "- make stop: Stop all services"
echo "- make logs: Show logs"
echo "- make test: Run tests"
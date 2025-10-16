# 🐳 Docker & Deployment Epic (DOCKER)

## Overview
Optimize Docker images for production deployment, create deployment automation scripts, and ensure complete offline functionality for the EmoRobCare system.

## Tasks

### DOCKER-001: Dockerfiles multi-stage ⏳ **MEDIUM PRIORITY**
**Status**: Basic Dockerfiles exist
**Estimated**: 16 hours
**Files to optimize**:
- `services/api/Dockerfile` (optimize)
- `services/asr/Dockerfile` (optimize)
- `services/frontend/Dockerfile` (optimize)
- `services/fuseki-job/Dockerfile` (optimize)

#### Subtasks:
- [ ] **Multi-stage Build Optimization**: Implement multi-stage builds for all services
- [ ] **Base Image Optimization**: Use minimal base images (alpine/python-slim)
- [ ] **Layer Caching**: Optimize Docker layer order for better caching
- [ ] **Size Reduction**: Target < 500MB per service image
- [ ] **Security Hardening**: Remove unnecessary packages and users
- [ ] **Model Pre-loading**: Download models during build for offline deployment
- [ ] **Build Args**: Use build arguments for version and configuration management
- [ ] **Health Check Implementation**: Add comprehensive health checks

#### Implementation Details:
```dockerfile
# services/api/Dockerfile - Optimized Multi-stage
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

FROM base as builder
WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM base as runtime
WORKDIR /app

# Create non-root user
RUN useradd --create-home --shell /bin/bash emorobcare

# Copy installed packages from builder
COPY --from=builder /root/.local /home/emorobcare/.local

# Copy application code
COPY --chown=emorobcare:emorobcare . .

# Download models during build
RUN python -c "from services.api.models import download_models; download_models()" \
    && rm -rf /home/emorobcare/.cache/pip

# Set permissions
USER emorobcare
ENV PATH=/home/emorobcare/.local/bin:$PATH

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Acceptance Criteria:
- [ ] All service images < 500MB after optimization
- [ ] Multi-stage builds reduce final image size by >30%
- [ ] Models downloaded during build for offline capability
- [ ] Health checks pass for all services
- [ ] Security scan passes (no critical vulnerabilities)

---

### DOCKER-002: Build y run scripts ⏳ **MEDIUM PRIORITY**
**Status**: Basic Makefile exists
**Estimated**: 12 hours
**Files to implement**:
- `scripts/build.sh` (new)
- `scripts/deploy.sh` (new)
- `scripts/stop.sh` (enhance)
- `scripts/backup.sh` (new)
- `scripts/monitor.sh` (new)
- `docker-compose.prod.yml` (new)

#### Subtasks:
- [ ] **Automated Build Script**: Script to build all images with proper tagging
- [ ] **Deployment Automation**: Script to deploy services with proper startup order
- [ ] **Environment Management**: Support for development/staging/production environments
- [ ] **Service Dependencies**: Handle service startup dependencies gracefully
- [ ] **Health Monitoring**: Script to monitor service health and status
- [ ] **Backup Management**: Automated backup of databases and configurations
- [ ] **Log Management**: Centralized log collection and rotation
- [ ] **Error Recovery**: Automatic restart and recovery mechanisms

#### Implementation Details:
```bash
#!/bin/bash
# scripts/deploy.sh - Deployment Automation

set -e

# Configuration
ENVIRONMENT=${1:-production}
COMPOSE_FILE="docker-compose.${ENVIRONMENT}.yml"
PROJECT_NAME="emorobcare"

echo "Deploying EmoRobCare to ${ENVIRONMENT}..."

# Pre-deployment checks
echo "Running pre-deployment checks..."
python scripts/pre_deploy_checks.py

# Build images if needed
if [ "$ENVIRONMENT" = "production" ]; then
    echo "Building production images..."
    docker-compose -f $COMPOSE_FILE build --no-cache
fi

# Stop existing services
echo "Stopping existing services..."
docker-compose -f $COMPOSE_FILE down

# Deploy services in dependency order
echo "Deploying services..."
docker-compose -f $COMPOSE_FILE up -d mongodb qdrant fuseki
echo "Waiting for databases to be ready..."
sleep 30

docker-compose -f $COMPOSE_FILE up -d api asr
echo "Waiting for API services to be ready..."
sleep 20

docker-compose -f $COMPOSE_FILE up -d frontend

# Post-deployment verification
echo "Running post-deployment verification..."
python scripts/post_deploy_checks.py

echo "Deployment completed successfully!"
echo "Application available at: http://localhost:81"
```

#### Acceptance Criteria:
- [ ] Single command deploys entire system (`make deploy`)
- [ ] Scripts handle all deployment scenarios correctly
- [ ] Service startup order respects dependencies
- [ ] Health checks prevent deployment of unhealthy services
- [ ] Backup and recovery procedures work correctly

---

### DOCKER-003: Optimización offline ⏳ **HIGH PRIORITY**
**Status**: Partially implemented
**Estimated**: 20 hours
**Files to implement**:
- `scripts/download_models.py` (new)
- `models/model_manifest.json` (new)
- `config/offline_config.py` (new)
- `docker-compose.offline.yml` (new)

#### Subtasks:
- [ ] **Model Download Script**: Automated download of all required models
- [ ] **Model Verification**: Verify model integrity with checksums
- [ ] **Offline Configuration**: Configuration for complete offline operation
- [ ] **Package Caching**: Cache Python packages and system dependencies
- [ ] **Network Isolation**: Ensure zero external dependencies at runtime
- [ ] **Fallback Mechanisms**: Graceful handling of missing components
- [ ] **Resource Optimization**: Optimize for environments with limited resources
- [ ] **Update Mechanism**: Secure way to update models and components

#### Implementation Details:
```python
# scripts/download_models.py
import os
import hashlib
import requests
from pathlib import Path

MODEL_MANIFEST = {
    "qwen2-7b-instruct": {
        "url": "https://huggingface.co/Qwen/Qwen2-7B-Instruct/resolve/main/pytorch_model.bin",
        "checksum": "sha256:...",
        "size": "14GB",
        "required": True
    },
    "whisper-large-v3": {
        "url": "https://huggingface.co/openai/whisper-large-v3/resolve/main/pytorch_model.bin",
        "checksum": "sha256:...",
        "size": "3GB",
        "required": True
    },
    "sentence-transformers": {
        "url": "https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2/resolve/main/pytorch_model.bin",
        "checksum": "sha256:...",
        "size": "400MB",
        "required": True
    }
}

def download_with_verification(model_name, model_info):
    """Download model with checksum verification"""
    model_path = Path(f"models/{model_name}")
    model_path.mkdir(parents=True, exist_ok=True)

    if model_path.exists():
        print(f"Model {model_name} already exists, verifying...")
        if verify_model(model_path, model_info['checksum']):
            print(f"Model {model_name} verified successfully")
            return
        else:
            print(f"Model {model_name} verification failed, re-downloading...")

    print(f"Downloading {model_name} ({model_info['size']})...")
    # Download implementation with progress bar
    # Verify checksum after download

def prepare_offline_environment():
    """Prepare complete offline environment"""
    # Download all models
    # Cache Python packages
    # Download system dependencies
    # Create offline Docker compose file
```

#### Acceptance Criteria:
- [ ] All models downloaded and verified during build
- [ ] System runs completely offline after deployment
- [ ] Model integrity verified with checksums
- [ ] Update mechanism works securely
- [ ] Resource usage optimized for target hardware

---

## Production Infrastructure

### Docker Compose Configurations
- [ ] **Development Configuration**: Hot reload, debugging enabled
- [ ] **Staging Configuration**: Production-like setup for testing
- [ ] **Production Configuration**: Optimized for performance and security
- [ ] **Offline Configuration**: Complete offline deployment setup

### Monitoring & Logging
- [ ] **Service Health Monitoring**: Comprehensive health checks
- [ ] **Log Aggregation**: Centralized log collection
- [ ] **Performance Monitoring**: Resource usage tracking
- [ ] **Error Tracking**: Automated error alerting

### Security Hardening
- [ ] **Container Security**: Minimal base images, non-root users
- [ ] **Network Isolation**: Proper network segmentation
- [ ] **Secret Management**: Secure handling of sensitive data
- [ ] **Vulnerability Scanning**: Regular security scans

---

## Deployment Strategies

### Development Deployment
- [ ] **Hot Reload**: Code changes automatically reflected
- [ ] **Debugging**: Debug ports and tools available
- [ ] **Testing**: Easy testing and validation setup
- [ ] **Data Persistence**: Local data persistence for development

### Staging Deployment
- [ ] **Production Parity**: Close to production configuration
- [ ] **Automated Testing**: Integration and E2E test execution
- [ ] **Performance Testing**: Load and performance validation
- [ ] **Security Testing**: Security vulnerability scanning

### Production Deployment
- [ ] **Zero Downtime**: Rolling updates without service interruption
- [ ] **Health Checks**: Comprehensive health validation
- [ ] **Monitoring**: Full monitoring and alerting setup
- [ ] **Backup**: Automated backup and recovery procedures

---

## Success Metrics

### Image Optimization Metrics
- [ ] **Image Size**: < 500MB per service image
- [ ] **Build Time**: < 10 minutes for full build
- [ ] **Security Score**: No critical vulnerabilities
- [ ] **Startup Time**: < 30 seconds for full system startup

### Deployment Metrics
- [ ] **Deployment Success Rate**: > 99% successful deployments
- [ ] **Deployment Time**: < 5 minutes for complete deployment
- [ ] **Recovery Time**: < 2 minutes for service recovery
- [ ] **Downtime**: < 1 minute per month

### Offline Capability Metrics
- [ ] **Offline Functionality**: 100% functionality without internet
- [ ] **Model Coverage**: All required models available offline
- [ ] **Dependency Coverage**: All dependencies bundled offline
- [ ] **Update Success**: > 95% successful offline updates

---

## Implementation Timeline

### Week 1
1. Complete DOCKER-001: Multi-stage Dockerfile optimization
2. Begin DOCKER-003: Offline optimization setup
3. Implement basic deployment scripts

### Week 2
1. Complete DOCKER-002: Build and deployment automation
2. Complete DOCKER-003: Offline optimization
3. Implement monitoring and health checks
4. Security hardening and vulnerability scanning

### Week 3
1. Comprehensive testing of deployment procedures
2. Documentation and deployment guides
3. Performance optimization and final integration

---

## Related Files & References

- `docker-compose.yml` - Current development configuration
- `Makefile` - Current build and deployment commands
- `services/api/Dockerfile` - Current API Dockerfile
- `services/asr/Dockerfile` - Current ASR Dockerfile
- `docs/deployment.md` - Deployment documentation guidelines
- `scripts/offline_prep.sh` - Offline preparation scripts
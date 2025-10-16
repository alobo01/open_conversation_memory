# EmoRobCare — Conversaciones LLM para niños TEA2

Sistema conversacional offline para niños 5-13 años con TEA2, con soporte emocional bilingüe y memoria semántica.

## 🎯 Visión rápida

- **Conversaciones naturales** con LLM local (Qwen3)
- **Memoria semántica** con Knowledge Graph + RAG
- **ASR multilingüe** con 3 niveles de precisión
- **Retroalimentación emocional**: **¡Qué bien!**, __tranquilo__
- **100% offline** después del build
- **Interfaz web** en Vue 3 (port 81)

## 📁 Estructura del repo

```
├── services/
│   ├── api/          # FastAPI /conv, /kg, /asr
│   ├── asr/          # Whisper/faster-whisper
│   ├── frontend/     # Vue 3 + Vite
│   └── fuseki-job/   # Reasoner batch jobs
├── .claude/
│   ├── agents/       # Subagentes especializados
│   ├── prompts/      # Plantillas reutilizables
│   ├── workflows/    # Orquestación de tareas
│   ├── mcp/          # Configuración MCP servers
│   └── policies/     # Reglas de seguridad
├── docs/             # Documentación técnica
├── tests/            # Tests e2e
└── scripts/          # Automatización
```

## 🛠️ Requisitos

### Hardware
- **CPU**: 4+ cores recomendados
- **RAM**: 8GB+ (16GB recomendado)
- **GPU**: Opcional, CUDA compatible para ASR
- **Storage**: 10GB+ para modelos y datos

### Software
- Docker 20.10+
- Python 3.11+
- Node.js 18+
- Git

## 🚀 Cómo iniciar (offline completo)

### 1. Clonar y setup
```bash
git clone <repo>
cd emorobcare
make setup
```

### 2. Construir imágenes Docker
```bash
# API principal
docker build -t emorobcare-api -f services/api/Dockerfile .

# ASR service
docker build -t emorobcare-asr -f services/asr/Dockerfile .

# Frontend
docker build -t emorobcare-ui -f services/frontend/Dockerfile .

# Fuseki + reasoner
docker build -t emorobcare-fuseki -f services/fuseki-job/Dockerfile .
```

### 3. Iniciar servicios (sin compose)
```bash
# 1. Base de datos (MongoDB + Qdrant + Fuseki)
docker run -d --name mongodb -p 27017:27017 mongo:7
docker run -d --name qdrant -p 6333:6333 qdrant/qdrant
docker run -d --name fuseki -p 3030:3030 stain/jena-fuseki

# 2. Servicios principales
docker run -d --name api -p 8000:8000 \
  -e MONGODB_URI=mongodb://host.docker.internal:27017 \
  -e QDRANT_URL=http://host.docker.internal:6333 \
  -e FUSEKI_URL=http://host.docker.internal:3030 \
  emorobcare-api

docker run -d --name asr -p 8001:8001 \
  --gpus all  # si tienes GPU NVIDIA \
  emorobcare-asr

# 3. Frontend
docker run -d --name ui -p 81:80 \
  -e API_URL=http://host.docker.internal:8000 \
  emorobcare-ui

# 4. Reasoner batch job
docker run --name reasoner --rm \
  -e FUSEKI_URL=http://host.docker.internal:3030 \
  emorobcare-fuseki
```

### 4. Verificar funcionamiento
```bash
# Check API health
curl http://localhost:8000/health

# Check UI
open http://localhost:81

# Check Fuseki
open http://localhost:3030
```

## ⚙️ Variables de entorno

### Modo online/offline
```bash
# OFFLINE_MODE=true (default) -> usa LLM local
# OFFLINE_MODE=false -> usa Claude API cuando disponible
export OFFLINE_MODE=true

# GPU para ASR
export ASR_GPU=true  # false para CPU-only

# Idioma por defecto
export DEFAULT_LANG=es  # o en
```

### API Keys (opcional, modo online)
```bash
export ANTHROPIC_API_KEY=your_key_here
export OPENAI_API_KEY=your_key_here
```

## 🧪 Probar la API

### Conversación básica
```bash
# Iniciar conversación
curl -X POST http://localhost:8000/conv/start \
  -H "Content-Type: application/json" \
  -d '{
    "child": "test_child",
    "topic": "school",
    "level": 3
  }'

# Responder
curl -X POST http://localhost:8000/conv/next \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "conv_123",
    "user_sentence": "Me gusta el recreo",
    "end": false
  }'
```

### ASR con diferentes niveles
```bash
# Fast mode
curl -X POST http://localhost:8001/asr/transcribe?tier=fast \
  -F "audio=@test_audio.wav"

# Balanced mode
curl -X POST http://localhost:8001/asr/transcribe?tier=balanced \
  -F "audio=@test_audio.wav"

# Accurate mode
curl -X POST http://localhost:8001/asr/transcribe?tier=accurate \
  -F "audio=@test_audio.wav"
```

### Knowledge Graph
```bash
# Insertar triples
curl -X POST http://localhost:8000/kg/insert \
  -H "Content-Type: application/json" \
  -d '{
    "sparql_update": "INSERT DATA { <ana> <likes> <school> }"
  }'

# Consultar
curl -X POST http://localhost:8000/kg/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "sparql_select": "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10"
  }'
```

## 🧠 Flujo de memoria

1. **Conversación** → MongoDB (mensajes crudos)
2. **Background task** → LLM extractor (vLLM)
3. **Triples generados** → Validación SHACL
4. **Fuseki** → Almacenamiento RDF + razonamiento
5. **Qdrant** → Búsqueda semántica para RAG
6. **Próxima conversación** → Contexto enriquecido

## 🔧 Calidad y desarrollo

### Linting y formateo
```bash
# Python
ruff check .
black .
mypy services/

# JavaScript/TypeScript
cd services/frontend
npm run lint
npm run format
```

### Tests
```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Contract tests (OpenAPI)
schemathesis run http://localhost:8000/openapi.json

# Coverage
pytest --cov=services/api tests/
```

### Pre-commit hooks
```bash
# Instalado con make setup
pre-commit run --all-files
```

## 🐳 Optimización Docker

### Tamaños objetivo
- API: ~400MB
- ASR: ~600MB (con modelos)
- Frontend: ~50MB
- Fuseki: ~200MB

### Técnicas usadas
- Multi-stage builds
- `python:3.11-slim` base
- `--no-cache` en pip installs
- Modelos descargados en build time
- `.dockerignore` optimizado

## 🚨 Troubleshooting

### Problemas comunes

**ASR lento**
```bash
# Verificar GPU
nvidia-smi

# Usar tier=fast si CPU only
curl -X POST ".../transcribe?tier=fast"
```

**LLM no responde**
```bash
# Verificar vLLM container
docker logs api

# Chequear memoria disponible
docker stats
```

**Frontend no conecta**
```bash
# Verificar API_URL
docker logs ui

# Test conexión directa
curl http://localhost:8000/health
```

### Logs detallados
```bash
# API logs
docker logs -f api

# ASR logs
docker logs -f asr

# Todos los servicios
docker-compose logs -f  # si usas compose
```

### Reset completo
```bash
# Limpiar todo
docker stop $(docker ps -aq)
docker rm $(docker ps -aq)
docker system prune -f

# Reconstruir
make clean
make setup
make deploy
```

## 📊 Métricas de monitorización

### API endpoints
- **Latencia /conv/next**: < 2s (local)
- **Throughput**: 10+ concurrentes
- **Error rate**: < 1%

### ASR
- **Fast tier**: < 1s, 85% accuracy
- **Balanced tier**: < 2s, 92% accuracy
- **Accurate tier**: < 4s, 97% accuracy

### Sistema
- **Memory usage**: < 8GB total
- **Disk usage**: < 5GB con modelos
- **CPU usage**: < 80% en conversación

## 🤝 Contribución

1. Fork del repo
2. Feature branch: `git checkout -b feature/nueva-funcionalidad`
3. Commit: `git commit -m "Agregar nueva funcionalidad"`
4. Push: `git push origin feature/nueva-funcionalidad`
5. PR con tests y documentación

## 📄 Licencia

MIT License - ver archivo LICENSE para detalles.

---

## 🆘 Ayuda

- Issues: GitHub Issues del repo
- Docs: Carpeta `docs/`
- Examples: `tests/examples/`

**Última actualización**: 2025-10-15
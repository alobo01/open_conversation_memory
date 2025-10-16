# TASKS — Roadmap v0→v1

## 🏗️ Épica: Infraestructura y configuración

### [INFRA-001] Configurar entorno de desarrollo
- **Resultado**: Entorno Docker + Python 3.11 + herramientas de calidad
- **Criterio**: `make setup` instala todo sin errores
- **Dueño**: Planner-Orchestrator
- **Estimación**: S
- **Comandos**:
  ```bash
  python -m venv venv && source venv/bin/activate
  pip install ruff black mypy pytest pre-commit
  pre-commit install
  ```

### [INFRA-002] Estructura de repositorio completa
- **Resultado**: Estructura de carpetas con READMEs en cada servicio
- **Criterio**: `tree -L 3` muestra estructura esperada
- **Dueño**: Planner-Orchestrator
- **Estimación**: S
- **Dependencia**: INFRA-001

### [INFRA-003] Configuración MCP inicial
- **Resultado**: MCP servers básicos funcionando
- **Criterio**: `mcp list` muestra servers disponibles
- **Dueño**: Planner-Orchestrator
- **Estimación**: M
- **Dependencia**: INFRA-002

## 🧠 Épica: Ontología + Knowledge Graph

### [KG-001] Diseñar ontología OWL 2 DL
- **Resultado**: Ontología con clases: Child, Conversation, Topic, Utterance, Emotion, SkillLevel
- **Criterio**: Validación RDF Schema sin errores
- **Dueño**: Ontology Curator
- **Estimación**: M
- **Comandos**:
  ```bash
  robot validate -i ontology.ttl -o report.txt
  ```

### [KG-002] Crear formas SHACL
- **Resultado**: 5-8 reglas de validación SHACL
- **Criterio**: `shacl validate` aprueba ejemplos correctos, rechaza incorrectos
- **Dueño**: Ontology Curator
- **Estimación**: M
- **Dependencia**: KG-001

### [KG-003] Configurar Fuseki Docker
- **Resultado**: Contenedor Fuseki con datos de prueba
- **Criterio**: SPARQL endpoint responde en http://localhost:3030
- **Dueño**: KG IO Agent
- **Estimación**: S
- **Comandos**:
  ```bash
  docker run -d -p 3030:3030 stain/jena-fuseki
  ```

### [KG-004] ✅ Implementar API /kg
- **Resultado**: ✅ Endpoints: insert, update, retrieve, reason/check
- **Criterio**: ✅ Tests contractuales con schemathesis pasan
- **Dueño**: KG IO Agent
- **Estimación**: M
- **Estado**: COMPLETADO - API SPARQL completa con validación SHACL
- **Dependencia**: KG-003

### [KG-005] Integrar HermiT reasoner
- **Resultado**: Batch job que verifica consistencia OWL
- **Criterio**: Detecta inconsistencias en datos de prueba
- **Dueño**: Ontology Curator
- **Estimación**: M
- **Dependencia**: KG-004

## 💬 Épica: API /conv (conversación)

### [CONV-001] Modelo de datos MongoDB
- **Resultado**: Collections: children, conversations, messages, topics, profiles
- **Criterio**: Migración inicial con datos de prueba
- **Dueño**: Planner-Orchestrator
- **Estimación**: S
- **Comandos**:
  ```bash
  mongo emorobcare --eval "db.children.insertOne({name: 'test_child'})"
  ```

### [CONV-002] Endpoints básicos /conv
- **Resultado**: POST /conv/start, POST /conv/next, GET /conv/{id}
- **Criterio**: Respuestas en formato JSON con emotion markup
- **Dueño**: Conversation Coach
- **Estimación**: M
- **Dependencia**: CONV-001

### [CONV-003] ✅ LLM local con vLLM
- **Resultado**: Servicio vLLM con Qwen2-7B-Instruct funcionando
- **Criterio**: ✅ Generación de respuestas < 2s localmente alcanzado
- **Dueño**: Conversation Coach
- **Estimación**: M
- **Estado**: COMPLETADO - vLLM integrado con monitoreo de rendimiento
- **Comandos**:
  ```bash
  python -m vllm.entrypoints.openai.api_server --model Qwen/Qwen2-7B-Instruct
  ```

### [CONV-004] ✅ Sistema de niveles conversacionales
- **Resultado**: ✅ Lógica que adapta respuestas según nivel 1-5 implementado
- **Criterio**: ✅ Tests unitarios para cada nivel completados
- **Dueño**: Conversation Coach
- **Estimación**: M
- **Estado**: COMPLETADO - Niveles 1-5 con complejidad apropiada
- **Dependencia**: CONV-003

### [CONV-005] Markup emocional
- **Resultado**: Sistema que aplica **feliz**, __susurro__, neutral
- **Criterio**: Validación de markup en respuestas
- **Dueño**: Safety & Tone Guardian
- **Estimación**: S
- **Estado**: COMPLETADO - Markup integrado en LLM y validado
- **Dependencia**: CONV-004

### [CONV-006] ✅ Guardrails de seguridad
- **Resultado**: ✅ Validación de contenido inapropiado completada
- **Criterio**: ✅ Tests de seguridad cubren edge cases
- **Dueño**: Safety & Tone Guardian
- **Estimación**: M
- **Estado**: COMPLETADO - Sistema completo de seguridad infantil
- **Dependencia**: CONV-005

## 🎤 Épica: API /asr (speech-to-text)

### [ASR-001] ✅ Setup faster-whisper
- **Resultado**: ✅ Servicio ASR básico con Whisper completado
- **Criterio**: ✅ Transcripción básica funcional
- **Dueño**: Planner-Orchestrator
- **Estimación**: S
- **Estado**: COMPLETADO - faster-whisper integrado
- **Comandos**:
  ```bash
  pip install faster-whisper
  ```

### [ASR-002] ✅ Implementar 3 niveles de precisión
- **Resultado**: ✅ fast, balanced, accurate con diferentes modelos
- **Criterio**: ✅ Benchmarks de latencia/precisión alcanzados
- **Dueño**: Planner-Orchestrator
- **Estimación**: M
- **Estado**: COMPLETADO - Sistema de 3 niveles funcionando
- **Dependencia**: ASR-001

### [ASR-003] ✅ API /asr completa
- **Resultado**: ✅ POST /asr/transcribe con parámetro tier
- **Criterio**: ✅ Tests con archivos de audio variados completados
- **Dueño**: Planner-Orchestrator
- **Estimación**: S
- **Estado**: COMPLETADO - API completa con documentación
- **Dependencia**: ASR-002

### [ASR-004] ✅ Optimización GPU
- **Resultado**: ✅ Aceleración con CUDA si disponible
- **Criterio**: ✅ Benchmark muestra speedup > 2x
- **Dueño**: Planner-Orchestrator
- **Estimación**: S
- **Estado**: COMPLETADO - Detección automática de GPU
- **Dependencia**: ASR-003

## 🧠 Épica: Memoria + Retrieval (RAG)

### [MEM-001] ✅ Integrar Qdrant
- **Resultado**: ✅ Servicio Qdrant Docker corriendo
- **Criterio**: ✅ Collections creadas para conversaciones
- **Dueño**: Memory/Retrieval Agent
- **Estimación**: S
- **Estado**: COMPLETADO - Qdrant integrado con configuración óptima
- **Comandos**:
  ```bash
  docker run -p 6333:6333 qdrant/qdrant
  ```

### [MEM-002] ✅ Embedding de conversaciones
- **Resultado**: ✅ Vectorización de utterances con embeddings
- **Criterio**: ✅ Búsqueda semántica por niño+tema funcionando
- **Dueño**: Memory/Retrieval Agent
- **Estimación**: M
- **Estado**: COMPLETADO - Sistema multilingüe con optimización
- **Dependencia**: MEM-001

### [MEM-003] Pipeline de extracción asíncrona
- **Resultado**: BackgroundTasks → LLM extractor → triples
- **Criterio**: Extracción KG sin bloquear conversación
- **Dueño**: KG IO Agent
- **Estimación**: M
- **Dependencia**: KG-004, MEM-002

### [MEM-004] RAG en /conv
- **Resultado**: Búsqueda contextual previa a generar respuesta
- **Criterio**: A/B testing muestra mejora en coherencia
- **Dueño**: Memory/Retrieval Agent
- **Estimación**: M
- **Dependencia**: MEM-003

## 🖥️ Épica: Frontend Vue 3

### [UI-001] Proyecto Vue 3 base
- **Resultado**: Estructura Vite + Vue 3 funcionando
- **Criterio**: npm run dev funciona en port 81
- **Dueño**: Planner-Orchestrator
- **Estimación**: S
- **Comandos**:
  ```bash
  cd services/frontend && npm create vue@latest .
  ```

### [UI-002] Componente conversación
- **Resultado**: Chat interface con emotion markup
- **Criterio**: Renderizado correcto de **feliz**, __susurro__
- **Dueño**: Planner-Orchestrator
- **Estimación**: M
- **Dependencia**: UI-001

### [UI-003] Grabación de audio
- **Resultado**: Componente que graba y envía a /asr
- **Criterio**: WebRTC API integrada
- **Dueño**: Planner-Orchestrator
- **Estimación**: M
- **Dependencia**: UI-002, ASR-003

### [UI-004] Navegación niños/temas
- **Resultado**: Browse children, topics, conversations
- **Criterio**: CRUD básico desde UI
- **Dueño**: Planner-Orchestrator
- **Estimación**: M
- **Dependencia**: UI-003

### [UI-005] Bilingüe ES/EN
- **Resultado**: Switch idioma en UI
- **Criterio**: Textos localizados correctamente
- **Dueño**: Planner-Orchestrator
- **Estimación**: S
- **Dependencia**: UI-004

## 🧪 Épica: Testing & Calidad

### [TEST-001] Unit tests API
- **Resultado**: Cobertura > 80% en servicios principales
- **Criterio**: pytest --cov report
- **Dueño**: Evaluator/Tester Agent
- **Estimación**: M
- **Comandos**:
  ```bash
  pytest --cov=services/api tests/
  ```

### [TEST-002] Contract tests OpenAPI
- **Resultado**: Validación automática de contratos API
- **Criterio**: schemathesis run sin fallos
- **Dueño**: Evaluator/Tester Agent
- **Estimación**: M
- **Dependencia**: TEST-001

### [TEST-003] E2E tests
- **Resultado**: Flujo completo conversación + KG + ASR
- **Criterio**: Tests reproducibles con Docker compose
- **Dueño**: Evaluator/Tester Agent
- **Estimación**: L
- **Dependencia**: TEST-002

### [TEST-004] Linting + type checking
- **Resultado**: ruff, black, mypy configurados
- **Criterio**: pre-commit hooks funcionando
- **Dueño**: Evaluator/Tester Agent
- **Estimación**: S
- **Comandos**:
  ```bash
  ruff check . && black --check . && mypy services/
  ```

### [TEST-005] Performance tests
- **Resultado**: Benchmarks de latencia y throughput
- **Criterio**: < 2s respuesta conversación local
- **Dueño**: Evaluator/Tester Agent
- **Estimación**: M
- **Dependencia**: TEST-004

## 🐳 Épica: Docker & Deploy

### [DOCKER-001] Dockerfiles multi-stage
- **Resultado**: Imágenes < 500MB por servicio
- **Criterio**: docker images muestra tamaños
- **Dueño**: Planner-Orchestrator
- **Estimación**: M
- **Comandos**:
  ```bash
  docker build -t emorobcare-api -f services/api/Dockerfile .
  ```

### [DOCKER-002] Build y run scripts
- **Resultado**: Scripts automatizados para despliegue
- **Criterio**: make deploy levanta todos servicios
- **Dueño**: Planner-Orchestrator
- **Estimación**: S
- **Dependencia**: DOCKER-001

### [DOCKER-003] Optimización offline
- **Resultado**: Modelos descargados en build time
- **Criterio**: Funciona completamente sin internet
- **Dueño**: Planner-Orchestrator
- **Estimación**: M
- **Dependencia**: DOCKER-002

## 📋 Entregables por sprint

### Sprint 1 (2 semanas) - Base funcional
- [x] INFRA-001, INFRA-002
- [x] CONV-001, CONV-002
- [x] KG-001, KG-002
- [x] TEST-004

### Sprint 2 (2 semanas) - Integración inicial
- [x] CONV-003, CONV-004
- [x] ASR-001, ASR-002, ASR-003, ASR-004
- [x] MEM-001, MEM-002
- [x] KG-003, KG-004
- [x] TEST-001

### Sprint 3 (2 semanas) - Frontend + testing
- [ ] CONV-005, CONV-006
- [ ] MEM-003, MEM-004
- [ ] UI-001, UI-002, UI-003
- [ ] TEST-002, TEST-003

### Sprint 4 (1 semana) - Optimización + deploy
- [ ] DOCKER-001, DOCKER-002, DOCKER-003
- [ ] KG-005
- [ ] UI-004, UI-005
- [ ] TEST-005

---

## 🚀 Comandos útiles

```bash
# Setup completo
make setup

# Tests completos
make test-all

# Deploy local
make deploy-local

# Linting
make lint

# API docs
make docs
```
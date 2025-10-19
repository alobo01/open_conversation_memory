# PRD — Conversación abierta niño TEA2 + LLM (APIs: /conv, /kg, /asr)

## 1. Objetivo & éxito

### v0 (MVP)
- API funcional para conversaciones con LLM local
- Sistema de KG básico con validación SHACL
- ASR con 3 niveles (fast/balanced/accurate)
- Interfaz mínima en navegador (port 81)

### v1
- UI completa en Vue 3 con grabación/reproducción de audio
- Sistema completo de perfiles y configuración por usuario
- Evaluación automática de calidad conversacional

**Éxito:** Niños 5-13 con TEA2 pueden mantener conversaciones naturales en español/inglés con retroalimentación emocional adecuada.

## 2. Usuarios & casos de uso

### Usuarios primarios
- **Niños 5-13 años con TEA2**: Niveles conversacionales variables
- **Terapeutas/tutores**: Configuran perfiles y revisan progresos
- **Investigadores**: Acceden a datos anonimizados para análisis

### Casos de uso
1. **Conversación guiada**: Niño elige tema (escuela, amigos, etc.)
2. **Práctica social**: Interacciones seguras con retroalimentación emocional
3. **Seguimiento**: Monitoreo de progreso conversacional

## 3. Alcance v0 / Fuera de alcance

### Incluido
- APIs: /conv, /kg, /asr completas
- Memoria híbrida: MongoDB + Qdrant + Fuseki
- LLM local (Qwen3-4B/8B instruct)
- ASR con Whisper/faster-whisper
- Ontología OWL 2 DL + SHACL

### Excluido
- Sistema de autenticación
- Interfaz completa (solo prueba básica)
- Cifrado de datos
- Sincronización remota

## 4. Requisitos funcionales

### API /conv (conversación)
```
POST /conv/start
{
  "child": "id|name",
  "topic": "school|hobbies|holidays|food|friends",
  "level": 1-5
}
→ {
  "conversation_id": "...",
  "starting_sentence": "__Hola__, ¿te apetece hablar de la escuela?",
  "end": false
}

POST /conv/next
{
  "conversation_id": "...",
  "user_sentence": "...",
  "end": false
}
→ {
  "reply": "**¡Qué bien!** ¿Qué te gusta más del recreo?",
  "end": false
}

# Memory endpoints
GET /conv/memory/{child_id}/context?topic=school&query=juegos&limit=3
→ {
  "child_id": "ana_7",
  "context": [
    {"text": "Me gusta jugar al fútbol", "score": 0.85, "timestamp": 1704110400}
  ]
}

GET /conv/memory/{child_id}/search?query=deportes&limit=5
GET /conv/memory/{child_id}/summary?topic=hobbies
DELETE /conv/memory/{conversation_id}
GET /conv/memory/status
```

**Integración con vLLM**: El servicio LLM debe atacar la API de vLLM (OpenAI-compatible) en lugar de importar vLLM directamente:
```python
# services/api/services/llm_service.py debe usar:
import httpx
response = await httpx.post(
    "http://localhost:8001/v1/completions",
    json={"model": "Qwen/Qwen2-7B-Instruct", "prompt": prompt, "max_tokens": 150}
)
```

### API /kg (knowledge graph)
```
POST /kg/insert → INSERT DATA {...}
POST /kg/update → DELETE/INSERT WHERE {...}
POST /kg/retrieve → SELECT ...
POST /kg/reason/check → {consistent: true, violations: []}
```

### API /asr (speech-to-text)
```
POST /asr/transcribe?tier=fast|balanced|accurate
→ {text: "Hola, estoy bien", lang: "es"}
```

### Memoria híbrida (Embedded-Memory Architecture)
- **MongoDB**: Perfiles, conversaciones, mensajes (persistencia estructurada)
- **Qdrant**: Vector embeddings para búsqueda semántica por niño+tema
  - Modelo: `paraphrase-multilingual-MiniLM-L12-v2` (384 dimensiones)
  - Embeddings automáticos de cada mensaje
  - Filtrado por child_id, topic, nivel conversacional
- **Fuseki**: Triple store OWL + SHACL (conocimiento explícito)

### Sistema de memoria semántica
- **Embedding automático**: Cada mensaje se vectoriza al guardarse
- **Búsqueda contextual**: Recupera conversaciones similares previas
- **Context retrieval endpoints**:
  - `GET /conv/memory/{child_id}/context` - Contexto relevante
  - `GET /conv/memory/{child_id}/search` - Búsqueda semántica
  - `GET /conv/memory/{child_id}/summary` - Resumen de memoria
  - `DELETE /conv/memory/{conversation_id}` - Borrar memoria
  - `GET /conv/memory/status` - Estado del sistema

### Extracción asíncrona (Knowledge Graph Population)
BackgroundTasks → vLLM extractor API → entidades+relaciones → validación SHACL → triples Fuseki
- **Pipeline**: Conversación → extracción LLM → RDF triples → validación → inserción KG
- **Validación**: SHACL shapes previo a inserción en Fuseki
- **Performance**: < 30 segundos por conversación, sin bloquear respuestas

## 5. Requisitos no funcionales

### Operación
- **Offline completo** después del build
- **Docker imágenes < 500MB** cada servicio (excepto vLLM que es externo)
- **Port 81** para UI de prueba
- **Español por defecto**, bilingüe ES/EN
- **vLLM como servicio externo**: API en port 8001 (OpenAI-compatible)

### Performance
- **Latencia respuesta conversacional**: < 2s (incluyendo embedding y context retrieval)
- **Context retrieval**: < 500ms para búsqueda semántica
- **Extracción KG**: < 30s por conversación (background, no bloqueante)
- **Embedding generation**: < 200ms por mensaje

### Emociones en texto
- **énfasis positivo**: **¡Qué bien!**
- **susurro calmante**: __respira profundo__
- **neutral**: sin marcas

### Niveles conversacionales
- **1-2**: Frases cortas, 1 idea por oración
- **3-4**: Oraciones simples, conectores básicos
- **5**: Conversación fluida con variedad léxica

## 6. Datos & privacidad

### Almacenamiento local
- Sin datos personales innecesarios
- Retención indefinida de conversaciones
- Exportación JSON futura

### Seguridad
- Sin PII en logs
- Configuración por perfil de "temas permitidos/prohibidos"
- Validación SHACL para consistencia ontológica

## 7. Métricas de éxito

### Conversacional
- **Tasa de continuación Conversación**: > 70%
- **Coherencia temática**: mantenimiento del tema elegido
- **Variedad léxica**: uso diverso de vocabulario

### Técnica
- **Tasa errores SHACL**: < 5%
- **Cobertura tests**: > 90%
- **Latencia respuesta**: < 2s local

## 8. Riesgos & mitigación

### ASR errores
- **Riesgo**: Mala transcripción en niños
- **Mitigación**: 3 niveles de precisión, validación manual

### Seguridad contenido
- **Riesgo**: Respuestas inapropiadas
- **Mitigación**: Safety guardian agent, reglas configurables

### Consistencia ontológica
- **Riesgo**: Inconsistencias en KG
- **Mitigación**: SHACL + HermiT reasoner batch

## 9. Hitos & entregables

### Sprint 1 (2 semanas)
- [ ] API base FastAPI (/conv)
- [ ] MongoDB collections iniciales
- [ ] Tests básicos

### Sprint 2 (2 semanas)
- [ ] Servicio ASR con 3 niveles
- [ ] Integración Qdrant para RAG
- [ ] UI mínima Vue 3

### Sprint 3 (2 semanas)
- [ ] Servicio Fuseki + ontología
- [ ] Validación SHACL
- [ ] End-to-end tests

### Sprint 4 (1 semana)
- [ ] Optimización Docker
- [ ] Documentación completa
- [ ] Deploy demo

## 10. Anexos

### Prompt de extracción de entidades
```markdown
# Entity Extraction Prompt

You are an expert entity extractor for child conversations. Extract entities and relationships from the following conversation turn.

**Conversation:**
Child: {child_text}
Assistant: {assistant_text}

**Extract:**
1. **Entities**: People, places, objects, activities mentioned
2. **Emotions**: Emotional states expressed
3. **Relationships**: Connections between entities
4. **Topics**: Main subjects discussed

**Output format (JSON):**
{
  "entities": [
    {"type": "Activity", "value": "fútbol", "confidence": 0.9},
    {"type": "Place", "value": "escuela", "confidence": 0.85}
  ],
  "emotions": [{"type": "positive", "intensity": 0.8}],
  "relationships": [
    {"subject": "child", "predicate": "likes", "object": "fútbol"}
  ],
  "topics": ["hobbies", "sports"]
}

Extract only factual information. Be conservative with confidence scores.
```

### SHACL Shapes - memoria.ttl
```turtle
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix emo: <https://iiia.csic.es/kg/emorobcare#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

# Child Memory Shape
emo:ChildMemoryShape a sh:NodeShape ;
    sh:targetClass emo:Child ;
    sh:property [
        sh:path emo:hasMemoryEntry ;
        sh:node emo:MemoryEntryShape ;
        sh:minCount 0 ;
    ] ;
    sh:property [
        sh:path emo:hasInterest ;
        sh:class emo:Topic ;
        sh:minCount 0 ;
    ] .

# Memory Entry Shape
emo:MemoryEntryShape a sh:NodeShape ;
    sh:property [
        sh:path emo:text ;
        sh:datatype xsd:string ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
    ] ;
    sh:property [
        sh:path emo:embedding ;
        sh:datatype xsd:string ;  # JSON array as string
        sh:maxCount 1 ;
    ] ;
    sh:property [
        sh:path emo:timestamp ;
        sh:datatype xsd:dateTime ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
    ] ;
    sh:property [
        sh:path emo:relevanceScore ;
        sh:datatype xsd:float ;
        sh:minInclusive 0.0 ;
        sh:maxInclusive 1.0 ;
    ] .

# Extracted Entity Shape
emo:ExtractedEntityShape a sh:NodeShape ;
    sh:targetClass emo:ExtractedEntity ;
    sh:property [
        sh:path emo:entityType ;
        sh:in ("Activity" "Place" "Person" "Object" "Emotion") ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
    ] ;
    sh:property [
        sh:path emo:value ;
        sh:datatype xsd:string ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
    ] ;
    sh:property [
        sh:path emo:confidence ;
        sh:datatype xsd:float ;
        sh:minInclusive 0.0 ;
        sh:maxInclusive 1.0 ;
    ] .
```

### Ejemplo conversación completo
```json
{
  "conversation_id": "conv_123",
  "child": "ana_7",
  "topic": "school",
  "level": 3,
  "turns": [
    {
      "role": "assistant",
      "text": "__Hola__ Ana, ¿cómo fue tu día en el colegio?",
      "emotion": "neutral"
    },
    {
      "role": "user",
      "text": "Bien, jugué en el recreo",
      "asr_confidence": 0.92
    },
    {
      "role": "assistant",
      "text": "**¡Qué divertido!** ¿Con qué jugaste?",
      "emotion": "positive"
    }
  ]
}
```

### Configuración perfil niño
```json
{
  "child_id": "ana_7",
  "age": 7,
  "preferred_topics": ["school", "friends"],
  "avoid_topics": ["family_issues"],
  "level": 3,
  "sensitivity": "medium",
  "language": "es"
}
```
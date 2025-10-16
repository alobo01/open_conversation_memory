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

### Memoria híbrida
- **MongoDB**: Perfiles, conversaciones, mensajes
- **Qdrant**: Búsqueda semántica por niño+tema
- **Fuseki**: Triple store OWL + SHACL

### Extracción asíncrona
BackgroundTasks → vLLM extractor → triples SHACL → Fuseki

## 5. Requisitos no funcionales

### Operación
- **Offline completo** después del build
- **Docker imágenes < 500MB** cada servicio
- **Port 81** para UI de prueba
- **Español por defecto**, bilingüe ES/EN

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
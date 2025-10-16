# Template para extracción de Knowledge Graph

## Conversación a procesar
```
{conversation_text}
```

## Contexto
- **ID Niño**: {child_id}
- **ID Conversación**: {conversation_id}
- **Tema principal**: {main_topic}
- **Timestamp**: {timestamp}

## Instrucciones de extracción

### 1. Identificar entidades principales
- Personas mencionadas (amigos, familiares)
- Lugares (escuela, casa, parque)
- Actividades (juegos, estudiar, comer)
- Emociones explícitas o implícitas
- Preferencias e intereses

### 2. Extraer relaciones
- [Persona] -> [le_gusta] -> [Actividad]
- [Lugar] -> [es_tipo_de] -> [Categoría]
- [Niño] -> [siente] -> [Emoción]
- [Actividad] -> [ocurre_en] -> [Lugar]

### 3. Generar triples RDF
Usando prefijos:
```
@prefix emo: <https://iiia.csic.es/kg/emotion/> .
@prefix act: <https://iiia.csic.es/kg/activity/> .
@prefix loc: <https://iiia.csic.es/kg/location/> .
@prefix rel: <https://iiia.csic.es/kg/relation/> .
```

### 4. Formato de salida
```json
{
  "extracted_triples": [
    {
      "subject": "emo:child_123",
      "predicate": "rel:likes",
      "object": "act:playing_soccer",
      "confidence": 0.9
    }
  ],
  "entities": [
    {
      "name": "playing_soccer",
      "type": "Activity",
      "iri": "act:playing_soccer"
    }
  ],
  "metadata": {
    "extraction_model": "qwen3-4b",
    "confidence_threshold": 0.7,
    "total_triples": 5
  }
}
```

## Ejemplo de extracción

### Conversación original
"Hoy en el colegio jugué fútbol con mis amigos en el recreo. Me encanta porque corre mucho y gana."

### Triples extraídos
```turtle
emo:child_123 rel:played act:soccer .
emo:child_123 rel:hasFriend emo:friend_group .
act:soccer rel:atLocation loc:school_playground .
emo:child_123 rel:feels emo:happy .
act:soccer rel:hasProperty act:running .
```

## Reglas de calidad
- Solo extraer relaciones con confianza > 0.7
- Normalizar entidades cuando sea posible
- Incluir contexto temporal cuando sea relevante
- Validar contra ontología existente
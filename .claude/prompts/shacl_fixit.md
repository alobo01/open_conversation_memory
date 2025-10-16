# Template para reparar violaciones SHACL

## Violaciones detectadas
```json
{shacl_violations}
```

## Grafo actual
```turtle
{current_graph}
```

## Shapes SHACL relevantes
```turtle
{shacl_shapes}
```

## Instrucciones de reparación

### 1. Analizar violaciones
Para cada violación:
- Identificar el tipo de constraint fallido
- Localizar los nodos afectados
- Determinar causa raíz

### 2. Proponer soluciones
- **Datos faltantes**: Agregar valores por defecto
- **Valores incorrectos**: Corregir según reglas
- **Relaciones inválidas**: Eliminar o reemplazar
- **Tipos incorrectos**: Convertir o eliminar

### 3. Generar SPARQL UPDATE
Crear sentencias UPDATE para:
- INSERT DATA para agregar faltantes
- DELETE WHERE para eliminar incorrectos
- DELETE/INSERT WHERE para modificar

### 4. Formato de salida
```json
{
  "analysis": {
    "total_violations": 3,
    "violation_types": ["minCount", "datatype", "allowedValues"],
    "affected_nodes": ["emo:child_123", "act:unknown"]
  },
  "repairs": [
    {
      "violation_id": "v1",
      "repair_type": "INSERT",
      "sparql_update": "INSERT DATA { emo:child_123 rel:age \"7\"^^xsd:integer }",
      "confidence": 0.95
    }
  ],
  "validation_plan": [
    "Ejecutar reparaciones en orden",
    "Re-validar con SHACL",
    "Verificar consistencia general"
  ]
}
```

## Ejemplos comunes de reparación

### Violación: minCount en propiedad requerida
```sparql
INSERT DATA {
  emo:child_123 rel:hasAge "7"^^xsd:integer .
}
```

### Violación: datatype incorrecto
```sparql
DELETE WHERE {
  emo:child_123 rel:age ?age .
}
INSERT DATA {
  emo:child_123 rel:age "7"^^xsd:integer .
}
```

### Violación: valor no permitido
```sparql
DELETE WHERE {
  emo:child_123 rel:favoriteColor "purple" .
}
INSERT DATA {
  emo:child_123 rel:favoriteColor "blue" .
}
```

## Prioridades de reparación
1. **Alta**: Violaciones que rompen consultas básicas
2. **Media**: Inconsistencias de datos
3. **Baja**: Valores faltantes opcionales

## Reglas de seguridad
- Nunca eliminar datos críticos sin confirmación
- Mantener traceability de cambios
- Validar antes de aplicar cambios masivos
- Crear backup antes de reparaciones complejas
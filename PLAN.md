# Plan

---

## Table of Contents

| Line | Section |
|------|----------|
| 1 | **1. Plan** |
| 3 | 1.1 Confirm Requirements |
| 6 | 1.2 Architectural Design |
| 9 | 1.3 API Definition |
| 12 | 1.4 Ontology & KG |
| 15 | 1.5 Memory & Retrieval |
| 18 | 1.6 Subagents & Workflow |
| 21 | 1.7 ASR Integration |
| 24 | 1.8 Safety & Tone Controls |
| 27 | 1.9 Testing Strategy |
| 30 | 1.10 Dockerization |
| 33 | 1.11 Documentation & Prompts |
| 36 | 1.12 Validation & Roadmap |
| 39 | **2. Key Decisions & Trade-offs** |
| 41 | 2.1 Language & UI |
| 44 | 2.2 Model Selection |
| 47 | 2.3 Reasoning vs Speed |
| 50 | 2.4 Knowledge Graph Integration |
| 53 | 2.5 Safety & Personalization |
| 56 | 2.6 Data Persistence |
| 59 | 2.7 Security |
| 62 | 2.8 Architecture |
| 65 | 2.9 Scaling |
| 68 | 2.10 Reasoner Performance |
| 71 | **3. Architecture & Ports** |
| 73 | 3.1 Frontend (Vue3, port 81) |
| 76 | 3.2 Backend (FastAPI, port 8000) |
| 79 | 3.3 Databases |
| 83 | 3.4 ASR Service |
| 86 | 3.5 Reasoner Container |
| 89 | **4. API Endpoints** |
| 91 | 4.1 `/conv` (POST) |
| 106 | 4.2 `/asr` (POST) |
| 114 | 4.3 `/kg` (GET/POST) |
| 125 | **5. Ontology (OWL 2 DL)** |
| 136 | 5.1 Classes & Properties |
| 144 | 5.2 Example TTL |
| 151 | **6. SHACL Shapes** |
| 153 | 6.1 Child Shape |
| 160 | 6.2 Utterance Shape |
| 165 | **7. Reasoning** |
| 172 | **8. Memory & Retrieval** |
| 185 | **9. ASR Modes** |
| 196 | **10. Testing & Linting** |
| 203 | **11. Docker Setup** |
| 211 | **12. Documentation** |
| 216 | **13. Validation Roadmap** |

---

# 1. Plan

## 1.1 Confirm Requirements
Clarify the system goals (conversation for autistic child, offline, Spanish-first) and constraints (small models offline, safety rules per child).

## 1.2 Architectural Design
Sketch out the main components (APIs, databases, LLM, ASR, KG) and how they interact. Decide on ports and data flow between frontend, backend, DBs, and ML models.

## 1.3 API Definition
Specify the three API endpoints – `/conv`, `/kg`, `/asr` – including request/response JSON formats and example payloads. Incorporate emotion markup in conversation responses.

## 1.4 Ontology & KG
Design a minimal ontology (OWL 2 DL) for `Child`, `Conversation`, `Utterance`, `Topic`, `Emotion`, etc., with SHACL shapes for data validation. Plan how to sync JSON profile data with RDF triples.

## 1.5 Memory & Retrieval
Plan hybrid memory: use MongoDB for profile/conversation storage, Fuseki for semantic triples, and Qdrant for vector embeddings. Include a pipeline to extract facts from conversations and update the KG asynchronously.

## 1.6 Subagents & Workflow
Outline Claude Code subagents for specialized tasks (planner, coach, safety, ontology, KG I/O, retrieval, tester). Determine each agent’s role, tool access (MCP servers for DB/FS/HTTP), and how the orchestrator will call them.

## 1.7 ASR Integration
Choose Whisper large-v3 as the base ASR model, and define three presets (fast, balanced, accurate) using faster-whisper optimization. Note expected performance trade-offs for each preset.

## 1.8 Safety & Tone Controls
Define how the system ensures child-appropriate content (via Safety Guardian agent and configurable “do not discuss” lists per child) and adjusts language complexity (Conversation Coach agent uses child’s skill level).

## 1.9 Testing Strategy
Plan unit tests for each component (FastAPI endpoints, KG updates, ASR outputs), integration tests for end-to-end conversation, and use tools like Schemathesis for API fuzz testing. Set up linting (`ruff`, `black`) and type checking (`mypy`) with pre-commit hooks.

## 1.10 Dockerization
Outline Docker images for each service (API, ASR, frontend, reasoner, DBs), using multi-stage builds to minimize size. Ensure images can run fully offline on the target GPU machine after one-time downloads.

## 1.11 Documentation & Prompts
Prepare prompts for generating documentation files (`PRD.md`, `TASKS.md`, `README.md`). Ensure these prompts guide Claude to produce ≤500 line docs that cover the system thoroughly.

## 1.12 Validation & Roadmap
Draft an acceptance checklist for v0 (minimal API-only functionality) and v1 (with full UI and advanced features) to verify the implementation against requirements.

---

# 2. Key Decisions & Trade-offs

## 2.1 Language & UI
Prioritize Spanish for child interactions (with English available for UI toggles). Store prompts and messages in both languages, defaulting to Spanish.

## 2.2 Model Selection
Use Qwen3 4B/8B instruct models served via vLLM for efficiency. These compact models balance capability and low VRAM use for offline GPU deployment.

## 2.3 Reasoning vs Speed
Use a multi-agent prompt strategy (Planner, Coach, Safety, etc.) to ensure safety and personalization, trading throughput for correctness.

## 2.4 Knowledge Graph Integration
Combine MongoDB (for JSON persistence) and Fuseki RDF store (for semantics and reasoning via OWL + SHACL). Maintain sync through a KG I/O agent.

## 2.5 Safety & Personalization
Implement configurable per-child safety rules via allow/deny lists and tone filtering by the Safety Guardian agent.

## 2.6 Data Persistence
Retain all data locally (no deletion, no cloud calls) for simplicity and privacy.

## 2.7 Security
Skip authentication and encryption in v0 since it’s a local prototype, noting future security requirements.

## 2.8 Architecture
Use lightweight microservices: API, ASR, DBs, UI, reasoner — all in separate Docker containers.

## 2.9 Scaling
Low-concurrency design; prioritize simplicity and correctness over scalability.

## 2.10 Reasoner Performance
Use HermiT for OWL 2 DL reasoning, with small datasets ensuring speed; supplement with SHACL for lightweight validation.

---

# 3. Architecture & Ports

## 3.1 Frontend (Vue3, port 81)
Simulates child chat and admin panels.

## 3.2 Backend (FastAPI, port 8000)
- Endpoints: `/conv`, `/kg`, `/asr`
- Integrates local LLM (Qwen via vLLM)
- Orchestrates Planner, Coach, Safety, Ontology agents

## 3.3 Databases
- **MongoDB (27017)** – child profiles & conversations  
- **Qdrant (6333)** – semantic memory vectors  
- **Fuseki (3030)** – RDF store (ontology, triples)

## 3.4 ASR Service
Whisper large-v3 via faster-whisper (port 5000).

## 3.5 Reasoner Container
Runs HermiT and SHACL validations periodically.

---

# 4. API Endpoints

## 4.1 `/conv` (POST)
Handles conversational turns.  
Includes safety guard, tone adjustments, emotion markup, and background KG/memory updates.

## 4.2 `/asr` (POST)
Speech-to-text transcription using Whisper large-v3.  
Supports presets: `fast`, `balanced`, `accurate`.

## 4.3 `/kg` (GET/POST)
Exposes SPARQL endpoints for querying or updating RDF data.

---

# 5. Ontology (OWL 2 DL)

## 5.1 Classes & Properties
Core classes: `Child`, `Conversation`, `Utterance`, `Topic`, `Emotion`, `SkillLevel`  
Object/Data properties: `hasUtterance`, `saidBy`, `aboutTopic`, `expressesEmotion`, `hasName`, `hasSkillLevel`, etc.

## 5.2 Example TTL
```ttl
@prefix iiia: <https://iiia.csic.es/kg/> .

iiia:Child rdf:type owl:Class .
iiia:Conversation rdf:type owl:Class .
iiia:Utterance rdf:type owl:Class .
iiia:hasName rdf:type owl:DatatypeProperty ; rdfs:domain iiia:Child .
````

---

# 6. SHACL Shapes

## 6.1 Child Shape

Ensures each `Child` has exactly one `hasName` and one `hasSkillLevel` (1–5).

## 6.2 Utterance Shape

Each `Utterance` must have text content and speaker.

---

# 7. Reasoning

Use **HermiT** for OWL DL inference and **SHACL** for constraint validation.

Example rule:

```
Child(?c) ∧ Conversation(?k) ∧ hasParticipant(?k,?c) ∧ aboutTopic(?k,?t)
→ hasInterest(?c,?t)
```

---

# 8. Memory & Retrieval

Combines:

* **Vector memory (Qdrant)** for semantic recall
* **Structured KG (Fuseki)** for explicit knowledge
* **Ontology Curator Agent** for ontology extension proposals
* **SHACL validation** for data consistency

---

# 9. ASR Modes

| Mode     | Precision | Speed         | Notes          |
| -------- | --------- | ------------- | -------------- |
| Fast     | int8      | ~4× realtime  | lower accuracy |
| Balanced | fp16      | 2× realtime   | default        |
| Accurate | fp16/fp32 | 0.5× realtime | max accuracy   |

---

# 10. Testing & Linting

Use `pytest`, `Schemathesis`, `ruff`, `black`, `mypy`.
Test prompt formatting, safety filters, tone adjustments, ontology updates, and API schema compliance.

---

# 11. Docker Setup

| Service  | Port  | Description     |
| -------- | ----- | --------------- |
| Frontend | 81    | Vue3 demo UI    |
| API      | 8000  | FastAPI core    |
| MongoDB  | 27017 | Profile storage |
| Fuseki   | 3030  | RDF triples     |
| Qdrant   | 6333  | Vector DB       |
| ASR      | 5000  | Whisper service |
| Reasoner | —     | OWL/SHACL job   |

---

# 12. Documentation

Generate:

* `PRD.md` – Product Requirements
* `TASKS.md` – Task breakdown
* `README.md` – Setup and usage

---

# 13. Validation Roadmap

| Version | Description                                                                |
| ------- | -------------------------------------------------------------------------- |
| v0      | Minimal API-only prototype                                                 |
| v1      | Full UI, multi-agent orchestration, ontology reasoning, offline deployment |


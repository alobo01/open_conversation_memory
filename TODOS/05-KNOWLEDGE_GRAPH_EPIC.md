# 🧠 Knowledge Graph Epic (KG)

## Overview
Complete the knowledge graph system with HermiT reasoner integration to enable advanced ontological reasoning and consistency checking for the EmoRobCare system.

## Tasks

### KG-005: Integrar HermiT reasoner ⏳ **MEDIUM PRIORITY**
**Status**: Pending implementation
**Estimated**: 20 hours
**Dependencies**: KG-004 ✅
**Files to implement**:
- `services/fuseki-job/hermit_reasoner.py` (new)
- `services/fuseki-job/reasoning_service.py` (new)
- `services/fuseki-job/models/reasoning_models.py` (new)
- `services/api/routers/knowledge_graph.py` (extend)
- `config/hermit_config.py` (new)

#### Subtasks:
- [ ] **HermiT Integration**: Integrate HermiT reasoner into the system
- [ ] **OWL 2 DL Reasoning**: Implement OWL 2 DL inference capabilities
- [ ] **Consistency Checking**: Batch job for knowledge graph consistency validation
- [ ] **Inference Rules**: Define custom inference rules for child development domain
- [ ] **Performance Optimization**: Optimize reasoning performance for large knowledge graphs
- [ ] **Error Handling**: Handle reasoning errors and inconsistencies gracefully
- [ ] **API Integration**: Extend KG API to include reasoning endpoints
- [ ] **Scheduled Jobs**: Implement scheduled reasoning tasks

#### Implementation Details:
```python
# services/fuseki-job/hermit_reasoner.py
import subprocess
import tempfile
import os
from pathlib import Path
from typing import List, Dict, Optional

class HermiTReasoner:
    def __init__(self, hermit_path: str = "/opt/hermit/hermit.jar"):
        self.hermit_path = hermit_path
        self.java_path = "/usr/bin/java"

    def check_consistency(self, owl_file: Path) -> Dict:
        """Check if OWL ontology is consistent"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.owl', delete=False) as f:
                # Write ontology to temporary file
                f.write(owl_file.read_text())
                temp_file = f.name

            # Run HermiT reasoner
            cmd = [
                self.java_path,
                "-jar", self.hermit_path,
                "-explain", "inconsistent",
                "-t", "300",  # 5 minute timeout
                temp_file
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600
            )

            os.unlink(temp_file)

            return {
                "consistent": result.returncode == 0,
                "explanations": result.stdout if result.returncode != 0 else "",
                "errors": result.stderr
            }

        except subprocess.TimeoutExpired:
            return {
                "consistent": False,
                "explanations": "Reasoning timeout exceeded",
                "errors": "Timeout"
            }

    def classify_ontology(self, owl_file: Path) -> Dict:
        """Classify ontology and return inferred information"""
        # Implementation for ontology classification
        pass

    def compute_inferred_hierarchy(self, owl_file: Path) -> Dict:
        """Compute inferred class hierarchy"""
        # Implementation for hierarchy computation
        pass
```

#### Acceptance Criteria:
- [ ] HermiT reasoner integrates successfully with the system
- [ ] Consistency checking runs without errors on valid data
- [ ] Inconsistency explanations are clear and actionable
- [ ] Reasoning performance meets requirements (< 5 minutes for typical KG)
- [ ] API endpoints provide access to reasoning results

---

## Cross-Cutting Features

### Ontology Enhancement
- [ ] **Child Development Ontology**: Extend ontology with child-specific concepts
- [ ] **Educational Concepts**: Add educational and therapeutic concepts
- [ ] **Emotional States**: Enhanced emotion representation and relationships
- [ ] **Conversation Patterns**: Ontology for conversation patterns and outcomes

### Integration with Memory System
- [ ] **Knowledge Extraction**: Enhanced entity and relationship extraction
- [ ] **Inference Integration**: Use inferred knowledge in conversations
- [ ] **Consistency Validation**: Ensure extracted data maintains consistency
- [ **Learning Patterns**: Identify and store learning patterns

### Performance Optimization
- [ ] **Incremental Reasoning**: Implement incremental reasoning for efficiency
- [ ] **Caching**: Cache reasoning results for frequently accessed data
- [ ] **Batch Processing**: Optimize batch processing of large datasets
- [ ] **Memory Management**: Efficient memory usage for large knowledge graphs

---

## Implementation Details

### Reasoning Service Architecture
```python
# services/fuseki-job/reasoning_service.py
class ReasoningService:
    def __init__(self, fuseki_url: str, hermit_reasoner: HermiTReasoner):
        self.fuseki_url = fuseki_url
        self.hermit = hermit_reasoner
        self.reasoning_cache = {}

    async def run_consistency_check(self) -> Dict:
        """Run consistency check on the entire knowledge graph"""
        # 1. Export current KG as OWL
        # 2. Run HermiT reasoning
        # 3. Analyze results
        # 4. Store results for API access
        pass

    async def classify_conversation_data(self, conversation_id: str) -> Dict:
        """Classify specific conversation data"""
        # Implementation for conversation-specific reasoning
        pass

    async def detect_learning_patterns(self, child_id: str) -> List[Dict]:
        """Detect learning patterns from knowledge graph"""
        # Implementation for pattern detection
        pass
```

### API Extensions
```python
# services/api/routers/knowledge_graph.py extension
@router.post("/reason/consistency")
async def check_consistency():
    """Trigger consistency check on knowledge graph"""
    # Trigger background reasoning job
    pass

@router.get("/reason/results/{job_id}")
async def get_reasoning_results(job_id: str):
    """Get results of reasoning job"""
    # Return reasoning results
    pass

@router.post("/reason/classify")
async def classify_entities(entities: List[str]):
    """Classify entities using inferred knowledge"""
    # Use reasoning to enhance entity classification
    pass
```

---

## Testing Requirements

### Unit Tests
- [ ] **HermiT Integration Tests**: Test reasoner integration and functionality
- [ ] **Reasoning Service Tests**: Test reasoning service logic
- [ ] **Ontology Tests**: Test ontology consistency and validity
- [ ] **Performance Tests**: Test reasoning performance with various data sizes

### Integration Tests
- [ ] **End-to-End Reasoning**: Test complete reasoning pipeline
- [ ] **API Integration Tests**: Test reasoning API endpoints
- [ ] **Memory Integration Tests**: Test reasoning integration with memory system
- [ ] **Error Handling Tests**: Test error conditions and recovery

### Performance Tests
- [ ] **Scalability Tests**: Test reasoning with large knowledge graphs
- [ ] **Timeout Tests**: Test reasoning timeout handling
- [ ] **Memory Usage Tests**: Monitor memory consumption during reasoning
- [ ] **Concurrent Reasoning**: Test multiple reasoning jobs running concurrently

---

## Success Metrics

### Functional Metrics
- [ ] **Consistency Detection**: Detect all inconsistencies in test datasets
- [ ] **Reasoning Accuracy**: > 95% accuracy in inference tasks
- [ ] **Explanation Quality**: Clear and actionable explanations for inconsistencies
- [ ] **API Reliability**: > 99% success rate for reasoning API calls

### Performance Metrics
- [ ] **Reasoning Speed**: < 5 minutes for typical knowledge graph
- [ ] **Memory Usage**: < 4GB memory usage for reasoning tasks
- [ ] **Cache Hit Rate**: > 80% cache hit rate for repeated queries
- [ ] **Concurrent Jobs**: Support for 3+ concurrent reasoning jobs

---

## Risks & Mitigations

### Technical Risks
- **Reasoning Performance**: Mitigate with incremental reasoning and caching
- **Memory Usage**: Implement efficient memory management and cleanup
- **Complexity**: Start with basic reasoning and expand gradually
- **Integration Complexity**: Careful API design and thorough testing

### Data Risks
- **Inconsistency Propagation**: Implement validation and error handling
- **Knowledge Quality**: Multiple validation layers and expert review
- **Scalability**: Performance testing and optimization strategies

---

## Implementation Timeline

### Week 1
1. Set up HermiT reasoner integration
2. Implement basic consistency checking
3. Create reasoning service foundation
4. Begin API extensions

### Week 2
1. Complete reasoning service implementation
2. Implement performance optimization
3. Add comprehensive error handling
4. Complete API integration

### Week 3
1. Comprehensive testing suite
2. Performance optimization and tuning
3. Documentation and deployment preparation
4. Integration testing with memory system

---

## Related Files & References

- `services/api/routers/knowledge_graph.py` - Existing KG API endpoints
- `services/fuseki-job/main.py` - Current Fuseki job processing
- `ontology/emo_ontology.ttl` - Current OWL ontology
- `config/kg_config.py` - Knowledge graph configuration
- `docs/knowledge_graph_design.md` - KG design documentation
- `tests/unit/test_knowledge_graph.py` - Existing KG tests
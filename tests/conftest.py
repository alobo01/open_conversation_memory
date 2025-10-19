import pytest
import sys
from unittest.mock import Mock, MagicMock, AsyncMock

# Mock heavy ML dependencies before any imports
sys.modules['vllm'] = Mock()
sys.modules['torch'] = Mock()
sys.modules['transformers'] = Mock()
sys.modules['whisper'] = Mock()
sys.modules['faster_whisper'] = Mock()
sys.modules['sentence_transformers'] = Mock()
sys.modules['qdrant_client'] = Mock()
sys.modules['qdrant_client.models'] = Mock()
sys.modules['motor'] = Mock()
sys.modules['motor.motor_asyncio'] = Mock()
sys.modules['SPARQLWrapper'] = Mock()
sys.modules['rdflib'] = Mock()
sys.modules['pyshacl'] = Mock()
sys.modules['pymongo'] = Mock()

# Configure specific mocks
torch_mock = sys.modules['torch']
torch_mock.cuda = Mock()
torch_mock.cuda.is_available = Mock(return_value=False)

transformers_mock = sys.modules['transformers']
transformers_mock.AutoTokenizer = Mock()
transformers_mock.AutoModelForCausalLM = Mock()

sentence_transformers_mock = sys.modules['sentence_transformers']
sentence_transformers_mock.SentenceTransformer = Mock()

# Mock Qdrant client and models
qdrant_mock = sys.modules['qdrant_client']
qdrant_client_class = Mock()
qdrant_client_class.return_value = Mock()
qdrant_mock.QdrantClient = qdrant_client_class

# Configure proper Qdrant client mock with collections response
mock_collections_response = Mock()
mock_collections_response.collections = []
qdrant_client_class.return_value.get_collections.return_value = mock_collections_response

qdrant_models_mock = sys.modules['qdrant_client.models']
qdrant_models_mock.PointStruct = Mock()
qdrant_models_mock.Filter = Mock()
qdrant_models_mock.FieldCondition = Mock()
qdrant_models_mock.MatchValue = Mock()

# Mock SentenceTransformer
sentence_transformers_mock = sys.modules['sentence_transformers']
sentence_transformers_mock.SentenceTransformer = Mock()
sentence_transformers_mock.SentenceTransformer.return_value = Mock()
sentence_transformers_mock.SentenceTransformer.return_value.encode = Mock(return_value=[0.1] * 384)

# Mock MongoDB
motor_mock = sys.modules['motor']
motor_asyncio_mock = Mock()
motor_asyncio_mock.AsyncIOMotorClient = Mock()
motor_mock.motor_asyncio = motor_asyncio_mock

# Mock SPARQLWrapper
sparql_mock = sys.modules['SPARQLWrapper']
sparql_mock.SPARQLWrapper = Mock()
sparql_mock.JSON = Mock()

# Mock RDFlib
rdflib_mock = sys.modules['rdflib']
rdflib_mock.Graph = Mock()
rdflib_mock.Namespace = Mock()
rdflib_mock.URIRef = Mock()
rdflib_mock.Literal = Mock()

# Mock rdflib.namespace
rdflib_namespace_mock = Mock()
rdflib_namespace_mock.RDF = Mock()
rdflib_namespace_mock.RDFS = Mock()
rdflib_namespace_mock.XSD = Mock()
rdflib_namespace_mock.OWL = Mock()
sys.modules['rdflib.namespace'] = rdflib_namespace_mock

# Mock PySHACL
pyshacl_mock = sys.modules['pyshacl']
pyshacl_mock.validate = Mock()

@pytest.fixture(scope="session")
def mock_heavy_dependencies():
    """Ensure all heavy dependencies are mocked"""
    pass

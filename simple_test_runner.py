#!/usr/bin/env python3
"""
Simple test runner for EmoRobCare that bypasses heavy ML dependencies
"""
import os
import sys
import subprocess
import importlib.util
from pathlib import Path

def create_test_conftest():
    """Create a conftest.py file with proper mocks for heavy dependencies"""
    conftest_content = '''import pytest
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
'''

    with open('tests/conftest.py', 'w') as f:
        f.write(conftest_content)

def check_python_version():
    """Check if Python is available and get version"""
    try:
        result = subprocess.run([sys.executable, '--version'],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"[OK] Python available: {result.stdout.strip()}")
            return True
        else:
            print("[FAIL] Python not available")
            return False
    except Exception as e:
        print(f"[FAIL] Error checking Python: {e}")
        return False

def install_test_dependencies():
    """Install test dependencies"""
    test_deps = [
        'pytest>=8.0.0',
        'pytest-mock>=3.12.0',
        'pytest-asyncio>=0.21.0',
        'fastapi>=0.104.1',
        'pydantic>=2.5.0',
        'pydantic-settings>=2.0.0',
        'python-multipart>=0.0.6',
        'python-dotenv>=1.0.0',
        'aiofiles>=23.2.0',
        'jinja2>=3.1.2',
        'httpx>=0.25.0',
        'numpy>=1.24.0',
        'scipy>=1.11.0',
        'qdrant-client>=1.7.0',
        'pymongo>=4.6.0',
        'motor>=3.3.0',
        'sparqlwrapper>=2.0.0',
        'rdflib>=7.0.0',
        'pyshacl>=0.20.0'
    ]

    print("[INSTALL] Installing test dependencies...")
    for dep in test_deps:
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'install', dep],
                                  capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                print(f"[OK] Installed {dep}")
            else:
                print(f"[FAIL] Failed to install {dep}: {result.stderr}")
        except Exception as e:
            print(f"[FAIL] Error installing {dep}: {e}")

def run_single_test_file(test_file):
    """Run a single test file"""
    print(f"[TEST] Running {test_file}...")

    try:
        result = subprocess.run([
            sys.executable, '-m', 'pytest',
            test_file, '-v', '--tb=short', '-x'
        ], capture_output=True, text=True, timeout=120)

        print(f"Exit code: {result.returncode}")
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print(f"[FAIL] Test {test_file} timed out")
        return False
    except Exception as e:
        print(f"[FAIL] Error running {test_file}: {e}")
        return False

def main():
    """Main test runner"""
    print("EmoRobCare Simple Test Runner")
    print("=" * 50)

    # Check Python availability
    if not check_python_version():
        return 1

    # Create conftest.py with mocks
    print("\n[SETUP] Setting up test environment...")
    create_test_conftest()
    print("[OK] Created tests/conftest.py with heavy dependency mocks")

    # Install test dependencies
    install_test_dependencies()

    # Find test files
    test_files = []
    for pattern in ['tests/unit/test_*.py', 'tests/e2e/test_*.py']:
        test_files.extend(Path('.').glob(pattern))

    print(f"\n[INFO] Found {len(test_files)} test files:")
    for test_file in test_files:
        print(f"  - {test_file}")

    # Run tests one by one
    print(f"\n[RUNNING] Running tests...")
    passed = 0
    failed = 0

    for test_file in sorted(test_files):
        if run_single_test_file(str(test_file)):
            passed += 1
            print(f"[PASS] {test_file.name} PASSED")
        else:
            failed += 1
            print(f"[FAIL] {test_file.name} FAILED")
        print("-" * 40)

    # Summary
    print(f"\n[SUMMARY] Test Summary:")
    print(f"Total: {len(test_files)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed == 0:
        print("[SUCCESS] All tests passed!")
        return 0
    else:
        print("[WARNING] Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
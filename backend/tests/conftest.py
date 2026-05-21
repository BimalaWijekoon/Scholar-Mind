"""
Test Configuration and Fixtures
"""

import pytest
import asyncio
from typing import Generator, AsyncGenerator
from unittest.mock import MagicMock, AsyncMock
import tempfile
import os


# Configure pytest-asyncio
pytest_plugins = ["pytest_asyncio"]


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_text() -> str:
    """Sample text for testing."""
    return """
    Machine learning is a subset of artificial intelligence (AI) that focuses on 
    building systems that learn from data. Deep learning uses neural networks with 
    multiple layers. Researchers at Stanford University have made significant advances 
    in natural language processing. The protein p53 plays a crucial role in cancer 
    prevention. Dr. Jane Smith published her findings in Nature journal.
    """


@pytest.fixture
def sample_pdf_path(temp_dir: str) -> str:
    """Create a sample PDF file for testing."""
    pdf_path = os.path.join(temp_dir, "sample.pdf")
    
    # Create a minimal PDF file for testing
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
100 700 Td
(Test document) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<< /Size 5 /Root 1 0 R >>
startxref
300
%%EOF"""
    
    with open(pdf_path, "wb") as f:
        f.write(pdf_content)
    
    return pdf_path


@pytest.fixture
def mock_llm() -> MagicMock:
    """Create a mock LLM for testing."""
    mock = MagicMock()
    mock.invoke.return_value = MagicMock(content="This is a test response.")
    return mock


@pytest.fixture
def mock_embeddings() -> MagicMock:
    """Create mock embeddings model."""
    import numpy as np
    
    mock = MagicMock()
    mock.encode.return_value = np.random.rand(384).astype(np.float32)
    return mock


@pytest.fixture
def mock_neo4j_client() -> AsyncMock:
    """Create a mock Neo4j client."""
    mock = AsyncMock()
    mock.connect.return_value = None
    mock.close.return_value = None
    mock.create_node.return_value = "node-1"
    mock.create_relationship.return_value = True
    mock.get_node.return_value = {"id": "node-1", "text": "Test", "labels": ["Entity"]}
    mock.get_neighbors.return_value = []
    mock.find_nodes.return_value = []
    mock.get_statistics.return_value = {"node_count": 10, "relationship_count": 5}
    return mock


@pytest.fixture
def mock_vector_store() -> MagicMock:
    """Create a mock vector store."""
    mock = MagicMock()
    mock.add.return_value = ["id-1", "id-2"]
    mock.search.return_value = [
        MagicMock(id="id-1", text="Test result 1", score=0.9),
        MagicMock(id="id-2", text="Test result 2", score=0.8),
    ]
    mock.delete.return_value = True
    return mock


@pytest.fixture
def sample_entities() -> list:
    """Sample entities for testing."""
    return [
        {"text": "machine learning", "entity_type": "CONCEPT", "confidence": 0.95},
        {"text": "Stanford University", "entity_type": "ORGANIZATION", "confidence": 0.98},
        {"text": "Dr. Jane Smith", "entity_type": "PERSON", "confidence": 0.92},
        {"text": "p53", "entity_type": "PROTEIN", "confidence": 0.88},
        {"text": "Nature", "entity_type": "ORGANIZATION", "confidence": 0.85},
    ]


@pytest.fixture
def sample_relations() -> list:
    """Sample relations for testing."""
    return [
        {
            "source_text": "Dr. Jane Smith",
            "source_type": "PERSON",
            "target_text": "Nature",
            "target_type": "ORGANIZATION",
            "relation_type": "PUBLISHED_IN",
            "confidence": 0.85,
        },
        {
            "source_text": "Stanford University",
            "source_type": "ORGANIZATION",
            "target_text": "natural language processing",
            "target_type": "CONCEPT",
            "relation_type": "RESEARCHES",
            "confidence": 0.80,
        },
    ]


@pytest.fixture
def mock_settings() -> MagicMock:
    """Create mock settings."""
    mock = MagicMock()
    mock.neo4j_uri = "bolt://localhost:7687"
    mock.neo4j_user = "neo4j"
    mock.neo4j_password = "password"
    mock.database_url = "postgresql+asyncpg://localhost/test"
    mock.redis_url = "redis://localhost:6379/0"
    mock.google_api_key = "test-api-key"
    mock.embedding_model = "all-MiniLM-L6-v2"
    mock.chunk_size = 512
    mock.chunk_overlap = 50
    mock.vector_store_type = "chroma"
    return mock


# Test client fixture for FastAPI
@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    from fastapi.testclient import TestClient
    from backend.main import app
    
    return TestClient(app)


@pytest.fixture
async def async_test_client():
    """Create an async test client for the FastAPI app."""
    from httpx import AsyncClient, ASGITransport
    from backend.main import app
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


class MockSpacyDoc:
    """Mock spaCy Doc object for testing."""
    
    def __init__(self, text: str, ents: list = None):
        self.text = text
        self.ents = ents or []
        self.sents = [self]
    
    def __iter__(self):
        return iter([])


class MockSpacyNLP:
    """Mock spaCy NLP pipeline."""
    
    def __call__(self, text: str) -> MockSpacyDoc:
        # Create some mock entities
        ents = [
            MagicMock(
                text="machine learning",
                label_="CONCEPT",
                start_char=0,
                end_char=16,
            ),
        ]
        return MockSpacyDoc(text, ents)


@pytest.fixture
def mock_spacy() -> MockSpacyNLP:
    """Create a mock spaCy pipeline."""
    return MockSpacyNLP()

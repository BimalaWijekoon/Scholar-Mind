"""
API Dependency Injection
"""

from typing import AsyncGenerator
from functools import lru_cache

from backend.config import settings
from backend.core.knowledge_graph.neo4j_client import Neo4jClient
from backend.core.retrieval.vector_store import VectorStore
from backend.services.document_service import DocumentService
from backend.services.query_service import QueryService
from backend.services.graph_service import GraphService


# Dependency providers
async def get_neo4j_client() -> AsyncGenerator[Neo4jClient, None]:
    """Get Neo4j client instance."""
    client = Neo4jClient(
        uri=settings.NEO4J_URI,
        user=settings.NEO4J_USER,
        password=settings.NEO4J_PASSWORD,
    )
    try:
        yield client
    finally:
        await client.close()


@lru_cache()
def get_vector_store() -> VectorStore:
    """Get vector store instance (cached singleton)."""
    return VectorStore(
        db_type=settings.VECTOR_STORE_TYPE,
        collection_name=settings.CHROMA_COLLECTION_NAME,
        persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
    )


@lru_cache()
def get_document_service() -> DocumentService:
    """Get document service instance (cached singleton).
    
    IMPORTANT: lru_cache ensures ML models (spaCy, sentence-transformers)
    are loaded only ONCE at first request, not on every request.
    Without this, every API call would re-load ~500MB of models.
    """
    return DocumentService()


@lru_cache()
def get_query_service() -> QueryService:
    """Get query service instance (cached singleton)."""
    return QueryService()


@lru_cache()
def get_graph_service() -> GraphService:
    """Get graph service instance (cached singleton)."""
    return GraphService()

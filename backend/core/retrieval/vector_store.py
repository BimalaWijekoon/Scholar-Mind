"""
Vector Store - Manage vector embeddings with ChromaDB and Qdrant
"""

from typing import List, Dict, Optional, Any, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import uuid


class VectorDBType(str, Enum):
    """Supported vector database types."""
    CHROMA = "chroma"
    QDRANT = "qdrant"


@dataclass
class VectorSearchResult:
    """Result from vector search."""
    id: str
    text: str
    score: float
    metadata: Dict


class VectorStore:
    """
    Vector store for managing embeddings.
    
    Supports:
    - ChromaDB (local/persistent)
    - Qdrant (local/cloud)
    """
    
    def __init__(
        self,
        db_type: VectorDBType = VectorDBType.CHROMA,
        collection_name: str = "documents",
        persist_directory: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        api_key: Optional[str] = None,
    ):
        """
        Initialize the vector store.
        
        Args:
            db_type: Type of vector database
            collection_name: Name of the collection
            persist_directory: Directory for persistent storage
            host: Host for remote database
            port: Port for remote database
            api_key: API key for cloud database
        """
        self.db_type = db_type
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        
        self._client = None
        self._collection = None
        
        if db_type == VectorDBType.CHROMA:
            self._init_chroma(persist_directory)
        elif db_type == VectorDBType.QDRANT:
            self._init_qdrant(host, port, api_key)
    
    def _init_chroma(self, persist_directory: Optional[str]) -> None:
        """Initialize ChromaDB."""
        import chromadb
        
        if persist_directory:
            # Create directory if it doesn't exist
            import os
            os.makedirs(persist_directory, exist_ok=True)
            # Use PersistentClient for newer ChromaDB versions
            try:
                self._client = chromadb.PersistentClient(path=persist_directory)
            except AttributeError:
                # Fallback for older versions
                from chromadb.config import Settings
                self._client = chromadb.Client(Settings(
                    chroma_db_impl="duckdb+parquet",
                    persist_directory=persist_directory,
                    anonymized_telemetry=False,
                ))
        else:
            self._client = chromadb.Client()
        
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
    
    def _init_qdrant(
        self,
        host: Optional[str],
        port: Optional[int],
        api_key: Optional[str],
    ) -> None:
        """Initialize Qdrant."""
        from qdrant_client import QdrantClient
        from qdrant_client.models import VectorParams, Distance
        
        if host and api_key:
            # Cloud Qdrant
            self._client = QdrantClient(url=host, api_key=api_key)
        elif host:
            # Self-hosted Qdrant
            self._client = QdrantClient(host=host, port=port or 6333)
        else:
            # In-memory Qdrant
            self._client = QdrantClient(":memory:")
        
        # Create collection if not exists
        collections = self._client.get_collections().collections
        if not any(c.name == self.collection_name for c in collections):
            self._client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=384,  # Default for all-MiniLM-L6-v2
                    distance=Distance.COSINE,
                ),
            )
    
    def add(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict]] = None,
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Add documents to the vector store.
        
        Args:
            texts: Document texts
            embeddings: Document embeddings
            metadatas: Optional metadata for each document
            ids: Optional IDs for each document
            
        Returns:
            List of document IDs
        """
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in texts]
        
        if metadatas is None:
            metadatas = [{} for _ in texts]
        
        if self.db_type == VectorDBType.CHROMA:
            self._collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=ids,
            )
        elif self.db_type == VectorDBType.QDRANT:
            from qdrant_client.models import PointStruct
            
            points = [
                PointStruct(
                    id=i,
                    vector=emb,
                    payload={"text": text, **meta, "_id": doc_id},
                )
                for i, (doc_id, text, emb, meta) in enumerate(zip(ids, texts, embeddings, metadatas))
            ]
            
            self._client.upsert(
                collection_name=self.collection_name,
                points=points,
            )
        
        return ids
    
    def search(
        self,
        query_embedding: List[float],
        k: int = 10,
        filter_metadata: Optional[Dict] = None,
    ) -> List[VectorSearchResult]:
        """
        Search for similar documents.
        
        Args:
            query_embedding: Query vector
            k: Number of results
            filter_metadata: Optional metadata filter
            
        Returns:
            List of search results
        """
        if self.db_type == VectorDBType.CHROMA:
            return self._search_chroma(query_embedding, k, filter_metadata)
        elif self.db_type == VectorDBType.QDRANT:
            return self._search_qdrant(query_embedding, k, filter_metadata)
        
        return []
    
    def _search_chroma(
        self,
        query_embedding: List[float],
        k: int,
        filter_metadata: Optional[Dict],
    ) -> List[VectorSearchResult]:
        """Search ChromaDB."""
        where = filter_metadata if filter_metadata else None
        
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        
        search_results = []
        
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                # ChromaDB returns distances, convert to similarity
                distance = results["distances"][0][i] if results["distances"] else 0
                score = 1 - distance  # Cosine similarity
                
                search_results.append(VectorSearchResult(
                    id=doc_id,
                    text=results["documents"][0][i] if results["documents"] else "",
                    score=score,
                    metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                ))
        
        return search_results
    
    def _search_qdrant(
        self,
        query_embedding: List[float],
        k: int,
        filter_metadata: Optional[Dict],
    ) -> List[VectorSearchResult]:
        """Search Qdrant."""
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        query_filter = None
        if filter_metadata:
            conditions = [
                FieldCondition(key=key, match=MatchValue(value=value))
                for key, value in filter_metadata.items()
            ]
            query_filter = Filter(must=conditions)
        
        results = self._client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=k,
            query_filter=query_filter,
        )
        
        search_results = []
        for result in results:
            payload = result.payload or {}
            search_results.append(VectorSearchResult(
                id=payload.get("_id", str(result.id)),
                text=payload.get("text", ""),
                score=result.score,
                metadata={k: v for k, v in payload.items() if k not in ["text", "_id"]},
            ))
        
        return search_results
    
    def delete(self, ids: List[str]) -> None:
        """
        Delete documents by ID.
        
        Args:
            ids: Document IDs to delete
        """
        if self.db_type == VectorDBType.CHROMA:
            self._collection.delete(ids=ids)
        elif self.db_type == VectorDBType.QDRANT:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            self._client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(key="_id", match=MatchValue(value=doc_id))
                        for doc_id in ids
                    ]
                ),
            )
    
    def get_count(self) -> int:
        """Get the number of documents in the store."""
        if self.db_type == VectorDBType.CHROMA:
            return self._collection.count()
        elif self.db_type == VectorDBType.QDRANT:
            info = self._client.get_collection(self.collection_name)
            return info.points_count
        return 0
    
    def clear(self) -> None:
        """Clear all documents from the store."""
        if self.db_type == VectorDBType.CHROMA:
            # Delete and recreate collection
            self._client.delete_collection(self.collection_name)
            self._collection = self._client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        elif self.db_type == VectorDBType.QDRANT:
            self._client.delete_collection(self.collection_name)
            from qdrant_client.models import VectorParams, Distance
            self._client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
    
    def persist(self) -> None:
        """Persist data to disk (if applicable)."""
        if self.db_type == VectorDBType.CHROMA and hasattr(self._client, 'persist'):
            self._client.persist()

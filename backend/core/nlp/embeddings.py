"""
Embeddings Manager - Generate and manage text embeddings
"""

import numpy as np
from typing import List, Dict, Optional, Union, Tuple
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer
import torch


@dataclass
class EmbeddingResult:
    """Represents an embedding result."""
    text: str
    embedding: np.ndarray
    model: str
    dimension: int


class EmbeddingsManager:
    """
    Manager for text embeddings using sentence-transformers.
    
    Supports:
    - Multiple embedding models
    - Batch processing
    - Caching
    """
    
    DEFAULT_MODEL = "all-MiniLM-L6-v2"
    SCIENTIFIC_MODEL = "allenai/scibert_scivocab_uncased"
    
    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        device: Optional[str] = None,
        use_cache: bool = True,
    ):
        """
        Initialize the embeddings manager.
        
        Args:
            model_name: Name of the sentence-transformers model
            device: Device to use ('cpu', 'cuda', or None for auto)
            use_cache: Whether to cache embeddings
        """
        self.model_name = model_name
        
        # Determine device
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device
        
        # Load model
        self.model = SentenceTransformer(model_name, device=device)
        self.dimension = self.model.get_sentence_embedding_dimension()
        
        # Optional cache
        self.use_cache = use_cache
        self._cache: Dict[str, np.ndarray] = {}
    
    def embed(self, text: str) -> EmbeddingResult:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            EmbeddingResult with embedding vector
        """
        # Check cache
        if self.use_cache and text in self._cache:
            embedding = self._cache[text]
        else:
            embedding = self.model.encode(text, convert_to_numpy=True)
            
            if self.use_cache:
                self._cache[text] = embedding
        
        return EmbeddingResult(
            text=text,
            embedding=embedding,
            model=self.model_name,
            dimension=self.dimension,
        )
    
    def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = False,
    ) -> List[EmbeddingResult]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
            show_progress: Whether to show progress bar
            
        Returns:
            List of EmbeddingResult objects
        """
        # Check cache for existing embeddings
        cached_indices = []
        uncached_texts = []
        uncached_indices = []
        
        for i, text in enumerate(texts):
            if self.use_cache and text in self._cache:
                cached_indices.append(i)
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        # Generate embeddings for uncached texts
        if uncached_texts:
            embeddings = self.model.encode(
                uncached_texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True,
            )
            
            # Update cache
            if self.use_cache:
                for text, emb in zip(uncached_texts, embeddings):
                    self._cache[text] = emb
        
        # Build results
        results = [None] * len(texts)
        
        for idx in cached_indices:
            text = texts[idx]
            results[idx] = EmbeddingResult(
                text=text,
                embedding=self._cache[text],
                model=self.model_name,
                dimension=self.dimension,
            )
        
        for i, idx in enumerate(uncached_indices):
            text = texts[idx]
            results[idx] = EmbeddingResult(
                text=text,
                embedding=embeddings[i],
                model=self.model_name,
                dimension=self.dimension,
            )
        
        return results
    
    def embed_query(self, query: str) -> np.ndarray:
        """
        Generate embedding for a query (optimized for similarity search).
        
        Args:
            query: Query text
            
        Returns:
            Embedding vector as numpy array
        """
        return self.model.encode(query, convert_to_numpy=True)
    
    def embed_documents(
        self,
        documents: List[str],
        batch_size: int = 32,
    ) -> np.ndarray:
        """
        Generate embeddings for documents (optimized for indexing).
        
        Args:
            documents: List of document texts
            batch_size: Batch size
            
        Returns:
            2D numpy array of embeddings (num_docs x dimension)
        """
        return self.model.encode(
            documents,
            batch_size=batch_size,
            convert_to_numpy=True,
        )
    
    def similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray,
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Cosine similarity score (0-1)
        """
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(np.dot(embedding1, embedding2) / (norm1 * norm2))
    
    def find_similar(
        self,
        query_embedding: np.ndarray,
        document_embeddings: np.ndarray,
        top_k: int = 10,
    ) -> List[Tuple[int, float]]:
        """
        Find most similar documents to a query.
        
        Args:
            query_embedding: Query embedding vector
            document_embeddings: Document embeddings matrix
            top_k: Number of results to return
            
        Returns:
            List of (index, similarity_score) tuples
        """
        # Normalize
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        doc_norms = document_embeddings / np.linalg.norm(
            document_embeddings, axis=1, keepdims=True
        )
        
        # Calculate similarities
        similarities = np.dot(doc_norms, query_norm)
        
        # Get top k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        return [(int(idx), float(similarities[idx])) for idx in top_indices]
    
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self.dimension
    
    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        self._cache.clear()
    
    def change_model(self, model_name: str) -> None:
        """
        Change the embedding model.
        
        Args:
            model_name: New model name
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name, device=self.device)
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.clear_cache()

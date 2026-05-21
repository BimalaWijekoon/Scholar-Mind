"""
Hybrid Retriever - Combine keyword and semantic search
"""

from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import re
import math
from collections import defaultdict


class RetrievalMode(str, Enum):
    """Retrieval mode options."""
    KEYWORD = "keyword"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


@dataclass
class RetrievalResult:
    """Result from retrieval."""
    id: str
    text: str
    score: float
    source: str
    metadata: Dict


class HybridRetriever:
    """
    Hybrid retriever combining keyword and semantic search.
    
    Supports:
    - BM25 keyword search
    - Vector semantic search
    - Reciprocal Rank Fusion (RRF)
    """
    
    def __init__(
        self,
        vector_store=None,
        embeddings_manager=None,
        alpha: float = 0.5,
        use_bm25: bool = True,
    ):
        """
        Initialize the hybrid retriever.
        
        Args:
            vector_store: Vector store for semantic search
            embeddings_manager: Embeddings manager
            alpha: Weight for semantic search (1-alpha for keyword)
            use_bm25: Whether to use BM25 for keyword search
        """
        self.vector_store = vector_store
        self.embeddings_manager = embeddings_manager
        self.alpha = alpha
        self.use_bm25 = use_bm25
        
        # Document index for keyword search
        self._documents: Dict[str, str] = {}
        self._doc_metadata: Dict[str, Dict] = {}
        self._inverted_index: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
        
        # BM25 parameters
        self.k1 = 1.5
        self.b = 0.75
        self._avg_doc_length = 0
        self._doc_lengths: Dict[str, int] = {}
    
    def add_documents(
        self,
        documents: List[Dict[str, Any]],
    ) -> None:
        """
        Add documents to the retriever.
        
        Args:
            documents: List of document dicts with 'id', 'text', and optional 'metadata'
        """
        for doc in documents:
            doc_id = doc["id"]
            text = doc["text"]
            metadata = doc.get("metadata", {})
            
            # Store document
            self._documents[doc_id] = text
            self._doc_metadata[doc_id] = metadata
            
            # Build inverted index
            tokens = self._tokenize(text)
            self._doc_lengths[doc_id] = len(tokens)
            
            # Count term frequencies
            term_freq = defaultdict(int)
            for token in tokens:
                term_freq[token] += 1
            
            # Add to inverted index
            for term, freq in term_freq.items():
                self._inverted_index[term].append((doc_id, freq))
        
        # Update average document length
        if self._doc_lengths:
            self._avg_doc_length = sum(self._doc_lengths.values()) / len(self._doc_lengths)
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text for keyword search."""
        # Simple tokenization: lowercase, split on non-alphanumeric
        text = text.lower()
        tokens = re.findall(r'\b\w+\b', text)
        return tokens
    
    def retrieve(
        self,
        query: str,
        k: int = 10,
        mode: RetrievalMode = RetrievalMode.HYBRID,
        filter_metadata: Optional[Dict] = None,
    ) -> List[RetrievalResult]:
        """
        Retrieve relevant documents.
        
        Args:
            query: Search query
            k: Number of results
            mode: Retrieval mode
            filter_metadata: Optional metadata filter
            
        Returns:
            List of retrieval results
        """
        if mode == RetrievalMode.KEYWORD:
            return self._keyword_search(query, k, filter_metadata)
        elif mode == RetrievalMode.SEMANTIC:
            return self._semantic_search(query, k, filter_metadata)
        else:
            return self._hybrid_search(query, k, filter_metadata)
    
    def _keyword_search(
        self,
        query: str,
        k: int,
        filter_metadata: Optional[Dict],
    ) -> List[RetrievalResult]:
        """Perform keyword search using BM25."""
        query_tokens = self._tokenize(query)
        
        if not query_tokens:
            return []
        
        # Calculate BM25 scores
        scores = defaultdict(float)
        N = len(self._documents)
        
        for token in query_tokens:
            if token not in self._inverted_index:
                continue
            
            posting_list = self._inverted_index[token]
            n = len(posting_list)
            
            # IDF component
            idf = max(0, (N - n + 0.5) / (n + 0.5))
            idf = math.log(1 + idf)
            
            for doc_id, tf in posting_list:
                # Skip if doesn't match filter
                if filter_metadata:
                    doc_meta = self._doc_metadata.get(doc_id, {})
                    if not all(doc_meta.get(k) == v for k, v in filter_metadata.items()):
                        continue
                
                doc_length = self._doc_lengths.get(doc_id, 0)
                
                # TF component with length normalization
                if self._avg_doc_length > 0:
                    tf_norm = (tf * (self.k1 + 1)) / (
                        tf + self.k1 * (1 - self.b + self.b * doc_length / self._avg_doc_length)
                    )
                else:
                    tf_norm = tf
                
                scores[doc_id] += idf * tf_norm
        
        # Sort and return top k
        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]
        
        results = []
        for doc_id, score in sorted_docs:
            results.append(RetrievalResult(
                id=doc_id,
                text=self._documents.get(doc_id, ""),
                score=score,
                source="keyword",
                metadata=self._doc_metadata.get(doc_id, {}),
            ))
        
        return results
    
    def _semantic_search(
        self,
        query: str,
        k: int,
        filter_metadata: Optional[Dict],
    ) -> List[RetrievalResult]:
        """Perform semantic search using vector store."""
        if not self.vector_store or not self.embeddings_manager:
            return []
        
        # Generate query embedding
        query_embedding = self.embeddings_manager.embed_query(query)
        
        # Search vector store
        vector_results = self.vector_store.search(
            query_embedding=query_embedding.tolist(),
            k=k,
            filter_metadata=filter_metadata,
        )
        
        results = []
        for vr in vector_results:
            results.append(RetrievalResult(
                id=vr.id,
                text=vr.text,
                score=vr.score,
                source="semantic",
                metadata=vr.metadata,
            ))
        
        return results
    
    def _hybrid_search(
        self,
        query: str,
        k: int,
        filter_metadata: Optional[Dict],
    ) -> List[RetrievalResult]:
        """Perform hybrid search using RRF fusion."""
        # Get results from both methods
        keyword_results = self._keyword_search(query, k * 2, filter_metadata)
        semantic_results = self._semantic_search(query, k * 2, filter_metadata)
        
        # Combine using Reciprocal Rank Fusion
        rrf_scores = defaultdict(float)
        result_map = {}
        
        rrf_k = 60  # RRF constant
        
        # Add keyword results
        for rank, result in enumerate(keyword_results):
            rrf_scores[result.id] += (1 - self.alpha) / (rrf_k + rank + 1)
            result_map[result.id] = result
        
        # Add semantic results
        for rank, result in enumerate(semantic_results):
            rrf_scores[result.id] += self.alpha / (rrf_k + rank + 1)
            if result.id not in result_map:
                result_map[result.id] = result
        
        # Sort by RRF score
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)[:k]
        
        results = []
        for doc_id in sorted_ids:
            original = result_map[doc_id]
            results.append(RetrievalResult(
                id=doc_id,
                text=original.text,
                score=rrf_scores[doc_id],
                source="hybrid",
                metadata=original.metadata,
            ))
        
        return results
    
    def set_alpha(self, alpha: float) -> None:
        """
        Set the semantic search weight.
        
        Args:
            alpha: Weight (0-1), higher means more semantic
        """
        self.alpha = max(0, min(1, alpha))
    
    def clear(self) -> None:
        """Clear all documents."""
        self._documents.clear()
        self._doc_metadata.clear()
        self._inverted_index.clear()
        self._doc_lengths.clear()
        self._avg_doc_length = 0

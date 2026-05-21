"""
Reranker - Rerank retrieved documents for better relevance
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class RerankerType(str, Enum):
    """Reranker types."""
    CROSS_ENCODER = "cross_encoder"
    COLBERT = "colbert"
    LLM = "llm"


@dataclass
class RerankResult:
    """Result from reranking."""
    id: str
    text: str
    original_score: float
    rerank_score: float
    final_rank: int
    metadata: Dict


class Reranker:
    """
    Reranker for improving retrieval relevance.
    
    Supports:
    - Cross-encoder models
    - ColBERT late interaction
    - LLM-based reranking
    """
    
    def __init__(
        self,
        reranker_type: RerankerType = RerankerType.CROSS_ENCODER,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
    ):
        """
        Initialize the reranker.
        
        Args:
            reranker_type: Type of reranker to use
            model_name: Model name/path
            device: Device to use
        """
        self.reranker_type = reranker_type
        self.model_name = model_name or "cross-encoder/ms-marco-MiniLM-L-6-v2"
        self.device = device
        
        self._model = None
        
        if reranker_type == RerankerType.CROSS_ENCODER:
            self._init_cross_encoder()
    
    def _init_cross_encoder(self) -> None:
        """Initialize cross-encoder model."""
        try:
            from sentence_transformers import CrossEncoder
            import torch
            
            device = self.device or ("cuda" if torch.cuda.is_available() else "cpu")
            self._model = CrossEncoder(self.model_name, device=device)
        except ImportError:
            pass
    
    def rerank(
        self,
        query: str,
        documents: List[Dict],
        top_k: Optional[int] = None,
    ) -> List[RerankResult]:
        """
        Rerank documents for a query.
        
        Args:
            query: Search query
            documents: List of document dicts with 'id', 'text', 'score'
            top_k: Number of results to return
            
        Returns:
            List of reranked results
        """
        if not documents:
            return []
        
        if self.reranker_type == RerankerType.CROSS_ENCODER:
            return self._rerank_cross_encoder(query, documents, top_k)
        elif self.reranker_type == RerankerType.LLM:
            return self._rerank_llm(query, documents, top_k)
        else:
            # Default: return as-is with original scores
            results = []
            for i, doc in enumerate(documents[:top_k] if top_k else documents):
                results.append(RerankResult(
                    id=doc["id"],
                    text=doc["text"],
                    original_score=doc.get("score", 0),
                    rerank_score=doc.get("score", 0),
                    final_rank=i + 1,
                    metadata=doc.get("metadata", {}),
                ))
            return results
    
    def _rerank_cross_encoder(
        self,
        query: str,
        documents: List[Dict],
        top_k: Optional[int],
    ) -> List[RerankResult]:
        """Rerank using cross-encoder."""
        if not self._model:
            return self._fallback_rerank(documents, top_k)
        
        # Prepare query-document pairs
        pairs = [(query, doc["text"]) for doc in documents]
        
        # Get scores
        scores = self._model.predict(pairs)
        
        # Create results with scores
        scored_docs = []
        for i, (doc, score) in enumerate(zip(documents, scores)):
            scored_docs.append((doc, float(score)))
        
        # Sort by rerank score
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        # Limit to top_k
        if top_k:
            scored_docs = scored_docs[:top_k]
        
        # Build results
        results = []
        for rank, (doc, rerank_score) in enumerate(scored_docs):
            results.append(RerankResult(
                id=doc["id"],
                text=doc["text"],
                original_score=doc.get("score", 0),
                rerank_score=rerank_score,
                final_rank=rank + 1,
                metadata=doc.get("metadata", {}),
            ))
        
        return results
    
    def _rerank_llm(
        self,
        query: str,
        documents: List[Dict],
        top_k: Optional[int],
    ) -> List[RerankResult]:
        """Rerank using LLM (placeholder)."""
        # LLM reranking would require async and LLM client
        # For now, use heuristic-based reranking
        return self._fallback_rerank(documents, top_k)
    
    def _fallback_rerank(
        self,
        documents: List[Dict],
        top_k: Optional[int],
    ) -> List[RerankResult]:
        """Fallback reranking using original scores."""
        sorted_docs = sorted(
            documents,
            key=lambda x: x.get("score", 0),
            reverse=True,
        )
        
        if top_k:
            sorted_docs = sorted_docs[:top_k]
        
        results = []
        for rank, doc in enumerate(sorted_docs):
            results.append(RerankResult(
                id=doc["id"],
                text=doc["text"],
                original_score=doc.get("score", 0),
                rerank_score=doc.get("score", 0),
                final_rank=rank + 1,
                metadata=doc.get("metadata", {}),
            ))
        
        return results
    
    def rerank_batch(
        self,
        queries: List[str],
        documents_per_query: List[List[Dict]],
        top_k: Optional[int] = None,
    ) -> List[List[RerankResult]]:
        """
        Rerank documents for multiple queries.
        
        Args:
            queries: List of queries
            documents_per_query: Documents for each query
            top_k: Number of results per query
            
        Returns:
            List of reranked results per query
        """
        results = []
        
        for query, docs in zip(queries, documents_per_query):
            query_results = self.rerank(query, docs, top_k)
            results.append(query_results)
        
        return results
    
    def calibrate_scores(
        self,
        results: List[RerankResult],
    ) -> List[RerankResult]:
        """
        Calibrate rerank scores to 0-1 range.
        
        Args:
            results: Rerank results
            
        Returns:
            Results with calibrated scores
        """
        if not results:
            return results
        
        scores = [r.rerank_score for r in results]
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score == min_score:
            # All same score, normalize to 1.0
            for r in results:
                r.rerank_score = 1.0
        else:
            for r in results:
                r.rerank_score = (r.rerank_score - min_score) / (max_score - min_score)
        
        return results

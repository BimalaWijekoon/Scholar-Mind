"""
Paper Recommendation System - Recommend related papers based on content and graph

This module provides paper recommendations using:
- Content-based similarity
- Graph-based connections
- Citation patterns
- User reading history
"""

from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from enum import Enum
import numpy as np
from collections import defaultdict


class RecommendationType(str, Enum):
    """Types of recommendation sources."""
    CONTENT = "content"  # Based on text similarity
    CITATION = "citation"  # Based on citation network
    AUTHOR = "author"  # Same authors
    TOPIC = "topic"  # Same topics/entities
    GRAPH = "graph"  # Graph neighborhood
    HYBRID = "hybrid"  # Combination of above


@dataclass
class Recommendation:
    """Represents a paper recommendation."""
    document_id: str
    title: str
    score: float
    recommendation_type: RecommendationType
    reasons: List[str]
    shared_entities: List[str]
    shared_authors: List[str]
    relevance_explanation: str


class PaperRecommender:
    """
    Recommend papers based on multiple signals.
    
    Uses content similarity, citation networks, author overlap,
    and knowledge graph connections to suggest relevant papers.
    """
    
    def __init__(
        self,
        vector_store=None,
        graph_service=None,
    ):
        """
        Initialize the recommender.
        
        Args:
            vector_store: Vector store for content similarity
            graph_service: Graph service for relationship queries
        """
        self.vector_store = vector_store
        self.graph_service = graph_service
        
        # Weights for hybrid scoring
        self.weights = {
            RecommendationType.CONTENT: 0.35,
            RecommendationType.CITATION: 0.25,
            RecommendationType.TOPIC: 0.20,
            RecommendationType.AUTHOR: 0.10,
            RecommendationType.GRAPH: 0.10,
        }
    
    async def recommend(
        self,
        document_id: str,
        top_k: int = 10,
        exclude_ids: Optional[Set[str]] = None,
        recommendation_types: Optional[List[RecommendationType]] = None,
    ) -> List[Recommendation]:
        """
        Get recommendations for a document.
        
        Args:
            document_id: ID of the source document
            top_k: Number of recommendations to return
            exclude_ids: Document IDs to exclude
            recommendation_types: Types of recommendations to include
            
        Returns:
            List of Recommendation objects
        """
        exclude_ids = exclude_ids or {document_id}
        exclude_ids.add(document_id)
        
        recommendation_types = recommendation_types or list(RecommendationType)
        
        all_recommendations: Dict[str, Dict] = defaultdict(lambda: {
            'scores': {},
            'reasons': [],
            'shared_entities': set(),
            'shared_authors': set(),
        })
        
        # Content-based recommendations
        if RecommendationType.CONTENT in recommendation_types:
            content_recs = await self._get_content_recommendations(document_id, top_k * 2)
            for rec in content_recs:
                if rec['id'] not in exclude_ids:
                    all_recommendations[rec['id']]['scores'][RecommendationType.CONTENT] = rec['score']
                    all_recommendations[rec['id']]['reasons'].append(f"Similar content (score: {rec['score']:.2f})")
                    all_recommendations[rec['id']]['title'] = rec.get('title', rec['id'])
        
        # Topic/Entity-based recommendations
        if RecommendationType.TOPIC in recommendation_types:
            topic_recs = await self._get_topic_recommendations(document_id, top_k * 2)
            for rec in topic_recs:
                if rec['id'] not in exclude_ids:
                    all_recommendations[rec['id']]['scores'][RecommendationType.TOPIC] = rec['score']
                    all_recommendations[rec['id']]['reasons'].append(
                        f"Shares {len(rec.get('shared_entities', []))} topics/entities"
                    )
                    all_recommendations[rec['id']]['shared_entities'].update(rec.get('shared_entities', []))
                    all_recommendations[rec['id']]['title'] = rec.get('title', rec['id'])
        
        # Citation-based recommendations
        if RecommendationType.CITATION in recommendation_types:
            citation_recs = await self._get_citation_recommendations(document_id, top_k * 2)
            for rec in citation_recs:
                if rec['id'] not in exclude_ids:
                    all_recommendations[rec['id']]['scores'][RecommendationType.CITATION] = rec['score']
                    all_recommendations[rec['id']]['reasons'].append(rec.get('reason', 'Citation network'))
                    all_recommendations[rec['id']]['title'] = rec.get('title', rec['id'])
        
        # Author-based recommendations
        if RecommendationType.AUTHOR in recommendation_types:
            author_recs = await self._get_author_recommendations(document_id, top_k * 2)
            for rec in author_recs:
                if rec['id'] not in exclude_ids:
                    all_recommendations[rec['id']]['scores'][RecommendationType.AUTHOR] = rec['score']
                    all_recommendations[rec['id']]['reasons'].append(
                        f"Same author(s): {', '.join(rec.get('shared_authors', []))}"
                    )
                    all_recommendations[rec['id']]['shared_authors'].update(rec.get('shared_authors', []))
                    all_recommendations[rec['id']]['title'] = rec.get('title', rec['id'])
        
        # Graph-based recommendations
        if RecommendationType.GRAPH in recommendation_types:
            graph_recs = await self._get_graph_recommendations(document_id, top_k * 2)
            for rec in graph_recs:
                if rec['id'] not in exclude_ids:
                    all_recommendations[rec['id']]['scores'][RecommendationType.GRAPH] = rec['score']
                    all_recommendations[rec['id']]['reasons'].append("Connected in knowledge graph")
                    all_recommendations[rec['id']]['title'] = rec.get('title', rec['id'])
        
        # Compute hybrid scores
        final_recommendations = []
        for doc_id, data in all_recommendations.items():
            hybrid_score = 0.0
            contributing_types = []
            
            for rec_type, weight in self.weights.items():
                if rec_type in data['scores']:
                    hybrid_score += data['scores'][rec_type] * weight
                    contributing_types.append(rec_type)
            
            # Determine primary recommendation type
            if len(contributing_types) > 1:
                primary_type = RecommendationType.HYBRID
            elif contributing_types:
                primary_type = contributing_types[0]
            else:
                continue
            
            # Generate explanation
            explanation = self._generate_explanation(
                data['scores'],
                list(data['shared_entities']),
                list(data['shared_authors']),
            )
            
            final_recommendations.append(Recommendation(
                document_id=doc_id,
                title=data.get('title', doc_id),
                score=hybrid_score,
                recommendation_type=primary_type,
                reasons=data['reasons'],
                shared_entities=list(data['shared_entities'])[:10],
                shared_authors=list(data['shared_authors']),
                relevance_explanation=explanation,
            ))
        
        # Sort by score and return top_k
        final_recommendations.sort(key=lambda x: x.score, reverse=True)
        return final_recommendations[:top_k]
    
    async def _get_content_recommendations(
        self,
        document_id: str,
        limit: int,
    ) -> List[Dict]:
        """Get recommendations based on content similarity."""
        if not self.vector_store:
            return []
        
        try:
            # Get document embeddings
            results = self.vector_store.search_similar(
                query=None,
                document_id=document_id,
                top_k=limit,
            )
            
            return [
                {
                    'id': r.get('document_id', r.get('id')),
                    'title': r.get('title', ''),
                    'score': r.get('score', 0.5),
                }
                for r in results
            ]
        except Exception:
            return []
    
    async def _get_topic_recommendations(
        self,
        document_id: str,
        limit: int,
    ) -> List[Dict]:
        """Get recommendations based on shared topics/entities."""
        if not self.graph_service:
            return []
        
        try:
            # Get entities from the document
            doc_entities = await self.graph_service.get_document_entities(document_id)
            entity_ids = [e['id'] for e in doc_entities]
            
            # Find other documents with these entities
            related_docs: Dict[str, Dict] = {}
            
            for entity_id in entity_ids[:20]:  # Limit to top 20 entities
                docs = await self.graph_service.get_entity_documents(entity_id)
                for doc in docs:
                    if doc['id'] != document_id:
                        if doc['id'] not in related_docs:
                            related_docs[doc['id']] = {
                                'id': doc['id'],
                                'title': doc.get('title', ''),
                                'shared_entities': [],
                            }
                        related_docs[doc['id']]['shared_entities'].append(entity_id)
            
            # Score by number of shared entities
            results = []
            for doc_id, data in related_docs.items():
                score = min(len(data['shared_entities']) / 10.0, 1.0)
                results.append({
                    'id': doc_id,
                    'title': data['title'],
                    'score': score,
                    'shared_entities': data['shared_entities'],
                })
            
            results.sort(key=lambda x: x['score'], reverse=True)
            return results[:limit]
        except Exception:
            return []
    
    async def _get_citation_recommendations(
        self,
        document_id: str,
        limit: int,
    ) -> List[Dict]:
        """Get recommendations based on citation network."""
        if not self.graph_service:
            return []
        
        try:
            results = []
            
            # Get papers this document cites
            cited = await self.graph_service.get_cited_documents(document_id)
            for doc in cited:
                results.append({
                    'id': doc['id'],
                    'title': doc.get('title', ''),
                    'score': 0.9,
                    'reason': 'Cited by this paper',
                })
            
            # Get papers that cite this document
            citing = await self.graph_service.get_citing_documents(document_id)
            for doc in citing:
                results.append({
                    'id': doc['id'],
                    'title': doc.get('title', ''),
                    'score': 0.85,
                    'reason': 'Cites this paper',
                })
            
            # Get co-cited papers (cited together)
            co_cited = await self.graph_service.get_co_cited_documents(document_id)
            for doc in co_cited:
                results.append({
                    'id': doc['id'],
                    'title': doc.get('title', ''),
                    'score': 0.7,
                    'reason': 'Frequently co-cited',
                })
            
            return results[:limit]
        except Exception:
            return []
    
    async def _get_author_recommendations(
        self,
        document_id: str,
        limit: int,
    ) -> List[Dict]:
        """Get recommendations based on author overlap."""
        if not self.graph_service:
            return []
        
        try:
            # Get authors of this document
            authors = await self.graph_service.get_document_authors(document_id)
            author_names = [a.get('name', '') for a in authors]
            
            # Get other papers by these authors
            results = []
            seen_docs = set()
            
            for author in authors:
                other_papers = await self.graph_service.get_author_documents(author['id'])
                for doc in other_papers:
                    if doc['id'] != document_id and doc['id'] not in seen_docs:
                        seen_docs.add(doc['id'])
                        results.append({
                            'id': doc['id'],
                            'title': doc.get('title', ''),
                            'score': 0.8,
                            'shared_authors': [author.get('name', '')],
                        })
            
            return results[:limit]
        except Exception:
            return []
    
    async def _get_graph_recommendations(
        self,
        document_id: str,
        limit: int,
    ) -> List[Dict]:
        """Get recommendations based on knowledge graph structure."""
        if not self.graph_service:
            return []
        
        try:
            # Get neighbors in the knowledge graph
            neighbors = await self.graph_service.get_document_neighbors(
                document_id,
                depth=2,
                limit=limit,
            )
            
            return [
                {
                    'id': n['id'],
                    'title': n.get('title', ''),
                    'score': 1.0 / (n.get('distance', 1) + 1),
                }
                for n in neighbors
                if n['id'] != document_id
            ]
        except Exception:
            return []
    
    def _generate_explanation(
        self,
        scores: Dict[RecommendationType, float],
        shared_entities: List[str],
        shared_authors: List[str],
    ) -> str:
        """Generate a human-readable explanation for the recommendation."""
        parts = []
        
        if RecommendationType.CONTENT in scores:
            parts.append(f"content similarity ({scores[RecommendationType.CONTENT]:.0%})")
        
        if shared_entities:
            entity_preview = ", ".join(shared_entities[:3])
            if len(shared_entities) > 3:
                entity_preview += f" and {len(shared_entities) - 3} more"
            parts.append(f"shared topics: {entity_preview}")
        
        if shared_authors:
            parts.append(f"same author(s): {', '.join(shared_authors)}")
        
        if RecommendationType.CITATION in scores:
            parts.append("citation relationship")
        
        if RecommendationType.GRAPH in scores:
            parts.append("knowledge graph connection")
        
        if parts:
            return "Recommended based on " + "; ".join(parts)
        return "Related document"
    
    async def recommend_for_query(
        self,
        query: str,
        top_k: int = 10,
        exclude_ids: Optional[Set[str]] = None,
    ) -> List[Recommendation]:
        """
        Get recommendations based on a search query.
        
        Args:
            query: Search query
            top_k: Number of recommendations
            exclude_ids: Documents to exclude
            
        Returns:
            List of recommendations
        """
        exclude_ids = exclude_ids or set()
        
        if not self.vector_store:
            return []
        
        try:
            # Search for relevant documents
            results = self.vector_store.search(query, top_k=top_k * 2)
            
            recommendations = []
            for result in results:
                doc_id = result.get('document_id', result.get('id'))
                if doc_id not in exclude_ids:
                    recommendations.append(Recommendation(
                        document_id=doc_id,
                        title=result.get('title', doc_id),
                        score=result.get('score', 0.5),
                        recommendation_type=RecommendationType.CONTENT,
                        reasons=[f"Matches query: '{query[:50]}...'"],
                        shared_entities=[],
                        shared_authors=[],
                        relevance_explanation=f"Relevant to your search for '{query}'",
                    ))
            
            return recommendations[:top_k]
        except Exception:
            return []


async def get_recommendations(
    document_id: str,
    top_k: int = 10,
    vector_store=None,
    graph_service=None,
) -> List[Dict]:
    """
    Convenience function to get paper recommendations.
    
    Args:
        document_id: Source document ID
        top_k: Number of recommendations
        vector_store: Optional vector store
        graph_service: Optional graph service
        
    Returns:
        List of recommendation dictionaries
    """
    recommender = PaperRecommender(
        vector_store=vector_store,
        graph_service=graph_service,
    )
    
    recommendations = await recommender.recommend(document_id, top_k)
    
    return [
        {
            "document_id": r.document_id,
            "title": r.title,
            "score": r.score,
            "type": r.recommendation_type.value,
            "reasons": r.reasons,
            "shared_entities": r.shared_entities,
            "shared_authors": r.shared_authors,
            "explanation": r.relevance_explanation,
        }
        for r in recommendations
    ]

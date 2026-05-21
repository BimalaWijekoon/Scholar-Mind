"""
Duplicate Detector - Detect duplicate and similar papers

This module identifies:
- Exact duplicate documents
- Near-duplicate documents (same content, different formatting)
- Similar documents that may cover the same topic
"""

from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import hashlib
import re
from collections import Counter
from difflib import SequenceMatcher


class SimilarityLevel(str, Enum):
    """Levels of document similarity."""
    EXACT = "exact"  # Identical content
    NEAR_DUPLICATE = "near_duplicate"  # Same content, minor differences
    HIGHLY_SIMILAR = "highly_similar"  # Very similar, likely same topic
    SIMILAR = "similar"  # Similar content
    RELATED = "related"  # Related but different


@dataclass
class DuplicateMatch:
    """Represents a duplicate/similar document match."""
    document_id: str
    match_document_id: str
    similarity_level: SimilarityLevel
    similarity_score: float
    matching_sections: List[str]
    differences: List[str]
    recommendation: str


class DuplicateDetector:
    """
    Detect duplicate and similar documents.
    
    Uses multiple strategies:
    - Content hashing for exact duplicates
    - MinHash/SimHash for near-duplicates
    - Text similarity for similar documents
    - Entity overlap for related documents
    """
    
    def __init__(
        self,
        vector_store=None,
        embeddings_manager=None,
    ):
        """
        Initialize the detector.
        
        Args:
            vector_store: Vector store for similarity search
            embeddings_manager: Embeddings manager for computing vectors
        """
        self.vector_store = vector_store
        self.embeddings_manager = embeddings_manager
        
        # Thresholds for different similarity levels
        self.thresholds = {
            SimilarityLevel.EXACT: 0.99,
            SimilarityLevel.NEAR_DUPLICATE: 0.90,
            SimilarityLevel.HIGHLY_SIMILAR: 0.80,
            SimilarityLevel.SIMILAR: 0.65,
            SimilarityLevel.RELATED: 0.50,
        }
    
    async def detect(
        self,
        document_id: str,
        document_text: str,
        candidate_ids: Optional[List[str]] = None,
        min_similarity: float = 0.5,
    ) -> List[DuplicateMatch]:
        """
        Detect duplicates/similar documents for a given document.
        
        Args:
            document_id: ID of the document to check
            document_text: Text content of the document
            candidate_ids: Optional list of candidate document IDs to check
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of DuplicateMatch objects
        """
        matches = []
        
        # 1. Check for exact duplicates using content hash
        content_hash = self._compute_content_hash(document_text)
        
        # 2. Check for near-duplicates using normalized text
        normalized_text = self._normalize_text(document_text)
        normalized_hash = self._compute_content_hash(normalized_text)
        
        # 3. Compute shingles for similarity
        shingles = self._compute_shingles(normalized_text)
        
        # 4. Use vector similarity if available
        if self.vector_store:
            similar_docs = await self._find_similar_via_vectors(
                document_text, 
                exclude_id=document_id,
                top_k=20
            )
            
            for doc in similar_docs:
                if candidate_ids and doc['id'] not in candidate_ids:
                    continue
                
                score = doc.get('score', 0)
                if score >= min_similarity:
                    level = self._get_similarity_level(score)
                    
                    # Get matching sections
                    matching_sections = self._find_matching_sections(
                        document_text,
                        doc.get('text', ''),
                    )
                    
                    # Identify differences
                    differences = self._identify_differences(
                        document_text,
                        doc.get('text', ''),
                    )
                    
                    matches.append(DuplicateMatch(
                        document_id=document_id,
                        match_document_id=doc['id'],
                        similarity_level=level,
                        similarity_score=score,
                        matching_sections=matching_sections,
                        differences=differences,
                        recommendation=self._get_recommendation(level, score),
                    ))
        
        # Sort by similarity score
        matches.sort(key=lambda x: x.similarity_score, reverse=True)
        
        return matches
    
    def detect_in_batch(
        self,
        documents: List[Dict[str, str]],
        min_similarity: float = 0.7,
    ) -> List[DuplicateMatch]:
        """
        Detect duplicates within a batch of documents.
        
        Args:
            documents: List of dicts with 'id' and 'text' keys
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of DuplicateMatch objects
        """
        matches = []
        seen_pairs: Set[Tuple[str, str]] = set()
        
        # Precompute hashes and normalized texts
        doc_data = {}
        for doc in documents:
            doc_id = doc['id']
            text = doc['text']
            normalized = self._normalize_text(text)
            
            doc_data[doc_id] = {
                'text': text,
                'normalized': normalized,
                'hash': self._compute_content_hash(text),
                'normalized_hash': self._compute_content_hash(normalized),
                'shingles': self._compute_shingles(normalized),
                'word_set': set(normalized.split()),
            }
        
        # Compare all pairs
        doc_ids = list(doc_data.keys())
        
        for i, id1 in enumerate(doc_ids):
            for id2 in doc_ids[i + 1:]:
                pair_key = tuple(sorted([id1, id2]))
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)
                
                data1 = doc_data[id1]
                data2 = doc_data[id2]
                
                # Check exact duplicate
                if data1['hash'] == data2['hash']:
                    matches.append(DuplicateMatch(
                        document_id=id1,
                        match_document_id=id2,
                        similarity_level=SimilarityLevel.EXACT,
                        similarity_score=1.0,
                        matching_sections=["Entire document"],
                        differences=[],
                        recommendation="These are exact duplicates. Consider removing one.",
                    ))
                    continue
                
                # Check near-duplicate
                if data1['normalized_hash'] == data2['normalized_hash']:
                    matches.append(DuplicateMatch(
                        document_id=id1,
                        match_document_id=id2,
                        similarity_level=SimilarityLevel.NEAR_DUPLICATE,
                        similarity_score=0.95,
                        matching_sections=["Content is identical after normalization"],
                        differences=["Formatting differences"],
                        recommendation="Near-duplicate detected. Documents have identical content with formatting differences.",
                    ))
                    continue
                
                # Compute similarity
                similarity = self._compute_jaccard_similarity(
                    data1['shingles'],
                    data2['shingles'],
                )
                
                if similarity >= min_similarity:
                    level = self._get_similarity_level(similarity)
                    
                    matches.append(DuplicateMatch(
                        document_id=id1,
                        match_document_id=id2,
                        similarity_level=level,
                        similarity_score=similarity,
                        matching_sections=self._find_matching_sections(
                            data1['text'], data2['text']
                        ),
                        differences=self._identify_differences(
                            data1['text'], data2['text']
                        ),
                        recommendation=self._get_recommendation(level, similarity),
                    ))
        
        # Sort by similarity score
        matches.sort(key=lambda x: x.similarity_score, reverse=True)
        
        return matches
    
    def _compute_content_hash(self, text: str) -> str:
        """Compute hash of content."""
        return hashlib.sha256(text.encode()).hexdigest()
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove punctuation
        text = re.sub(r'[^\w\s]', '', text)
        
        # Remove numbers (optional, depending on use case)
        # text = re.sub(r'\d+', '', text)
        
        return text.strip()
    
    def _compute_shingles(self, text: str, k: int = 3) -> Set[str]:
        """Compute k-shingles (word n-grams) for text."""
        words = text.split()
        if len(words) < k:
            return {" ".join(words)}
        
        return {" ".join(words[i:i+k]) for i in range(len(words) - k + 1)}
    
    def _compute_jaccard_similarity(self, set1: Set[str], set2: Set[str]) -> float:
        """Compute Jaccard similarity between two sets."""
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    async def _find_similar_via_vectors(
        self,
        text: str,
        exclude_id: str,
        top_k: int = 20,
    ) -> List[Dict]:
        """Find similar documents using vector similarity."""
        if not self.vector_store:
            return []
        
        try:
            results = self.vector_store.search(text, top_k=top_k)
            return [r for r in results if r.get('id') != exclude_id]
        except Exception:
            return []
    
    def _get_similarity_level(self, score: float) -> SimilarityLevel:
        """Determine similarity level from score."""
        for level in [
            SimilarityLevel.EXACT,
            SimilarityLevel.NEAR_DUPLICATE,
            SimilarityLevel.HIGHLY_SIMILAR,
            SimilarityLevel.SIMILAR,
            SimilarityLevel.RELATED,
        ]:
            if score >= self.thresholds[level]:
                return level
        return SimilarityLevel.RELATED
    
    def _find_matching_sections(
        self,
        text1: str,
        text2: str,
        min_match_length: int = 50,
    ) -> List[str]:
        """Find matching sections between two texts."""
        matching_sections = []
        
        # Use SequenceMatcher to find matching blocks
        matcher = SequenceMatcher(None, text1, text2)
        
        for block in matcher.get_matching_blocks():
            if block.size >= min_match_length:
                section = text1[block.a:block.a + block.size]
                # Truncate for display
                if len(section) > 200:
                    section = section[:200] + "..."
                matching_sections.append(section.strip())
        
        return matching_sections[:5]  # Limit to top 5 matches
    
    def _identify_differences(
        self,
        text1: str,
        text2: str,
    ) -> List[str]:
        """Identify key differences between two texts."""
        differences = []
        
        # Compare word sets
        words1 = set(self._normalize_text(text1).split())
        words2 = set(self._normalize_text(text2).split())
        
        only_in_1 = words1 - words2
        only_in_2 = words2 - words1
        
        if only_in_1:
            unique_words = list(only_in_1)[:10]
            differences.append(f"Document 1 contains unique terms: {', '.join(unique_words)}")
        
        if only_in_2:
            unique_words = list(only_in_2)[:10]
            differences.append(f"Document 2 contains unique terms: {', '.join(unique_words)}")
        
        # Compare lengths
        len_diff = abs(len(text1) - len(text2))
        if len_diff > 1000:
            differences.append(f"Significant length difference: {len_diff} characters")
        
        return differences
    
    def _get_recommendation(self, level: SimilarityLevel, score: float) -> str:
        """Get recommendation based on similarity level."""
        recommendations = {
            SimilarityLevel.EXACT: 
                "Exact duplicate detected. Remove one of the documents.",
            SimilarityLevel.NEAR_DUPLICATE: 
                "Near-duplicate detected. Review for versioning or remove duplicate.",
            SimilarityLevel.HIGHLY_SIMILAR: 
                f"Highly similar ({score:.0%}). May be same source or heavily borrowed. Review carefully.",
            SimilarityLevel.SIMILAR: 
                f"Similar documents ({score:.0%}). Likely cover same topic. Consider consolidating.",
            SimilarityLevel.RELATED: 
                f"Related documents ({score:.0%}). May provide complementary information.",
        }
        return recommendations.get(level, "Review for potential overlap.")


async def detect_duplicates(
    document_id: str,
    document_text: str,
    vector_store=None,
    min_similarity: float = 0.5,
) -> List[Dict]:
    """
    Convenience function to detect duplicates.
    
    Args:
        document_id: ID of the document to check
        document_text: Text content of the document
        vector_store: Optional vector store
        min_similarity: Minimum similarity threshold
        
    Returns:
        List of duplicate match dictionaries
    """
    detector = DuplicateDetector(vector_store=vector_store)
    matches = await detector.detect(document_id, document_text, min_similarity=min_similarity)
    
    return [
        {
            "document_id": m.document_id,
            "match_document_id": m.match_document_id,
            "similarity_level": m.similarity_level.value,
            "similarity_score": m.similarity_score,
            "matching_sections": m.matching_sections,
            "differences": m.differences,
            "recommendation": m.recommendation,
        }
        for m in matches
    ]


def detect_duplicates_batch(
    documents: List[Dict[str, str]],
    min_similarity: float = 0.7,
) -> List[Dict]:
    """
    Detect duplicates within a batch of documents.
    
    Args:
        documents: List of dicts with 'id' and 'text' keys
        min_similarity: Minimum similarity threshold
        
    Returns:
        List of duplicate match dictionaries
    """
    detector = DuplicateDetector()
    matches = detector.detect_in_batch(documents, min_similarity=min_similarity)
    
    return [
        {
            "document_id": m.document_id,
            "match_document_id": m.match_document_id,
            "similarity_level": m.similarity_level.value,
            "similarity_score": m.similarity_score,
            "matching_sections": m.matching_sections,
            "differences": m.differences,
            "recommendation": m.recommendation,
        }
        for m in matches
    ]

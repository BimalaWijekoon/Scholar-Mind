"""
Machine Learning Module

This module provides ML capabilities for ScholarMind:
- Entity classification
- Claim extraction
- Contradiction detection
- Paper recommendations
- Research question generation
- Duplicate detection
"""

from backend.ml.model_manager import ModelManager
from backend.ml.entity_classifier import EntityClassifier
from backend.ml.claim_extractor import ClaimExtractor, extract_claims
from backend.ml.contradiction_detector import ContradictionDetector, detect_contradictions
from backend.ml.paper_recommender import PaperRecommender, get_recommendations
from backend.ml.question_generator import ResearchQuestionGenerator, generate_research_questions
from backend.ml.duplicate_detector import DuplicateDetector, detect_duplicates, detect_duplicates_batch

__all__ = [
    # Core
    "ModelManager",
    "EntityClassifier",
    # Claim extraction
    "ClaimExtractor",
    "extract_claims",
    # Contradiction detection
    "ContradictionDetector",
    "detect_contradictions",
    # Recommendations
    "PaperRecommender",
    "get_recommendations",
    # Question generation
    "ResearchQuestionGenerator",
    "generate_research_questions",
    # Duplicate detection
    "DuplicateDetector",
    "detect_duplicates",
    "detect_duplicates_batch",
]

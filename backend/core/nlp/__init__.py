"""
NLP Processing Module
"""

from backend.core.nlp.entity_extractor import EntityExtractor
from backend.core.nlp.relation_extractor import RelationExtractor
from backend.core.nlp.concept_linker import ConceptLinker
from backend.core.nlp.embeddings import EmbeddingsManager

__all__ = ["EntityExtractor", "RelationExtractor", "ConceptLinker", "EmbeddingsManager"]

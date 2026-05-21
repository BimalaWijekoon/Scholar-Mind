"""
Entity Extractor - Extract named entities from text using spaCy and custom models
"""

import spacy
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum


class EntityType(str, Enum):
    """Entity type categories."""
    PERSON = "PERSON"
    ORGANIZATION = "ORG"
    LOCATION = "LOC"
    DATE = "DATE"
    CONCEPT = "CONCEPT"
    TECHNOLOGY = "TECHNOLOGY"
    METHOD = "METHOD"
    METRIC = "METRIC"
    CHEMICAL = "CHEMICAL"
    DISEASE = "DISEASE"
    GENE = "GENE"
    PROTEIN = "PROTEIN"


@dataclass
class Entity:
    """Represents an extracted entity."""
    text: str
    entity_type: str
    start_char: int
    end_char: int
    confidence: float
    source: str
    metadata: Dict


class EntityExtractor:
    """
    Entity extractor using spaCy and custom NER models.
    
    Supports:
    - Standard NER (PERSON, ORG, LOC, DATE)
    - Scientific entities (SciSpacy)
    - Custom domain entities
    """
    
    def __init__(
        self,
        model_name: str = "en_core_web_lg",
        use_scispacy: bool = True,
        custom_patterns: Optional[Dict] = None,
    ):
        """
        Initialize the entity extractor.
        
        Args:
            model_name: spaCy model to use
            use_scispacy: Whether to use SciSpacy for scientific entities
            custom_patterns: Custom entity patterns
        """
        self.nlp = spacy.load(model_name)
        self.use_scispacy = use_scispacy
        self.custom_patterns = custom_patterns or {}
        
        # Load SciSpacy model if available
        self.sci_nlp = None
        if use_scispacy:
            try:
                self.sci_nlp = spacy.load("en_core_sci_lg")
            except OSError:
                pass
        
        # Add custom patterns to entity ruler
        if custom_patterns:
            self._add_custom_patterns(custom_patterns)
    
    def _add_custom_patterns(self, patterns: Dict) -> None:
        """Add custom patterns to the entity ruler."""
        ruler = self.nlp.add_pipe("entity_ruler", before="ner")
        
        pattern_list = []
        for entity_type, terms in patterns.items():
            for term in terms:
                pattern_list.append({"label": entity_type, "pattern": term})
        
        ruler.add_patterns(pattern_list)
    
    def extract(self, text: str, document_id: Optional[str] = None) -> List[Entity]:
        """
        Extract entities from text.
        
        Args:
            text: Text to extract entities from
            document_id: Optional document ID for tracking
            
        Returns:
            List of Entity objects
        """
        entities = []
        
        # Extract with standard model
        doc = self.nlp(text)
        
        for ent in doc.ents:
            entities.append(Entity(
                text=ent.text,
                entity_type=ent.label_,
                start_char=ent.start_char,
                end_char=ent.end_char,
                confidence=0.9,  # spaCy doesn't provide confidence scores
                source="spacy",
                metadata={
                    "document_id": document_id,
                    "model": "en_core_web_lg",
                },
            ))
        
        # Extract with SciSpacy if available
        if self.sci_nlp:
            sci_doc = self.sci_nlp(text)
            
            for ent in sci_doc.ents:
                # Avoid duplicates
                if not any(
                    e.text == ent.text and e.start_char == ent.start_char
                    for e in entities
                ):
                    entities.append(Entity(
                        text=ent.text,
                        entity_type=ent.label_,
                        start_char=ent.start_char,
                        end_char=ent.end_char,
                        confidence=0.85,
                        source="scispacy",
                        metadata={
                            "document_id": document_id,
                            "model": "en_core_sci_lg",
                        },
                    ))
        
        # Deduplicate and merge
        entities = self._deduplicate_entities(entities)
        
        return entities
    
    def extract_batch(
        self,
        texts: List[str],
        document_ids: Optional[List[str]] = None,
    ) -> List[List[Entity]]:
        """
        Extract entities from multiple texts.
        
        Args:
            texts: List of texts
            document_ids: Optional list of document IDs
            
        Returns:
            List of entity lists (one per text)
        """
        if document_ids is None:
            document_ids = [None] * len(texts)
        
        results = []
        
        # Process in batches with spaCy's pipe
        docs = list(self.nlp.pipe(texts, batch_size=50))
        
        for i, doc in enumerate(docs):
            entities = []
            
            for ent in doc.ents:
                entities.append(Entity(
                    text=ent.text,
                    entity_type=ent.label_,
                    start_char=ent.start_char,
                    end_char=ent.end_char,
                    confidence=0.9,
                    source="spacy",
                    metadata={"document_id": document_ids[i]},
                ))
            
            results.append(entities)
        
        return results
    
    def _deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """Remove duplicate and overlapping entities."""
        if not entities:
            return entities
        
        # Sort by position and length
        sorted_entities = sorted(
            entities,
            key=lambda e: (e.start_char, -(e.end_char - e.start_char)),
        )
        
        deduplicated = [sorted_entities[0]]
        
        for entity in sorted_entities[1:]:
            prev = deduplicated[-1]
            
            # Check for overlap
            if entity.start_char >= prev.end_char:
                deduplicated.append(entity)
            elif entity.confidence > prev.confidence:
                # Replace with higher confidence entity
                deduplicated[-1] = entity
        
        return deduplicated
    
    def get_entity_types(self) -> Set[str]:
        """Get all supported entity types."""
        types = set(self.nlp.get_pipe("ner").labels)
        
        if self.sci_nlp:
            types.update(self.sci_nlp.get_pipe("ner").labels)
        
        types.update(self.custom_patterns.keys())
        
        return types

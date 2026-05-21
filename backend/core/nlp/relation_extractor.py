"""
Relation Extractor - Extract relationships between entities
"""

import spacy
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum


class RelationType(str, Enum):
    """Common relation types."""
    AUTHORED_BY = "AUTHORED_BY"
    CITES = "CITES"
    WORKS_FOR = "WORKS_FOR"
    LOCATED_IN = "LOCATED_IN"
    PART_OF = "PART_OF"
    USED_BY = "USED_BY"
    RELATED_TO = "RELATED_TO"
    CAUSES = "CAUSES"
    TREATS = "TREATS"
    INTERACTS_WITH = "INTERACTS_WITH"
    SIMILAR_TO = "SIMILAR_TO"
    DERIVED_FROM = "DERIVED_FROM"
    APPLIES_TO = "APPLIES_TO"


@dataclass
class Relation:
    """Represents a relation between two entities."""
    source_text: str
    source_type: str
    target_text: str
    target_type: str
    relation_type: str
    confidence: float
    context: str
    metadata: Dict


class RelationExtractor:
    """
    Relation extractor using dependency parsing and pattern matching.
    
    Supports:
    - Dependency-based extraction
    - Pattern-based extraction
    - Neural relation classification (optional)
    """
    
    def __init__(
        self,
        model_name: str = "en_core_web_lg",
        use_neural: bool = False,
    ):
        """
        Initialize the relation extractor.
        
        Args:
            model_name: spaCy model to use
            use_neural: Whether to use neural relation classifier
        """
        self.nlp = spacy.load(model_name)
        self.use_neural = use_neural
        
        # Define extraction patterns
        self.patterns = self._define_patterns()
    
    def _define_patterns(self) -> List[Dict]:
        """Define relation extraction patterns."""
        patterns = [
            {
                "relation": RelationType.AUTHORED_BY,
                "verbs": ["write", "author", "publish", "create", "develop"],
                "preps": ["by"],
            },
            {
                "relation": RelationType.CITES,
                "verbs": ["cite", "reference", "mention", "discuss"],
                "preps": [],
            },
            {
                "relation": RelationType.WORKS_FOR,
                "verbs": ["work", "employ", "affiliate"],
                "preps": ["for", "at", "with"],
            },
            {
                "relation": RelationType.LOCATED_IN,
                "verbs": ["locate", "base", "situate", "found"],
                "preps": ["in", "at"],
            },
            {
                "relation": RelationType.PART_OF,
                "verbs": ["include", "contain", "comprise", "consist"],
                "preps": ["of", "in"],
            },
            {
                "relation": RelationType.USED_BY,
                "verbs": ["use", "utilize", "employ", "apply"],
                "preps": ["by", "in"],
            },
            {
                "relation": RelationType.CAUSES,
                "verbs": ["cause", "lead", "result", "induce", "trigger"],
                "preps": ["to", "in"],
            },
            {
                "relation": RelationType.TREATS,
                "verbs": ["treat", "cure", "heal", "remedy"],
                "preps": [],
            },
        ]
        return patterns
    
    def extract(
        self,
        text: str,
        entities: Optional[List[Dict]] = None,
    ) -> List[Relation]:
        """
        Extract relations from text.
        
        Args:
            text: Text to extract relations from
            entities: Optional pre-extracted entities
            
        Returns:
            List of Relation objects
        """
        doc = self.nlp(text)
        relations = []
        
        # Extract using dependency patterns
        dep_relations = self._extract_from_dependencies(doc)
        relations.extend(dep_relations)
        
        # Extract using predefined patterns
        pattern_relations = self._extract_from_patterns(doc)
        relations.extend(pattern_relations)
        
        # Extract entity co-occurrences
        if entities:
            cooccurrence_relations = self._extract_cooccurrences(doc, entities)
            relations.extend(cooccurrence_relations)
        
        # Deduplicate
        relations = self._deduplicate_relations(relations)
        
        return relations
    
    def _extract_from_dependencies(self, doc) -> List[Relation]:
        """Extract relations using dependency parsing."""
        relations = []
        
        for sent in doc.sents:
            # Find verbs
            for token in sent:
                if token.pos_ == "VERB":
                    verb_lemma = token.lemma_.lower()
                    
                    # Find subject and object
                    subject = None
                    obj = None
                    
                    for child in token.children:
                        if child.dep_ in ("nsubj", "nsubjpass"):
                            subject = self._get_span(child)
                        elif child.dep_ in ("dobj", "pobj", "attr"):
                            obj = self._get_span(child)
                        elif child.dep_ == "prep":
                            # Look for prepositional objects
                            for prep_child in child.children:
                                if prep_child.dep_ == "pobj":
                                    obj = self._get_span(prep_child)
                    
                    if subject and obj:
                        # Determine relation type
                        rel_type = self._determine_relation_type(verb_lemma)
                        
                        relations.append(Relation(
                            source_text=subject,
                            source_type="ENTITY",
                            target_text=obj,
                            target_type="ENTITY",
                            relation_type=rel_type,
                            confidence=0.7,
                            context=sent.text,
                            metadata={"verb": verb_lemma},
                        ))
        
        return relations
    
    def _get_span(self, token) -> str:
        """Get the full span for a token (including compound modifiers)."""
        span_tokens = [token]
        
        for child in token.children:
            if child.dep_ in ("compound", "amod", "det"):
                span_tokens.append(child)
        
        span_tokens.sort(key=lambda t: t.i)
        return " ".join(t.text for t in span_tokens)
    
    def _determine_relation_type(self, verb_lemma: str) -> str:
        """Determine relation type from verb."""
        for pattern in self.patterns:
            if verb_lemma in pattern["verbs"]:
                return pattern["relation"].value
        
        return RelationType.RELATED_TO.value
    
    def _extract_from_patterns(self, doc) -> List[Relation]:
        """Extract relations using pattern matching."""
        relations = []
        
        # Entity pairs in same sentence
        for sent in doc.sents:
            entities_in_sent = list(sent.ents)
            
            for i, ent1 in enumerate(entities_in_sent):
                for ent2 in entities_in_sent[i + 1:]:
                    # Check for relation indicators between entities
                    between_text = doc.text[ent1.end_char:ent2.start_char].lower()
                    
                    for pattern in self.patterns:
                        for verb in pattern["verbs"]:
                            if verb in between_text:
                                relations.append(Relation(
                                    source_text=ent1.text,
                                    source_type=ent1.label_,
                                    target_text=ent2.text,
                                    target_type=ent2.label_,
                                    relation_type=pattern["relation"].value,
                                    confidence=0.6,
                                    context=sent.text,
                                    metadata={"pattern_verb": verb},
                                ))
                                break
        
        return relations
    
    def _extract_cooccurrences(
        self,
        doc,
        entities: List[Dict],
    ) -> List[Relation]:
        """Extract relations from entity co-occurrences."""
        relations = []
        
        # Group entities by sentence
        sentence_entities = {}
        
        for ent in entities:
            for i, sent in enumerate(doc.sents):
                if ent["start_char"] >= sent.start_char and ent["end_char"] <= sent.end_char:
                    if i not in sentence_entities:
                        sentence_entities[i] = []
                    sentence_entities[i].append(ent)
                    break
        
        # Create co-occurrence relations
        for sent_idx, ents in sentence_entities.items():
            for i, ent1 in enumerate(ents):
                for ent2 in ents[i + 1:]:
                    relations.append(Relation(
                        source_text=ent1["text"],
                        source_type=ent1.get("entity_type", "ENTITY"),
                        target_text=ent2["text"],
                        target_type=ent2.get("entity_type", "ENTITY"),
                        relation_type=RelationType.RELATED_TO.value,
                        confidence=0.4,
                        context="",
                        metadata={"extraction_method": "cooccurrence"},
                    ))
        
        return relations
    
    def _deduplicate_relations(self, relations: List[Relation]) -> List[Relation]:
        """Remove duplicate relations."""
        seen = set()
        deduplicated = []
        
        for rel in relations:
            key = (
                rel.source_text.lower(),
                rel.target_text.lower(),
                rel.relation_type,
            )
            
            if key not in seen:
                seen.add(key)
                deduplicated.append(rel)
        
        return deduplicated

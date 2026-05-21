"""
Contradiction Detector - Detect contradictions between papers/claims

This module identifies conflicting statements between different sources,
such as:
- Conflicting performance claims
- Opposing conclusions
- Incompatible methodologies
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import spacy
from difflib import SequenceMatcher


class ContradictionType(str, Enum):
    """Types of contradictions."""
    DIRECT = "direct"  # Direct logical contradiction
    NUMERICAL = "numerical"  # Conflicting numbers/metrics
    METHODOLOGICAL = "methodological"  # Different methods, different conclusions
    CAUSAL = "causal"  # Conflicting cause-effect claims
    TEMPORAL = "temporal"  # Claims that conflict in timing
    PARTIAL = "partial"  # Partial disagreement


class ContradictionSeverity(str, Enum):
    """Severity levels for contradictions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Contradiction:
    """Represents a detected contradiction."""
    claim1: str
    claim2: str
    source1: str
    source2: str
    contradiction_type: ContradictionType
    severity: ContradictionSeverity
    confidence: float
    explanation: str
    shared_entities: List[str]
    resolution_suggestions: List[str]


class ContradictionDetector:
    """
    Detect contradictions between claims from different sources.
    
    Uses semantic similarity, numerical comparison, and linguistic
    patterns to identify conflicting statements.
    """
    
    def __init__(self, model_name: str = "en_core_web_sm"):
        """Initialize the contradiction detector."""
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", model_name])
            self.nlp = spacy.load(model_name)
        
        # Negation words
        self.negation_words = {
            'not', 'no', 'never', 'neither', 'none', 'nobody', 
            'nothing', 'nowhere', "n't", 'cannot', "can't", 
            "won't", "don't", "doesn't", "didn't", "isn't", 
            "aren't", "wasn't", "weren't", 'without', 'lack',
            'fail', 'fails', 'failed', 'unable'
        }
        
        # Comparison words
        self.comparison_words = {
            'better': 'worse',
            'higher': 'lower',
            'more': 'less',
            'faster': 'slower',
            'larger': 'smaller',
            'greater': 'lesser',
            'increase': 'decrease',
            'improve': 'degrade',
            'superior': 'inferior',
            'outperform': 'underperform',
        }
        
        # Numerical pattern
        self.number_pattern = re.compile(r'(\d+\.?\d*)\s*(%|percent)?')
    
    def detect(
        self,
        claims1: List[Dict],
        claims2: List[Dict],
        source1_name: str = "Source 1",
        source2_name: str = "Source 2",
        similarity_threshold: float = 0.6,
    ) -> List[Contradiction]:
        """
        Detect contradictions between two sets of claims.
        
        Args:
            claims1: Claims from first source
            claims2: Claims from second source
            source1_name: Name of first source
            source2_name: Name of second source
            similarity_threshold: Minimum similarity to consider claims related
            
        Returns:
            List of Contradiction objects
        """
        contradictions = []
        
        for c1 in claims1:
            for c2 in claims2:
                # Check if claims are about similar topics
                similarity = self._compute_similarity(c1['text'], c2['text'])
                
                if similarity >= similarity_threshold:
                    # Check for contradiction
                    contradiction = self._check_contradiction(
                        c1, c2, source1_name, source2_name, similarity
                    )
                    
                    if contradiction:
                        contradictions.append(contradiction)
        
        # Sort by severity and confidence
        contradictions.sort(
            key=lambda x: (
                list(ContradictionSeverity).index(x.severity),
                -x.confidence
            ),
            reverse=True
        )
        
        return contradictions
    
    def _compute_similarity(self, text1: str, text2: str) -> float:
        """Compute semantic similarity between two texts."""
        doc1 = self.nlp(text1)
        doc2 = self.nlp(text2)
        
        # Use spaCy's built-in similarity
        if doc1.vector_norm and doc2.vector_norm:
            similarity = doc1.similarity(doc2)
        else:
            # Fallback to sequence matching
            similarity = SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
        
        return similarity
    
    def _check_contradiction(
        self,
        claim1: Dict,
        claim2: Dict,
        source1: str,
        source2: str,
        similarity: float,
    ) -> Optional[Contradiction]:
        """Check if two claims contradict each other."""
        text1 = claim1['text']
        text2 = claim2['text']
        
        # Extract entities from both claims
        doc1 = self.nlp(text1)
        doc2 = self.nlp(text2)
        
        entities1 = {ent.text.lower() for ent in doc1.ents}
        entities2 = {ent.text.lower() for ent in doc2.ents}
        shared_entities = list(entities1 & entities2)
        
        # Check for different contradiction types
        
        # 1. Direct negation contradiction
        neg_result = self._check_negation_contradiction(text1, text2)
        if neg_result:
            return Contradiction(
                claim1=text1,
                claim2=text2,
                source1=source1,
                source2=source2,
                contradiction_type=ContradictionType.DIRECT,
                severity=ContradictionSeverity.HIGH,
                confidence=neg_result['confidence'],
                explanation=neg_result['explanation'],
                shared_entities=shared_entities,
                resolution_suggestions=self._get_resolution_suggestions(ContradictionType.DIRECT),
            )
        
        # 2. Numerical contradiction
        num_result = self._check_numerical_contradiction(text1, text2, shared_entities)
        if num_result:
            return Contradiction(
                claim1=text1,
                claim2=text2,
                source1=source1,
                source2=source2,
                contradiction_type=ContradictionType.NUMERICAL,
                severity=num_result['severity'],
                confidence=num_result['confidence'],
                explanation=num_result['explanation'],
                shared_entities=shared_entities,
                resolution_suggestions=self._get_resolution_suggestions(ContradictionType.NUMERICAL),
            )
        
        # 3. Comparative contradiction
        comp_result = self._check_comparative_contradiction(text1, text2)
        if comp_result:
            return Contradiction(
                claim1=text1,
                claim2=text2,
                source1=source1,
                source2=source2,
                contradiction_type=ContradictionType.METHODOLOGICAL,
                severity=ContradictionSeverity.MEDIUM,
                confidence=comp_result['confidence'],
                explanation=comp_result['explanation'],
                shared_entities=shared_entities,
                resolution_suggestions=self._get_resolution_suggestions(ContradictionType.METHODOLOGICAL),
            )
        
        return None
    
    def _check_negation_contradiction(self, text1: str, text2: str) -> Optional[Dict]:
        """Check for negation-based contradictions."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        neg1 = words1 & self.negation_words
        neg2 = words2 & self.negation_words
        
        # One has negation, the other doesn't
        if bool(neg1) != bool(neg2):
            # Check if they share key content words
            content_words1 = {w for w in words1 if len(w) > 4 and w not in self.negation_words}
            content_words2 = {w for w in words2 if len(w) > 4 and w not in self.negation_words}
            
            shared_content = content_words1 & content_words2
            
            if len(shared_content) >= 2:
                return {
                    'confidence': min(0.6 + len(shared_content) * 0.1, 0.9),
                    'explanation': f"One claim contains negation while the other affirms. "
                                   f"Shared concepts: {', '.join(list(shared_content)[:5])}"
                }
        
        return None
    
    def _check_numerical_contradiction(
        self,
        text1: str,
        text2: str,
        shared_entities: List[str],
    ) -> Optional[Dict]:
        """Check for contradicting numerical claims."""
        numbers1 = self.number_pattern.findall(text1)
        numbers2 = self.number_pattern.findall(text2)
        
        if not numbers1 or not numbers2:
            return None
        
        # Compare numbers for same metrics
        for num1, unit1 in numbers1:
            for num2, unit2 in numbers2:
                # Same unit type
                if unit1.lower() == unit2.lower() or (not unit1 and not unit2):
                    val1 = float(num1)
                    val2 = float(num2)
                    
                    # Check for significant difference
                    if abs(val1 - val2) > 5:  # More than 5 points/percent difference
                        # Determine severity based on difference
                        diff = abs(val1 - val2)
                        if diff > 20:
                            severity = ContradictionSeverity.CRITICAL
                        elif diff > 10:
                            severity = ContradictionSeverity.HIGH
                        else:
                            severity = ContradictionSeverity.MEDIUM
                        
                        return {
                            'confidence': 0.8,
                            'severity': severity,
                            'explanation': f"Numerical discrepancy: {val1}{unit1 or ''} vs {val2}{unit2 or ''} "
                                           f"(difference: {diff:.1f}). "
                                           f"Both claims discuss: {', '.join(shared_entities[:3]) if shared_entities else 'similar topics'}"
                        }
        
        return None
    
    def _check_comparative_contradiction(self, text1: str, text2: str) -> Optional[Dict]:
        """Check for contradicting comparative statements."""
        text1_lower = text1.lower()
        text2_lower = text2.lower()
        
        for word, opposite in self.comparison_words.items():
            # Check if one text uses a word and the other uses its opposite
            if word in text1_lower and opposite in text2_lower:
                return {
                    'confidence': 0.75,
                    'explanation': f"Opposing comparisons: '{word}' in one claim vs '{opposite}' in the other"
                }
            if opposite in text1_lower and word in text2_lower:
                return {
                    'confidence': 0.75,
                    'explanation': f"Opposing comparisons: '{opposite}' in one claim vs '{word}' in the other"
                }
        
        return None
    
    def _get_resolution_suggestions(self, contradiction_type: ContradictionType) -> List[str]:
        """Get suggestions for resolving a contradiction."""
        suggestions = {
            ContradictionType.DIRECT: [
                "Examine the context in which each claim was made",
                "Check if claims refer to different conditions or settings",
                "Verify the methodology used in each study",
                "Look for more recent studies that may resolve the conflict",
            ],
            ContradictionType.NUMERICAL: [
                "Check if metrics are calculated the same way",
                "Verify evaluation datasets are identical",
                "Compare experimental conditions and hyperparameters",
                "Look for differences in data preprocessing",
            ],
            ContradictionType.METHODOLOGICAL: [
                "Examine the specific methods used in each study",
                "Check for differences in evaluation criteria",
                "Consider domain or dataset-specific factors",
                "Look at publication dates for methodological evolution",
            ],
            ContradictionType.CAUSAL: [
                "Examine the causal mechanisms proposed",
                "Check for confounding variables",
                "Look at the scope of each claim",
                "Consider if claims apply to different populations/domains",
            ],
            ContradictionType.TEMPORAL: [
                "Check the time periods covered by each study",
                "Consider if the field has evolved",
                "Look for changes in methodology over time",
            ],
            ContradictionType.PARTIAL: [
                "Identify the specific points of disagreement",
                "Look for conditions under which each claim holds",
                "Consider if claims are about different aspects",
            ],
        }
        
        return suggestions.get(contradiction_type, [
            "Compare methodologies carefully",
            "Verify data sources",
            "Check for updates or corrections",
        ])


def detect_contradictions(
    claims1: List[Dict],
    claims2: List[Dict],
    source1: str = "Document 1",
    source2: str = "Document 2",
) -> List[Dict]:
    """
    Convenience function to detect contradictions.
    
    Args:
        claims1: Claims from first source
        claims2: Claims from second source
        source1: Name of first source
        source2: Name of second source
        
    Returns:
        List of contradiction dictionaries
    """
    detector = ContradictionDetector()
    contradictions = detector.detect(claims1, claims2, source1, source2)
    
    return [
        {
            "claim1": c.claim1,
            "claim2": c.claim2,
            "source1": c.source1,
            "source2": c.source2,
            "type": c.contradiction_type.value,
            "severity": c.severity.value,
            "confidence": c.confidence,
            "explanation": c.explanation,
            "shared_entities": c.shared_entities,
            "resolution_suggestions": c.resolution_suggestions,
        }
        for c in contradictions
    ]

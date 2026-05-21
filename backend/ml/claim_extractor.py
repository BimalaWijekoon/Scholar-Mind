"""
Claim Extractor - Extract verifiable claims from academic text

This module identifies sentences that make factual claims which can be
verified or disputed, such as:
- "Method X achieves 95% accuracy on dataset Y"
- "Our approach outperforms previous methods"
- "This finding contradicts earlier research"
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import spacy


class ClaimType(str, Enum):
    """Types of claims that can be extracted."""
    PERFORMANCE = "performance"  # Claims about metrics/results
    COMPARISON = "comparison"  # Comparisons between methods
    CONTRIBUTION = "contribution"  # Novel contributions
    FINDING = "finding"  # Research findings
    HYPOTHESIS = "hypothesis"  # Proposed hypotheses
    LIMITATION = "limitation"  # Acknowledged limitations
    FUTURE_WORK = "future_work"  # Future research directions


@dataclass
class Claim:
    """Represents an extracted claim."""
    text: str
    claim_type: ClaimType
    confidence: float
    source_sentence: str
    entities: List[str]
    metrics: List[Dict[str, str]]
    is_verifiable: bool
    evidence_needed: List[str]


class ClaimExtractor:
    """
    Extract verifiable claims from academic text.
    
    Uses pattern matching and linguistic analysis to identify
    sentences that make specific, verifiable claims.
    """
    
    def __init__(self, model_name: str = "en_core_web_sm"):
        """Initialize the claim extractor."""
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", model_name])
            self.nlp = spacy.load(model_name)
        
        # Claim indicator patterns
        self.claim_patterns = self._define_patterns()
        
        # Metric patterns (percentages, numbers with units)
        self.metric_pattern = re.compile(
            r'(\d+\.?\d*)\s*(%|percent|accuracy|precision|recall|F1|BLEU|ROUGE|'
            r'points?|pp|ms|seconds?|hours?|times?|x faster|improvement)',
            re.IGNORECASE
        )
    
    def _define_patterns(self) -> Dict[ClaimType, List[str]]:
        """Define patterns for each claim type."""
        return {
            ClaimType.PERFORMANCE: [
                r'achiev(es?|ed|ing)\s+(\d+\.?\d*)',
                r'(accuracy|precision|recall|F1|score)\s+(of|is|was|reaches?)\s+\d+',
                r'obtains?\s+.{0,30}\d+\.?\d*\s*%',
                r'results?\s+(show|indicate|demonstrate)',
                r'outperforms?\s+.{0,50}by\s+\d+',
                r'improves?\s+.{0,30}by\s+\d+',
            ],
            ClaimType.COMPARISON: [
                r'outperforms?',
                r'better\s+than',
                r'worse\s+than',
                r'compared\s+to',
                r'superior\s+to',
                r'inferior\s+to',
                r'(more|less)\s+effective',
                r'state-of-the-art',
                r'SOTA',
                r'baseline',
            ],
            ClaimType.CONTRIBUTION: [
                r'we\s+(propose|present|introduce|develop)',
                r'our\s+(approach|method|model|system)',
                r'novel\s+(approach|method|technique)',
                r'first\s+to',
                r'contribution',
                r'main\s+finding',
            ],
            ClaimType.FINDING: [
                r'we\s+(find|found|observe|show|demonstrate)',
                r'results?\s+(show|indicate|suggest|reveal)',
                r'experiment(s|al)?\s+(show|demonstrate|reveal)',
                r'analysis\s+(shows?|reveals?|indicates?)',
                r'evidence\s+(suggests?|shows?)',
            ],
            ClaimType.HYPOTHESIS: [
                r'we\s+hypothesize',
                r'hypothesis',
                r'we\s+conjecture',
                r'we\s+expect',
                r'should\s+(be|have|show)',
                r'might\s+(be|have|explain)',
            ],
            ClaimType.LIMITATION: [
                r'limitation',
                r'drawback',
                r'weakness',
                r'fails?\s+to',
                r'does\s+not\s+(handle|work|scale)',
                r'limited\s+(to|by)',
                r'challenge',
            ],
            ClaimType.FUTURE_WORK: [
                r'future\s+work',
                r'future\s+research',
                r'will\s+(explore|investigate|extend)',
                r'plan\s+to',
                r'could\s+be\s+(extended|improved)',
                r'direction',
            ],
        }
    
    def extract(
        self,
        text: str,
        min_confidence: float = 0.5,
    ) -> List[Claim]:
        """
        Extract claims from text.
        
        Args:
            text: Text to extract claims from
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of Claim objects
        """
        doc = self.nlp(text)
        claims = []
        
        for sent in doc.sents:
            sent_text = sent.text.strip()
            
            # Skip very short sentences
            if len(sent_text) < 20:
                continue
            
            # Check for claim patterns
            claim_type, confidence = self._classify_claim(sent_text)
            
            if claim_type and confidence >= min_confidence:
                # Extract entities from the sentence
                entities = [ent.text for ent in sent.ents]
                
                # Extract metrics
                metrics = self._extract_metrics(sent_text)
                
                # Determine if verifiable
                is_verifiable = self._is_verifiable(sent_text, metrics)
                
                # Determine what evidence would be needed
                evidence_needed = self._get_evidence_needed(claim_type, sent_text)
                
                claims.append(Claim(
                    text=sent_text,
                    claim_type=claim_type,
                    confidence=confidence,
                    source_sentence=sent_text,
                    entities=entities,
                    metrics=metrics,
                    is_verifiable=is_verifiable,
                    evidence_needed=evidence_needed,
                ))
        
        return claims
    
    def _classify_claim(self, sentence: str) -> Tuple[Optional[ClaimType], float]:
        """Classify a sentence as a particular claim type."""
        best_type = None
        best_confidence = 0.0
        
        for claim_type, patterns in self.claim_patterns.items():
            matches = 0
            for pattern in patterns:
                if re.search(pattern, sentence, re.IGNORECASE):
                    matches += 1
            
            if matches > 0:
                # Confidence based on number of pattern matches
                confidence = min(0.5 + (matches * 0.15), 0.95)
                
                # Boost confidence if metrics are present
                if self.metric_pattern.search(sentence):
                    confidence = min(confidence + 0.1, 0.98)
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_type = claim_type
        
        return best_type, best_confidence
    
    def _extract_metrics(self, sentence: str) -> List[Dict[str, str]]:
        """Extract numerical metrics from a sentence."""
        metrics = []
        
        for match in self.metric_pattern.finditer(sentence):
            value, unit = match.groups()
            metrics.append({
                "value": value,
                "unit": unit,
                "full_match": match.group(0),
            })
        
        return metrics
    
    def _is_verifiable(self, sentence: str, metrics: List[Dict]) -> bool:
        """Determine if a claim is verifiable."""
        # Claims with specific metrics are more verifiable
        if metrics:
            return True
        
        # Claims with comparisons to named entities are verifiable
        comparison_words = ['than', 'compared to', 'versus', 'vs', 'outperforms']
        if any(word in sentence.lower() for word in comparison_words):
            return True
        
        # Claims about specific datasets are verifiable
        dataset_indicators = ['dataset', 'benchmark', 'corpus', 'SQuAD', 'GLUE', 'ImageNet']
        if any(indicator.lower() in sentence.lower() for indicator in dataset_indicators):
            return True
        
        return False
    
    def _get_evidence_needed(self, claim_type: ClaimType, sentence: str) -> List[str]:
        """Determine what evidence would be needed to verify the claim."""
        evidence = []
        
        if claim_type == ClaimType.PERFORMANCE:
            evidence.extend([
                "Experimental results on benchmark datasets",
                "Statistical significance tests",
                "Comparison with baseline methods",
            ])
        elif claim_type == ClaimType.COMPARISON:
            evidence.extend([
                "Head-to-head experimental comparison",
                "Same evaluation metrics and datasets",
                "Statistical significance of differences",
            ])
        elif claim_type == ClaimType.CONTRIBUTION:
            evidence.extend([
                "Literature review showing novelty",
                "Experimental validation",
                "Ablation studies",
            ])
        elif claim_type == ClaimType.FINDING:
            evidence.extend([
                "Reproducible experiments",
                "Statistical analysis",
                "Multiple trials or cross-validation",
            ])
        elif claim_type == ClaimType.HYPOTHESIS:
            evidence.extend([
                "Theoretical justification",
                "Preliminary experimental evidence",
                "Related work supporting the hypothesis",
            ])
        
        return evidence
    
    def extract_key_claims(
        self,
        text: str,
        top_k: int = 5,
    ) -> List[Claim]:
        """
        Extract the top-k most important claims from text.
        
        Args:
            text: Text to extract claims from
            top_k: Number of claims to return
            
        Returns:
            List of top claims sorted by importance
        """
        all_claims = self.extract(text)
        
        # Score claims by importance
        def score_claim(claim: Claim) -> float:
            score = claim.confidence
            
            # Boost for verifiable claims
            if claim.is_verifiable:
                score += 0.2
            
            # Boost for claims with metrics
            score += len(claim.metrics) * 0.1
            
            # Boost for contribution and performance claims
            if claim.claim_type in [ClaimType.CONTRIBUTION, ClaimType.PERFORMANCE]:
                score += 0.15
            
            return score
        
        sorted_claims = sorted(all_claims, key=score_claim, reverse=True)
        return sorted_claims[:top_k]


def extract_claims(text: str, top_k: int = 10) -> List[Dict]:
    """
    Convenience function to extract claims from text.
    
    Args:
        text: Text to analyze
        top_k: Number of claims to return
        
    Returns:
        List of claim dictionaries
    """
    extractor = ClaimExtractor()
    claims = extractor.extract_key_claims(text, top_k)
    
    return [
        {
            "text": c.text,
            "type": c.claim_type.value,
            "confidence": c.confidence,
            "entities": c.entities,
            "metrics": c.metrics,
            "verifiable": c.is_verifiable,
            "evidence_needed": c.evidence_needed,
        }
        for c in claims
    ]

"""
Entity Classifier - Classify entities into categories
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """Result of entity classification."""
    text: str
    predicted_class: str
    confidence: float
    all_scores: Dict[str, float]


class EntityClassifier:
    """
    Classifier for categorizing entities.
    
    Uses:
    - Fine-tuned transformers
    - Rule-based classification
    - Ensemble methods
    """
    
    # Default entity categories
    DEFAULT_CATEGORIES = [
        "PERSON",
        "ORGANIZATION",
        "LOCATION",
        "CONCEPT",
        "TECHNOLOGY",
        "METHOD",
        "DATASET",
        "METRIC",
        "CHEMICAL",
        "DISEASE",
        "GENE",
        "OTHER",
    ]
    
    def __init__(
        self,
        model_manager=None,
        categories: Optional[List[str]] = None,
        use_rules: bool = True,
    ):
        """
        Initialize the entity classifier.
        
        Args:
            model_manager: Model manager for loading classifier
            categories: Custom entity categories
            use_rules: Whether to use rule-based classification
        """
        self.model_manager = model_manager
        self.categories = categories or self.DEFAULT_CATEGORIES
        self.use_rules = use_rules
        
        self._model = None
        self._rules = self._build_rules()
    
    def _build_rules(self) -> Dict[str, List[str]]:
        """Build rule-based classification patterns."""
        return {
            "TECHNOLOGY": [
                "algorithm", "framework", "library", "system", "platform",
                "database", "api", "sdk", "protocol", "architecture",
                "neural network", "deep learning", "machine learning",
            ],
            "METHOD": [
                "method", "approach", "technique", "procedure", "process",
                "analysis", "evaluation", "assessment", "measurement",
            ],
            "DATASET": [
                "dataset", "corpus", "benchmark", "collection", "database",
            ],
            "METRIC": [
                "accuracy", "precision", "recall", "f1", "score", "rate",
                "loss", "error", "performance", "metric",
            ],
            "CHEMICAL": [
                "molecule", "compound", "protein", "enzyme", "acid",
                "ion", "receptor", "inhibitor", "drug",
            ],
            "DISEASE": [
                "disease", "syndrome", "disorder", "cancer", "infection",
                "condition", "illness", "pathology",
            ],
        }
    
    def classify(self, entity_text: str, context: Optional[str] = None) -> ClassificationResult:
        """
        Classify an entity.
        
        Args:
            entity_text: Entity text to classify
            context: Optional surrounding context
            
        Returns:
            ClassificationResult with predicted class
        """
        # Try rule-based first
        if self.use_rules:
            rule_result = self._classify_by_rules(entity_text)
            if rule_result and rule_result.confidence > 0.8:
                return rule_result
        
        # Try model-based classification
        if self.model_manager:
            try:
                model_result = self._classify_by_model(entity_text, context)
                if model_result:
                    return model_result
            except Exception as e:
                logger.warning(f"Model classification failed: {e}")
        
        # Fallback to rules or OTHER
        if self.use_rules:
            rule_result = self._classify_by_rules(entity_text)
            if rule_result:
                return rule_result
        
        return ClassificationResult(
            text=entity_text,
            predicted_class="OTHER",
            confidence=0.5,
            all_scores={"OTHER": 0.5},
        )
    
    def classify_batch(
        self,
        entities: List[str],
        contexts: Optional[List[str]] = None,
    ) -> List[ClassificationResult]:
        """
        Classify multiple entities.
        
        Args:
            entities: List of entity texts
            contexts: Optional list of contexts
            
        Returns:
            List of classification results
        """
        if contexts is None:
            contexts = [None] * len(entities)
        
        results = []
        for entity, context in zip(entities, contexts):
            result = self.classify(entity, context)
            results.append(result)
        
        return results
    
    def _classify_by_rules(self, entity_text: str) -> Optional[ClassificationResult]:
        """Classify using rule-based patterns."""
        text_lower = entity_text.lower()
        
        scores = {}
        
        for category, patterns in self._rules.items():
            score = 0.0
            for pattern in patterns:
                if pattern in text_lower:
                    score = max(score, 0.9)
                elif any(word in text_lower for word in pattern.split()):
                    score = max(score, 0.6)
            
            if score > 0:
                scores[category] = score
        
        if scores:
            best_category = max(scores, key=scores.get)
            return ClassificationResult(
                text=entity_text,
                predicted_class=best_category,
                confidence=scores[best_category],
                all_scores=scores,
            )
        
        return None
    
    def _classify_by_model(
        self,
        entity_text: str,
        context: Optional[str],
    ) -> Optional[ClassificationResult]:
        """Classify using ML model."""
        if not self.model_manager:
            return None
        
        # Prepare input
        if context:
            input_text = f"{context} [SEP] {entity_text}"
        else:
            input_text = entity_text
        
        # Get predictions
        try:
            probs = self.model_manager.predict("classifier", input_text)
            
            # Map to categories
            scores = {}
            for i, category in enumerate(self.categories[:len(probs[0])]):
                scores[category] = float(probs[0][i])
            
            best_category = max(scores, key=scores.get)
            
            return ClassificationResult(
                text=entity_text,
                predicted_class=best_category,
                confidence=scores[best_category],
                all_scores=scores,
            )
        except Exception:
            return None
    
    def add_rule(self, category: str, patterns: List[str]) -> None:
        """
        Add classification rules.
        
        Args:
            category: Entity category
            patterns: List of patterns for this category
        """
        if category not in self._rules:
            self._rules[category] = []
        
        self._rules[category].extend(patterns)
        
        if category not in self.categories:
            self.categories.append(category)
    
    def get_categories(self) -> List[str]:
        """Get all entity categories."""
        return self.categories.copy()
    
    def get_category_counts(
        self,
        classifications: List[ClassificationResult],
    ) -> Dict[str, int]:
        """
        Get counts per category.
        
        Args:
            classifications: List of classification results
            
        Returns:
            Dictionary of category counts
        """
        counts = {cat: 0 for cat in self.categories}
        
        for result in classifications:
            if result.predicted_class in counts:
                counts[result.predicted_class] += 1
            else:
                counts["OTHER"] = counts.get("OTHER", 0) + 1
        
        return counts

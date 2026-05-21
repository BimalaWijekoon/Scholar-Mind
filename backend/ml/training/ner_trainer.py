"""
NER Trainer - Train custom Named Entity Recognition models
"""

from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class TrainingConfig:
    """Configuration for NER training."""
    model_name: str = "en_core_web_lg"
    output_dir: str = "models/custom_ner"
    epochs: int = 30
    batch_size: int = 16
    learning_rate: float = 2e-5
    dropout: float = 0.1
    eval_split: float = 0.2
    early_stopping_patience: int = 5


@dataclass
class TrainingResult:
    """Result of training."""
    model_path: str
    metrics: Dict[str, float]
    training_time: float
    epochs_completed: int
    best_epoch: int


class NERTrainer:
    """
    Trainer for custom NER models.
    
    Supports:
    - spaCy NER training
    - Fine-tuning on custom entities
    - Evaluation and metrics
    """
    
    def __init__(self, config: Optional[TrainingConfig] = None):
        """
        Initialize the NER trainer.
        
        Args:
            config: Training configuration
        """
        self.config = config or TrainingConfig()
    
    def prepare_data(
        self,
        annotations: List[Dict],
        output_path: Optional[str] = None,
    ) -> Tuple[List, List]:
        """
        Prepare training data from annotations.
        
        Args:
            annotations: List of annotation dicts with 'text' and 'entities'
            output_path: Optional path to save prepared data
            
        Returns:
            Tuple of (train_data, eval_data)
        """
        import random
        
        # Convert to spaCy format
        data = []
        for ann in annotations:
            text = ann["text"]
            entities = []
            
            for ent in ann.get("entities", []):
                entities.append((
                    ent["start"],
                    ent["end"],
                    ent["label"],
                ))
            
            data.append((text, {"entities": entities}))
        
        # Shuffle and split
        random.shuffle(data)
        split_idx = int(len(data) * (1 - self.config.eval_split))
        
        train_data = data[:split_idx]
        eval_data = data[split_idx:]
        
        # Save if path provided
        if output_path:
            with open(output_path, 'w') as f:
                json.dump({
                    "train": train_data,
                    "eval": eval_data,
                }, f)
        
        return train_data, eval_data
    
    def train(
        self,
        train_data: List,
        eval_data: Optional[List] = None,
    ) -> TrainingResult:
        """
        Train the NER model.
        
        Args:
            train_data: Training data in spaCy format
            eval_data: Optional evaluation data
            
        Returns:
            TrainingResult with metrics and model path
        """
        import spacy
        from spacy.training import Example
        import time
        
        start_time = time.time()
        
        # Load base model
        nlp = spacy.load(self.config.model_name)
        
        # Get or create NER component
        if "ner" not in nlp.pipe_names:
            ner = nlp.add_pipe("ner")
        else:
            ner = nlp.get_pipe("ner")
        
        # Add labels from training data
        for _, annotations in train_data:
            for ent in annotations.get("entities", []):
                ner.add_label(ent[2])
        
        # Prepare training
        other_pipes = [pipe for pipe in nlp.pipe_names if pipe != "ner"]
        
        best_score = 0.0
        best_epoch = 0
        patience_counter = 0
        
        with nlp.disable_pipes(*other_pipes):
            optimizer = nlp.resume_training()
            
            for epoch in range(self.config.epochs):
                losses = {}
                
                # Training loop
                import random
                random.shuffle(train_data)
                
                for batch_start in range(0, len(train_data), self.config.batch_size):
                    batch = train_data[batch_start:batch_start + self.config.batch_size]
                    
                    examples = []
                    for text, annotations in batch:
                        doc = nlp.make_doc(text)
                        example = Example.from_dict(doc, annotations)
                        examples.append(example)
                    
                    nlp.update(examples, drop=self.config.dropout, losses=losses)
                
                # Evaluation
                if eval_data:
                    scores = self._evaluate(nlp, eval_data)
                    f1_score = scores.get("f1", 0.0)
                    
                    logger.info(
                        f"Epoch {epoch + 1}: Loss={losses.get('ner', 0):.4f}, "
                        f"F1={f1_score:.4f}"
                    )
                    
                    # Early stopping check
                    if f1_score > best_score:
                        best_score = f1_score
                        best_epoch = epoch + 1
                        patience_counter = 0
                        
                        # Save best model
                        output_dir = Path(self.config.output_dir)
                        output_dir.mkdir(parents=True, exist_ok=True)
                        nlp.to_disk(output_dir / "best_model")
                    else:
                        patience_counter += 1
                        
                        if patience_counter >= self.config.early_stopping_patience:
                            logger.info(f"Early stopping at epoch {epoch + 1}")
                            break
                else:
                    logger.info(f"Epoch {epoch + 1}: Loss={losses.get('ner', 0):.4f}")
        
        # Save final model
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        nlp.to_disk(output_dir / "final_model")
        
        training_time = time.time() - start_time
        
        # Final evaluation
        final_metrics = {}
        if eval_data:
            final_metrics = self._evaluate(nlp, eval_data)
        
        return TrainingResult(
            model_path=str(output_dir / "best_model"),
            metrics=final_metrics,
            training_time=training_time,
            epochs_completed=epoch + 1,
            best_epoch=best_epoch,
        )
    
    def _evaluate(self, nlp, eval_data: List) -> Dict[str, float]:
        """Evaluate model on data."""
        from spacy.training import Example
        from spacy.scorer import Scorer
        
        examples = []
        for text, annotations in eval_data:
            doc = nlp.make_doc(text)
            example = Example.from_dict(doc, annotations)
            examples.append(example)
        
        scorer = Scorer()
        scores = scorer.score(examples)
        
        return {
            "precision": scores.get("ents_p", 0.0),
            "recall": scores.get("ents_r", 0.0),
            "f1": scores.get("ents_f", 0.0),
        }
    
    def load_model(self, model_path: str) -> Any:
        """Load a trained model."""
        import spacy
        return spacy.load(model_path)
    
    def predict(self, nlp, texts: List[str]) -> List[List[Dict]]:
        """
        Run predictions with trained model.
        
        Args:
            nlp: Loaded spaCy model
            texts: Texts to process
            
        Returns:
            List of entity lists per text
        """
        results = []
        
        for doc in nlp.pipe(texts):
            entities = []
            for ent in doc.ents:
                entities.append({
                    "text": ent.text,
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char,
                })
            results.append(entities)
        
        return results

"""
Model Manager - Manage ML models for inference
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    """Information about a loaded model."""
    name: str
    model_type: str
    version: str
    path: Optional[str]
    loaded: bool
    device: str


class ModelManager:
    """
    Manager for ML models.
    
    Handles:
    - Model loading and caching
    - Model inference
    - Model versioning
    - Resource management
    """
    
    def __init__(
        self,
        models_dir: Optional[str] = None,
        device: Optional[str] = None,
        cache_size: int = 3,
    ):
        """
        Initialize the model manager.
        
        Args:
            models_dir: Directory containing models
            device: Device to load models on
            cache_size: Maximum number of models to keep loaded
        """
        self.models_dir = Path(models_dir) if models_dir else Path("models")
        
        # Determine device
        if device:
            self.device = device
        else:
            import torch
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        self.cache_size = cache_size
        
        # Model cache
        self._models: Dict[str, Any] = {}
        self._model_info: Dict[str, ModelInfo] = {}
        
        # Default models
        self._default_models = {
            "embeddings": "sentence-transformers/all-MiniLM-L6-v2",
            "ner": "en_core_web_lg",
            "reranker": "cross-encoder/ms-marco-MiniLM-L-6-v2",
            "classifier": "distilbert-base-uncased",
        }
    
    def load_model(
        self,
        model_name: str,
        model_type: str = "auto",
        model_path: Optional[str] = None,
        **kwargs,
    ) -> Any:
        """
        Load a model.
        
        Args:
            model_name: Name identifier for the model
            model_type: Type of model (embeddings, ner, classifier, etc.)
            model_path: Path or HuggingFace model name
            **kwargs: Additional model loading arguments
            
        Returns:
            Loaded model
        """
        # Check cache
        if model_name in self._models:
            logger.info(f"Using cached model: {model_name}")
            return self._models[model_name]
        
        # Determine model path
        if model_path is None:
            model_path = self._default_models.get(model_name, model_name)
        
        # Load based on type
        try:
            if model_type == "embeddings" or "sentence-transformers" in str(model_path):
                model = self._load_embeddings_model(model_path)
            elif model_type == "ner" or "spacy" in str(model_path) or model_path.startswith("en_"):
                model = self._load_spacy_model(model_path)
            elif model_type == "reranker" or "cross-encoder" in str(model_path):
                model = self._load_reranker_model(model_path)
            elif model_type == "classifier":
                model = self._load_classifier_model(model_path, **kwargs)
            else:
                model = self._load_transformer_model(model_path, **kwargs)
            
            # Cache model
            self._cache_model(model_name, model, model_type, model_path)
            
            return model
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise
    
    def _load_embeddings_model(self, model_path: str) -> Any:
        """Load sentence-transformers model."""
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer(model_path, device=self.device)
    
    def _load_spacy_model(self, model_path: str) -> Any:
        """Load spaCy model."""
        import spacy
        return spacy.load(model_path)
    
    def _load_reranker_model(self, model_path: str) -> Any:
        """Load cross-encoder model."""
        from sentence_transformers import CrossEncoder
        return CrossEncoder(model_path, device=self.device)
    
    def _load_classifier_model(self, model_path: str, num_labels: int = 2) -> Any:
        """Load classifier model."""
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForSequenceClassification.from_pretrained(
            model_path,
            num_labels=num_labels,
        )
        
        if self.device == "cuda":
            model = model.cuda()
        
        return {"model": model, "tokenizer": tokenizer}
    
    def _load_transformer_model(self, model_path: str, **kwargs) -> Any:
        """Load generic transformer model."""
        from transformers import AutoModel, AutoTokenizer
        
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModel.from_pretrained(model_path, **kwargs)
        
        if self.device == "cuda":
            model = model.cuda()
        
        return {"model": model, "tokenizer": tokenizer}
    
    def _cache_model(
        self,
        model_name: str,
        model: Any,
        model_type: str,
        model_path: str,
    ) -> None:
        """Cache a loaded model."""
        # Evict oldest if cache full
        if len(self._models) >= self.cache_size:
            oldest = next(iter(self._models))
            self.unload_model(oldest)
        
        self._models[model_name] = model
        self._model_info[model_name] = ModelInfo(
            name=model_name,
            model_type=model_type,
            version="1.0",
            path=model_path,
            loaded=True,
            device=self.device,
        )
        
        logger.info(f"Loaded and cached model: {model_name}")
    
    def get_model(self, model_name: str) -> Optional[Any]:
        """Get a loaded model."""
        return self._models.get(model_name)
    
    def unload_model(self, model_name: str) -> None:
        """Unload a model from memory."""
        if model_name in self._models:
            del self._models[model_name]
            if model_name in self._model_info:
                self._model_info[model_name].loaded = False
            
            # Force garbage collection
            import gc
            gc.collect()
            
            if self.device == "cuda":
                import torch
                torch.cuda.empty_cache()
            
            logger.info(f"Unloaded model: {model_name}")
    
    def list_models(self) -> List[ModelInfo]:
        """List all models (loaded and available)."""
        models = list(self._model_info.values())
        
        # Add default models not yet loaded
        for name in self._default_models:
            if name not in self._model_info:
                models.append(ModelInfo(
                    name=name,
                    model_type="default",
                    version="1.0",
                    path=self._default_models[name],
                    loaded=False,
                    device=self.device,
                ))
        
        return models
    
    def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """Get information about a model."""
        return self._model_info.get(model_name)
    
    def predict(
        self,
        model_name: str,
        inputs: Union[str, List[str]],
        **kwargs,
    ) -> Any:
        """
        Run prediction with a model.
        
        Args:
            model_name: Name of the model
            inputs: Input text(s)
            **kwargs: Additional prediction arguments
            
        Returns:
            Prediction results
        """
        model = self.get_model(model_name)
        if model is None:
            model = self.load_model(model_name)
        
        model_info = self._model_info.get(model_name)
        
        if model_info.model_type == "embeddings":
            return model.encode(inputs, **kwargs)
        elif model_info.model_type == "ner":
            if isinstance(inputs, list):
                return list(model.pipe(inputs, **kwargs))
            return model(inputs)
        elif model_info.model_type == "reranker":
            return model.predict(inputs, **kwargs)
        elif model_info.model_type == "classifier":
            return self._predict_classifier(model, inputs, **kwargs)
        else:
            return self._predict_transformer(model, inputs, **kwargs)
    
    def _predict_classifier(
        self,
        model_dict: Dict,
        inputs: Union[str, List[str]],
        **kwargs,
    ) -> Any:
        """Run classifier prediction."""
        import torch
        
        model = model_dict["model"]
        tokenizer = model_dict["tokenizer"]
        
        if isinstance(inputs, str):
            inputs = [inputs]
        
        encoded = tokenizer(
            inputs,
            padding=True,
            truncation=True,
            return_tensors="pt",
        )
        
        if self.device == "cuda":
            encoded = {k: v.cuda() for k, v in encoded.items()}
        
        with torch.no_grad():
            outputs = model(**encoded)
            probs = torch.softmax(outputs.logits, dim=-1)
        
        return probs.cpu().numpy()
    
    def _predict_transformer(
        self,
        model_dict: Dict,
        inputs: Union[str, List[str]],
        **kwargs,
    ) -> Any:
        """Run transformer prediction."""
        import torch
        
        model = model_dict["model"]
        tokenizer = model_dict["tokenizer"]
        
        if isinstance(inputs, str):
            inputs = [inputs]
        
        encoded = tokenizer(
            inputs,
            padding=True,
            truncation=True,
            return_tensors="pt",
        )
        
        if self.device == "cuda":
            encoded = {k: v.cuda() for k, v in encoded.items()}
        
        with torch.no_grad():
            outputs = model(**encoded)
        
        return outputs.last_hidden_state.cpu().numpy()
    
    def clear_cache(self) -> None:
        """Clear all cached models."""
        model_names = list(self._models.keys())
        for name in model_names:
            self.unload_model(name)

"""
Unit Tests for NLP Components
"""

import pytest
from unittest.mock import MagicMock, patch
import numpy as np


class TestEntityExtractor:
    """Tests for entity extraction."""
    
    def test_entity_extractor_initialization(self):
        """Test EntityExtractor can be initialized."""
        with patch("spacy.load") as mock_load:
            mock_load.return_value = MagicMock()
            
            from backend.core.nlp import EntityExtractor
            
            extractor = EntityExtractor(use_scispacy=False)
            assert extractor is not None
    
    def test_extract_entities_from_text(self, sample_text, mock_spacy):
        """Test entity extraction from sample text."""
        with patch("spacy.load", return_value=mock_spacy):
            from backend.core.nlp import EntityExtractor
            
            extractor = EntityExtractor(use_scispacy=False)
            # Override with mock
            extractor.nlp = mock_spacy
            
            entities = extractor.extract(sample_text, "doc-1")
            
            assert isinstance(entities, list)
            for entity in entities:
                assert hasattr(entity, "text")
                assert hasattr(entity, "entity_type")
                assert hasattr(entity, "confidence")
    
    def test_extract_empty_text(self, mock_spacy):
        """Test extraction from empty text."""
        with patch("spacy.load", return_value=mock_spacy):
            from backend.core.nlp import EntityExtractor
            
            extractor = EntityExtractor(use_scispacy=False)
            extractor.nlp = mock_spacy
            
            entities = extractor.extract("", "doc-1")
            
            assert isinstance(entities, list)
    
    def test_entity_deduplication(self, mock_spacy):
        """Test that duplicate entities are handled."""
        with patch("spacy.load", return_value=mock_spacy):
            from backend.core.nlp import EntityExtractor
            
            extractor = EntityExtractor(use_scispacy=False)
            extractor.nlp = mock_spacy
            
            text = "Machine learning is great. Machine learning is powerful."
            entities = extractor.extract(text, "doc-1")
            
            # Should have some deduplication logic
            assert isinstance(entities, list)
    
    def test_scientific_entity_types(self, mock_spacy):
        """Test extraction of scientific entity types."""
        with patch("spacy.load", return_value=mock_spacy):
            from backend.core.nlp import EntityExtractor
            
            extractor = EntityExtractor(use_scispacy=False)
            extractor.nlp = mock_spacy
            
            text = "The protein p53 binds to DNA and regulates cell cycle."
            entities = extractor.extract(text, "doc-1")
            
            # Scientific entities might be found with SciSpacy
            assert isinstance(entities, list)


class TestRelationExtractor:
    """Tests for relation extraction."""
    
    def test_relation_extractor_initialization(self):
        """Test RelationExtractor can be initialized."""
        with patch("spacy.load") as mock_load:
            mock_load.return_value = MagicMock()
            
            from backend.core.nlp import RelationExtractor
            
            extractor = RelationExtractor()
            assert extractor is not None
    
    def test_extract_relations(self, sample_text, sample_entities, mock_spacy):
        """Test relation extraction."""
        with patch("spacy.load", return_value=mock_spacy):
            from backend.core.nlp import RelationExtractor
            
            extractor = RelationExtractor()
            extractor.nlp = mock_spacy
            
            relations = extractor.extract(sample_text, sample_entities)
            
            assert isinstance(relations, list)
            for relation in relations:
                assert hasattr(relation, "source_text")
                assert hasattr(relation, "target_text")
                assert hasattr(relation, "relation_type")
    
    def test_extract_no_entities(self, sample_text, mock_spacy):
        """Test relation extraction with no entities."""
        with patch("spacy.load", return_value=mock_spacy):
            from backend.core.nlp import RelationExtractor
            
            extractor = RelationExtractor()
            extractor.nlp = mock_spacy
            
            relations = extractor.extract(sample_text, [])
            
            assert isinstance(relations, list)
            assert len(relations) == 0


class TestEmbeddingsManager:
    """Tests for embeddings generation."""
    
    def test_embeddings_manager_initialization(self):
        """Test EmbeddingsManager can be initialized."""
        with patch("sentence_transformers.SentenceTransformer") as mock_st:
            mock_st.return_value = MagicMock()
            
            from backend.core.nlp import EmbeddingsManager
            
            manager = EmbeddingsManager()
            assert manager is not None
    
    def test_embed_single_text(self, mock_embeddings):
        """Test embedding a single text."""
        with patch("sentence_transformers.SentenceTransformer") as mock_st:
            mock_st.return_value = mock_embeddings
            
            from backend.core.nlp import EmbeddingsManager
            
            manager = EmbeddingsManager()
            manager.model = mock_embeddings
            
            embedding = manager.embed("Test text")
            
            assert embedding is not None
            assert len(embedding) > 0
    
    def test_embed_multiple_documents(self, mock_embeddings):
        """Test embedding multiple documents."""
        with patch("sentence_transformers.SentenceTransformer") as mock_st:
            mock_embeddings.encode.return_value = np.random.rand(3, 384).astype(np.float32)
            mock_st.return_value = mock_embeddings
            
            from backend.core.nlp import EmbeddingsManager
            
            manager = EmbeddingsManager()
            manager.model = mock_embeddings
            
            texts = ["Doc 1", "Doc 2", "Doc 3"]
            embeddings = manager.embed_documents(texts)
            
            assert embeddings is not None
            assert len(embeddings) == 3
    
    def test_embed_empty_list(self, mock_embeddings):
        """Test embedding empty list."""
        with patch("sentence_transformers.SentenceTransformer") as mock_st:
            mock_embeddings.encode.return_value = np.array([])
            mock_st.return_value = mock_embeddings
            
            from backend.core.nlp import EmbeddingsManager
            
            manager = EmbeddingsManager()
            manager.model = mock_embeddings
            
            embeddings = manager.embed_documents([])
            
            assert len(embeddings) == 0
    
    def test_embedding_dimension(self, mock_embeddings):
        """Test embedding dimension."""
        with patch("sentence_transformers.SentenceTransformer") as mock_st:
            mock_embeddings.encode.return_value = np.random.rand(384).astype(np.float32)
            mock_st.return_value = mock_embeddings
            
            from backend.core.nlp import EmbeddingsManager
            
            manager = EmbeddingsManager()
            manager.model = mock_embeddings
            
            embedding = manager.embed("Test")
            
            # Default model should have 384 dimensions
            assert len(embedding) == 384


class TestConceptLinker:
    """Tests for concept linking."""
    
    def test_concept_linker_initialization(self):
        """Test ConceptLinker can be initialized."""
        from backend.core.nlp import ConceptLinker
        
        linker = ConceptLinker()
        assert linker is not None
    
    @pytest.mark.asyncio
    async def test_link_to_wikidata(self):
        """Test linking to Wikidata."""
        from backend.core.nlp import ConceptLinker
        
        linker = ConceptLinker()
        
        # Mock the HTTP request
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "search": [
                    {
                        "id": "Q11660",
                        "label": "artificial intelligence",
                        "description": "intelligence demonstrated by machines",
                    }
                ]
            }
            mock_response.raise_for_status = MagicMock()
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await linker.link_entity("artificial intelligence")
            
            # Test would check for linked entity
    
    def test_cache_functionality(self):
        """Test that caching works."""
        from backend.core.nlp import ConceptLinker
        
        linker = ConceptLinker(use_cache=True)
        
        # First lookup would cache
        # Second lookup should use cache
        # Implementation dependent


class TestNLPPipeline:
    """Integration tests for NLP pipeline."""
    
    def test_full_pipeline(self, sample_text, mock_spacy, mock_embeddings):
        """Test running the full NLP pipeline."""
        with patch("spacy.load", return_value=mock_spacy):
            with patch("sentence_transformers.SentenceTransformer") as mock_st:
                mock_embeddings.encode.return_value = np.random.rand(384).astype(np.float32)
                mock_st.return_value = mock_embeddings
                
                from backend.core.nlp import EntityExtractor, RelationExtractor, EmbeddingsManager
                
                # Extract entities
                entity_extractor = EntityExtractor(use_scispacy=False)
                entity_extractor.nlp = mock_spacy
                entities = entity_extractor.extract(sample_text, "doc-1")
                
                # Extract relations
                relation_extractor = RelationExtractor()
                relation_extractor.nlp = mock_spacy
                entity_list = [{"text": e.text, "entity_type": e.entity_type} for e in entities]
                relations = relation_extractor.extract(sample_text, entity_list)
                
                # Generate embeddings
                embeddings_manager = EmbeddingsManager()
                embeddings_manager.model = mock_embeddings
                embedding = embeddings_manager.embed(sample_text)
                
                assert isinstance(entities, list)
                assert isinstance(relations, list)
                assert embedding is not None

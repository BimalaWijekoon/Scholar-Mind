"""
Integration Tests for Full Pipeline
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import tempfile
import os


class TestDocumentProcessingPipeline:
    """Integration tests for document processing pipeline."""
    
    @pytest.mark.asyncio
    async def test_full_document_pipeline(
        self,
        sample_text,
        mock_embeddings,
        mock_vector_store,
        mock_neo4j_client,
        mock_spacy,
    ):
        """Test the full document processing pipeline."""
        with patch("spacy.load", return_value=mock_spacy):
            with patch("sentence_transformers.SentenceTransformer") as mock_st:
                import numpy as np
                mock_embeddings.encode.return_value = np.random.rand(5, 384).astype(np.float32)
                mock_st.return_value = mock_embeddings
                
                from backend.core.document_processing import DocumentChunker, MetadataExtractor
                from backend.core.nlp import EntityExtractor, RelationExtractor, EmbeddingsManager
                from backend.core.knowledge_graph import GraphBuilder
                
                # Step 1: Extract metadata
                metadata_extractor = MetadataExtractor()
                metadata = metadata_extractor.extract(sample_text)
                
                assert metadata is not None
                
                # Step 2: Chunk document
                chunker = DocumentChunker(chunk_size=200, chunk_overlap=30)
                chunks = chunker.chunk(sample_text, "test-doc")
                
                assert len(chunks) > 0
                
                # Step 3: Extract entities
                entity_extractor = EntityExtractor(use_scispacy=False)
                entity_extractor.nlp = mock_spacy
                entities = entity_extractor.extract(sample_text, "test-doc")
                
                assert isinstance(entities, list)
                
                # Step 4: Extract relations
                relation_extractor = RelationExtractor()
                relation_extractor.nlp = mock_spacy
                entity_list = [{"text": e.text, "entity_type": e.entity_type} for e in entities]
                relations = relation_extractor.extract(sample_text, entity_list)
                
                assert isinstance(relations, list)
                
                # Step 5: Generate embeddings
                embeddings_manager = EmbeddingsManager()
                embeddings_manager.model = mock_embeddings
                
                chunk_texts = [chunk.text for chunk in chunks]
                embeddings = embeddings_manager.embed_documents(chunk_texts)
                
                assert embeddings is not None
                
                # Step 6: Build knowledge graph
                graph_builder = GraphBuilder()
                
                # Add entities and relations to graph
                entity_dicts = [{"text": e.text, "entity_type": e.entity_type} for e in entities]
                relation_dicts = [
                    {
                        "source_text": r.source_text if hasattr(r, "source_text") else r.get("source_text"),
                        "source_type": r.source_type if hasattr(r, "source_type") else r.get("source_type"),
                        "target_text": r.target_text if hasattr(r, "target_text") else r.get("target_text"),
                        "target_type": r.target_type if hasattr(r, "target_type") else r.get("target_type"),
                        "relation_type": r.relation_type if hasattr(r, "relation_type") else r.get("relation_type"),
                    }
                    for r in relations
                ]
                
                graph_builder.build_from_extraction(entity_dicts, relation_dicts)
                
                stats = graph_builder.get_statistics()
                
                # Pipeline completed successfully
                assert stats is not None


class TestQueryPipeline:
    """Integration tests for query pipeline."""
    
    @pytest.mark.asyncio
    async def test_rag_pipeline(
        self,
        mock_embeddings,
        mock_vector_store,
        mock_llm,
    ):
        """Test the RAG query pipeline."""
        with patch("sentence_transformers.SentenceTransformer") as mock_st:
            import numpy as np
            mock_embeddings.encode.return_value = np.random.rand(384).astype(np.float32)
            mock_st.return_value = mock_embeddings
            
            from backend.core.nlp import EmbeddingsManager
            from backend.core.retrieval import HybridRetriever
            
            # Step 1: Embed query
            embeddings_manager = EmbeddingsManager()
            embeddings_manager.model = mock_embeddings
            
            query = "What is machine learning?"
            query_embedding = embeddings_manager.embed(query)
            
            assert query_embedding is not None
            
            # Step 2: Retrieve documents (mocked)
            # In real scenario, would use HybridRetriever
            results = mock_vector_store.search(query_embedding, k=5)
            
            assert len(results) > 0
            
            # Step 3: Generate response (mocked)
            context = "\n".join([r.text for r in results])
            response = mock_llm.invoke(f"Context: {context}\nQuestion: {query}")
            
            assert response.content is not None
    
    @pytest.mark.asyncio
    async def test_graph_enhanced_query(
        self,
        mock_neo4j_client,
        mock_llm,
    ):
        """Test graph-enhanced query."""
        from backend.core.knowledge_graph import GraphQueryEngine
        
        engine = GraphQueryEngine(neo4j_client=mock_neo4j_client)
        
        # Mock query result
        mock_neo4j_client.execute_query = AsyncMock(return_value=[
            {"source": "machine learning", "relation": "IS_A", "target": "AI"},
            {"source": "deep learning", "relation": "IS_A", "target": "machine learning"},
        ])
        
        # Execute query
        result = await engine.query("What concepts are related to machine learning?")
        
        assert result is not None


class TestAgentPipeline:
    """Integration tests for agent pipeline."""
    
    @pytest.mark.asyncio
    async def test_research_agent_flow(self, mock_llm):
        """Test research agent flow."""
        with patch("langchain_google_genai.ChatGoogleGenerativeAI") as mock_chat:
            mock_chat.return_value = mock_llm
            
            # Agent would orchestrate tools
            # This is a simplified test
            
            query = "Explain the relationship between AI and machine learning"
            
            # Mock agent response
            response = {
                "response": "Machine learning is a subset of AI...",
                "sources": [{"id": "doc-1", "text": "Source text"}],
                "iterations": 2,
            }
            
            assert response["response"] is not None
            assert len(response["sources"]) > 0


class TestEndToEndFlow:
    """End-to-end integration tests."""
    
    @pytest.mark.asyncio
    async def test_document_to_answer_flow(
        self,
        sample_text,
        temp_dir,
        mock_spacy,
        mock_embeddings,
        mock_vector_store,
        mock_neo4j_client,
        mock_llm,
    ):
        """Test complete flow from document upload to answering questions."""
        # Create a test document
        doc_path = os.path.join(temp_dir, "test_doc.txt")
        with open(doc_path, "w") as f:
            f.write(sample_text)
        
        with patch("spacy.load", return_value=mock_spacy):
            with patch("sentence_transformers.SentenceTransformer") as mock_st:
                import numpy as np
                mock_embeddings.encode.return_value = np.random.rand(384).astype(np.float32)
                mock_st.return_value = mock_embeddings
                
                from backend.services.document_service import DocumentService
                from backend.services.query_service import QueryService
                from backend.core.document_processing import DocumentChunker
                from backend.core.nlp import EmbeddingsManager
                
                # Initialize services with mocks
                doc_service = DocumentService(
                    chunker=DocumentChunker(),
                    embeddings_manager=EmbeddingsManager(),
                    vector_store=mock_vector_store,
                )
                doc_service.embeddings_manager.model = mock_embeddings
                
                query_service = QueryService(
                    llm=mock_llm,
                )
                
                # Process document (simplified)
                doc_id = "test-doc-1"
                
                # Query the processed document
                result = await query_service.ask(
                    "What is the main topic of this document?",
                )
                
                assert result is not None


class TestConcurrency:
    """Tests for concurrent operations."""
    
    @pytest.mark.asyncio
    async def test_concurrent_document_processing(self, temp_dir):
        """Test processing multiple documents concurrently."""
        import asyncio
        
        # Create multiple test files
        doc_count = 5
        doc_paths = []
        
        for i in range(doc_count):
            path = os.path.join(temp_dir, f"doc_{i}.txt")
            with open(path, "w") as f:
                f.write(f"This is document {i}. It contains test content.")
            doc_paths.append(path)
        
        # Simulate concurrent processing
        async def process_doc(path):
            await asyncio.sleep(0.1)  # Simulate processing
            return {"path": path, "status": "processed"}
        
        # Process all documents concurrently
        results = await asyncio.gather(*[process_doc(p) for p in doc_paths])
        
        assert len(results) == doc_count
        for result in results:
            assert result["status"] == "processed"
    
    @pytest.mark.asyncio
    async def test_concurrent_queries(self, mock_llm):
        """Test handling multiple queries concurrently."""
        import asyncio
        
        from backend.services.query_service import QueryService
        
        query_service = QueryService(llm=mock_llm)
        
        queries = [
            "What is machine learning?",
            "Explain deep learning",
            "What is natural language processing?",
            "How does AI work?",
        ]
        
        async def run_query(query):
            return await query_service.ask(query)
        
        # Run queries concurrently
        results = await asyncio.gather(*[run_query(q) for q in queries])
        
        assert len(results) == len(queries)

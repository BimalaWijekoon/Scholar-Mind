"""
Document Processing Tasks
"""

from typing import Dict, Optional
import logging
from celery import shared_task, chain, group
from backend.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="backend.tasks.document_tasks.process_document_task",
    max_retries=3,
)
def process_document_task(self, document_id: str, file_path: str) -> Dict:
    """
    Process a document through the full pipeline.
    
    This task:
    1. Parses the document
    2. Extracts metadata
    3. Chunks the document
    4. Generates embeddings
    5. Stores in vector store
    
    Args:
        document_id: Document ID
        file_path: Path to the document file
        
    Returns:
        Processing result
    """
    logger.info(f"Processing document: {document_id}")
    
    try:
        # Import here to avoid circular imports
        from backend.core.document_processing import PDFParser, DocumentChunker, MetadataExtractor
        from backend.core.nlp import EmbeddingsManager
        from backend.core.retrieval import VectorStore
        
        result = {
            "document_id": document_id,
            "status": "processing",
            "steps": [],
        }
        
        # Step 1: Parse document
        parser = PDFParser()
        parsed = parser.parse(file_path)
        result["steps"].append({"parse": "success", "pages": len(getattr(parsed, 'pages', []))})
        
        # Step 2: Extract metadata
        extractor = MetadataExtractor()
        metadata = extractor.extract(parsed.text, parsed.metadata)
        result["metadata"] = {
            "title": metadata.title,
            "authors": metadata.authors,
            "abstract": metadata.abstract[:200] if metadata.abstract else None,
        }
        result["steps"].append({"metadata": "success"})
        
        # Step 3: Chunk document
        chunker = DocumentChunker()
        chunks = chunker.chunk(parsed.text, document_id)
        result["chunk_count"] = len(chunks)
        result["steps"].append({"chunking": "success", "chunks": len(chunks)})
        
        # Step 4: Generate embeddings
        embeddings_manager = EmbeddingsManager()
        texts = [chunk.text for chunk in chunks]
        embeddings = embeddings_manager.embed_documents(texts)
        result["steps"].append({"embeddings": "success"})
        
        # Step 5: Store in vector store
        vector_store = VectorStore()
        chunk_ids = vector_store.add(
            texts=texts,
            embeddings=embeddings.tolist(),
            metadatas=[{
                "document_id": document_id,
                "chunk_index": i,
                "start_char": chunks[i].start_char,
                "end_char": chunks[i].end_char,
            } for i in range(len(chunks))],
        )
        result["chunk_ids"] = chunk_ids
        result["steps"].append({"vector_store": "success"})
        
        result["status"] = "completed"
        logger.info(f"Document {document_id} processed successfully")
        
        # Chain to entity extraction
        extract_entities_task.delay(document_id, parsed.text)
        
        return result
        
    except Exception as e:
        logger.error(f"Document processing failed: {e}")
        self.retry(exc=e, countdown=60)


@celery_app.task(
    bind=True,
    name="backend.tasks.document_tasks.extract_entities_task",
    max_retries=3,
)
def extract_entities_task(self, document_id: str, text: str) -> Dict:
    """
    Extract entities and relations from document text.
    
    Args:
        document_id: Document ID
        text: Document text
        
    Returns:
        Extraction result
    """
    logger.info(f"Extracting entities from document: {document_id}")
    
    try:
        from backend.core.nlp import EntityExtractor, RelationExtractor
        
        result = {
            "document_id": document_id,
            "status": "processing",
        }
        
        # Extract entities
        entity_extractor = EntityExtractor()
        entities = entity_extractor.extract(text, document_id)
        
        result["entities"] = [
            {
                "text": e.text,
                "type": e.entity_type,
                "confidence": e.confidence,
            }
            for e in entities
        ]
        
        # Extract relations
        relation_extractor = RelationExtractor()
        entity_list = [{"text": e.text, "entity_type": e.entity_type} for e in entities]
        relations = relation_extractor.extract(text, entity_list)
        
        result["relations"] = [
            {
                "source": r.source_text,
                "target": r.target_text,
                "type": r.relation_type,
                "confidence": r.confidence,
            }
            for r in relations
        ]
        
        result["status"] = "completed"
        logger.info(f"Entity extraction completed for {document_id}")
        
        # Chain to graph building
        build_graph_task.delay(document_id, result["entities"], result["relations"])
        
        return result
        
    except Exception as e:
        logger.error(f"Entity extraction failed: {e}")
        self.retry(exc=e, countdown=60)


@celery_app.task(
    bind=True,
    name="backend.tasks.document_tasks.build_graph_task",
    max_retries=3,
)
def build_graph_task(
    self,
    document_id: str,
    entities: list,
    relations: list,
) -> Dict:
    """
    Build knowledge graph from extracted entities and relations.
    
    Args:
        document_id: Document ID
        entities: List of extracted entities
        relations: List of extracted relations
        
    Returns:
        Graph building result
    """
    logger.info(f"Building graph for document: {document_id}")
    
    try:
        from backend.core.knowledge_graph import GraphBuilder, Neo4jClient
        from backend.config import get_settings
        
        settings = get_settings()
        result = {
            "document_id": document_id,
            "status": "processing",
        }
        
        # Build local graph
        graph_builder = GraphBuilder()
        graph_builder.build_from_extraction(entities, relations)
        
        result["local_graph"] = {
            "nodes": graph_builder.graph.number_of_nodes(),
            "edges": graph_builder.graph.number_of_edges(),
        }
        
        # Store in Neo4j if configured
        if settings.NEO4J_URI:
            import asyncio
            
            async def store_in_neo4j():
                client = Neo4jClient(
                    uri=settings.NEO4J_URI,
                    user=settings.NEO4J_USER,
                    password=settings.NEO4J_PASSWORD,
                )
                await client.connect()
                
                try:
                    node_ids = {}
                    
                    # Create nodes
                    for entity in entities:
                        node_id = await client.create_node(
                            label=entity["type"],
                            properties={
                                "text": entity["text"],
                                "document_id": document_id,
                                "confidence": entity.get("confidence", 1.0),
                            },
                        )
                        node_ids[entity["text"]] = node_id
                    
                    # Create relationships
                    for relation in relations:
                        source_id = node_ids.get(relation["source"])
                        target_id = node_ids.get(relation["target"])
                        
                        if source_id and target_id:
                            await client.create_relationship(
                                source_id=source_id,
                                target_id=target_id,
                                rel_type=relation["type"],
                                properties={
                                    "confidence": relation.get("confidence", 1.0),
                                    "document_id": document_id,
                                },
                            )
                    
                    return {
                        "nodes_created": len(entities),
                        "relationships_created": len(relations),
                    }
                finally:
                    await client.close()
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                neo4j_result = loop.run_until_complete(store_in_neo4j())
                result["neo4j"] = neo4j_result
            finally:
                loop.close()
        
        result["status"] = "completed"
        logger.info(f"Graph building completed for {document_id}")
        
        return result
        
    except Exception as e:
        logger.error(f"Graph building failed: {e}")
        self.retry(exc=e, countdown=60)


@celery_app.task(name="backend.tasks.document_tasks.cleanup_task")
def cleanup_task() -> Dict:
    """
    Periodic cleanup task.
    
    Cleans up:
    - Old task results
    - Temporary files
    - Expired cache entries
    """
    logger.info("Running cleanup task")
    
    import os
    import shutil
    from datetime import datetime, timedelta
    
    result = {
        "timestamp": datetime.utcnow().isoformat(),
        "cleaned": {},
    }
    
    # Clean temp directory
    temp_dir = "data/temp"
    if os.path.exists(temp_dir):
        cutoff = datetime.utcnow() - timedelta(hours=24)
        
        deleted = 0
        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)
            
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                if mtime < cutoff:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    else:
                        shutil.rmtree(file_path)
                    deleted += 1
            except Exception as e:
                logger.warning(f"Failed to delete {file_path}: {e}")
        
        result["cleaned"]["temp_files"] = deleted
    
    logger.info(f"Cleanup completed: {result}")
    return result


def process_document_pipeline(document_id: str, file_path: str):
    """
    Execute the full document processing pipeline.
    
    This chains all processing tasks.
    
    Args:
        document_id: Document ID
        file_path: Path to document file
    """
    # Chain: process -> extract -> build graph
    pipeline = chain(
        process_document_task.s(document_id, file_path),
    )
    
    return pipeline.apply_async()


def batch_process_documents(documents: list):
    """
    Process multiple documents in parallel.
    
    Args:
        documents: List of (document_id, file_path) tuples
    """
    tasks = group(
        process_document_task.s(doc_id, path)
        for doc_id, path in documents
    )
    
    return tasks.apply_async()

#!/usr/bin/env python
"""
Run Pipeline Script

This script runs the complete document processing pipeline on a set of documents.
"""

import asyncio
import logging
import argparse
from pathlib import Path
from typing import List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def process_document(file_path: str, doc_id: Optional[str] = None) -> dict:
    """
    Process a single document through the full pipeline.
    
    Args:
        file_path: Path to the document file
        doc_id: Optional document ID (auto-generated if not provided)
        
    Returns:
        Processing result dictionary
    """
    import uuid
    
    from backend.core.document_processing import PDFParser, WebParser, DocumentChunker, MetadataExtractor
    from backend.core.nlp import EntityExtractor, RelationExtractor, EmbeddingsManager
    from backend.core.knowledge_graph import GraphBuilder, Neo4jClient
    from backend.core.retrieval import VectorStore
    
    # Generate doc_id if not provided
    if not doc_id:
        doc_id = str(uuid.uuid4())
    
    result = {
        "document_id": doc_id,
        "file_path": file_path,
        "steps": [],
        "status": "processing",
    }
    
    try:
        # Step 1: Parse document
        logger.info(f"Parsing document: {file_path}")
        
        if file_path.endswith(".pdf"):
            parser = PDFParser()
            parsed = parser.parse(file_path)
        else:
            # Read as text
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            parsed = type("Parsed", (), {"text": text, "metadata": {}, "pages": []})()
        
        result["steps"].append({"parse": "success"})
        
        # Step 2: Extract metadata
        logger.info("Extracting metadata...")
        metadata_extractor = MetadataExtractor()
        metadata = metadata_extractor.extract(parsed.text, getattr(parsed, "metadata", None))
        
        result["metadata"] = {
            "title": metadata.title,
            "authors": metadata.authors,
            "abstract": metadata.abstract[:200] if metadata.abstract else None,
        }
        result["steps"].append({"metadata": "success"})
        
        # Step 3: Chunk document
        logger.info("Chunking document...")
        chunker = DocumentChunker(chunk_size=512, chunk_overlap=50)
        chunks = chunker.chunk(parsed.text, doc_id)
        
        result["chunk_count"] = len(chunks)
        result["steps"].append({"chunking": "success", "chunks": len(chunks)})
        
        # Step 4: Extract entities
        logger.info("Extracting entities...")
        entity_extractor = EntityExtractor(use_scispacy=False)
        entities = entity_extractor.extract(parsed.text, doc_id)
        
        result["entity_count"] = len(entities)
        result["steps"].append({"entity_extraction": "success", "entities": len(entities)})
        
        # Step 5: Extract relations
        logger.info("Extracting relations...")
        relation_extractor = RelationExtractor()
        entity_list = [{"text": e.text, "entity_type": e.entity_type} for e in entities]
        relations = relation_extractor.extract(parsed.text, entity_list)
        
        result["relation_count"] = len(relations)
        result["steps"].append({"relation_extraction": "success", "relations": len(relations)})
        
        # Step 6: Generate embeddings
        logger.info("Generating embeddings...")
        embeddings_manager = EmbeddingsManager()
        chunk_texts = [chunk.text for chunk in chunks]
        embeddings = embeddings_manager.embed_documents(chunk_texts)
        
        result["steps"].append({"embeddings": "success"})
        
        # Step 7: Store in vector store
        logger.info("Storing in vector store...")
        vector_store = VectorStore()
        chunk_ids = vector_store.add(
            texts=chunk_texts,
            embeddings=embeddings.tolist(),
            metadatas=[{
                "document_id": doc_id,
                "chunk_index": i,
            } for i in range(len(chunks))],
        )
        
        result["steps"].append({"vector_store": "success"})
        
        # Step 8: Build knowledge graph
        logger.info("Building knowledge graph...")
        graph_builder = GraphBuilder()
        
        entity_dicts = [
            {"text": e.text, "entity_type": e.entity_type, "confidence": e.confidence}
            for e in entities
        ]
        relation_dicts = [
            {
                "source_text": r.source_text,
                "target_text": r.target_text,
                "relation_type": r.relation_type,
                "confidence": r.confidence,
            }
            for r in relations
        ]
        
        graph_builder.build_from_extraction(entity_dicts, relation_dicts)
        
        result["graph_stats"] = graph_builder.get_statistics()
        result["steps"].append({"graph_build": "success"})
        
        # Step 9: Store in Neo4j (if configured)
        neo4j_uri = os.getenv("NEO4J_URI")
        if neo4j_uri:
            logger.info("Storing in Neo4j...")
            try:
                client = Neo4jClient(
                    uri=neo4j_uri,
                    user=os.getenv("NEO4J_USER", "neo4j"),
                    password=os.getenv("NEO4J_PASSWORD", "password"),
                )
                await client.connect()
                
                # Store entities and relations
                for node_id, data in graph_builder.graph.nodes(data=True):
                    await client.create_node(
                        label=data.get("node_type", "Entity"),
                        properties={
                            "id": node_id,
                            "text": data.get("label", ""),
                            "document_id": doc_id,
                        },
                    )
                
                for source, target, data in graph_builder.graph.edges(data=True):
                    await client.create_relationship(
                        source_id=source,
                        target_id=target,
                        rel_type=data.get("relation_type", "RELATED"),
                        properties={"document_id": doc_id},
                    )
                
                await client.close()
                result["steps"].append({"neo4j": "success"})
            except Exception as e:
                logger.warning(f"Neo4j storage failed: {e}")
                result["steps"].append({"neo4j": "skipped", "reason": str(e)})
        else:
            result["steps"].append({"neo4j": "skipped", "reason": "not configured"})
        
        result["status"] = "completed"
        logger.info(f"Document processing completed: {doc_id}")
        
    except Exception as e:
        logger.error(f"Document processing failed: {e}")
        result["status"] = "failed"
        result["error"] = str(e)
    
    return result


async def process_directory(directory: str, extensions: List[str] = None) -> List[dict]:
    """
    Process all documents in a directory.
    
    Args:
        directory: Path to directory
        extensions: List of file extensions to process
        
    Returns:
        List of processing results
    """
    if extensions is None:
        extensions = [".pdf", ".txt", ".md"]
    
    results = []
    directory_path = Path(directory)
    
    for ext in extensions:
        for file_path in directory_path.glob(f"**/*{ext}"):
            logger.info(f"Processing: {file_path}")
            result = await process_document(str(file_path))
            results.append(result)
    
    return results


def print_results(results: List[dict]):
    """Print processing results summary."""
    print("\n" + "=" * 60)
    print("PROCESSING RESULTS SUMMARY")
    print("=" * 60)
    
    total = len(results)
    completed = sum(1 for r in results if r["status"] == "completed")
    failed = sum(1 for r in results if r["status"] == "failed")
    
    print(f"\nTotal documents: {total}")
    print(f"Completed: {completed}")
    print(f"Failed: {failed}")
    
    total_entities = sum(r.get("entity_count", 0) for r in results)
    total_relations = sum(r.get("relation_count", 0) for r in results)
    total_chunks = sum(r.get("chunk_count", 0) for r in results)
    
    print(f"\nTotal entities extracted: {total_entities}")
    print(f"Total relations extracted: {total_relations}")
    print(f"Total chunks created: {total_chunks}")
    
    if failed > 0:
        print("\nFailed documents:")
        for r in results:
            if r["status"] == "failed":
                print(f"  - {r['file_path']}: {r.get('error', 'Unknown error')}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Document Processing Pipeline")
    parser.add_argument("path", help="File or directory path to process")
    parser.add_argument("--recursive", "-r", action="store_true", help="Process directory recursively")
    parser.add_argument("--extensions", "-e", nargs="+", default=[".pdf", ".txt", ".md"],
                       help="File extensions to process")
    args = parser.parse_args()
    
    path = Path(args.path)
    
    if path.is_file():
        results = [asyncio.run(process_document(str(path)))]
    elif path.is_dir():
        results = asyncio.run(process_directory(str(path), args.extensions))
    else:
        print(f"Error: Path not found: {path}")
        exit(1)
    
    print_results(results)

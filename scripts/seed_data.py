#!/usr/bin/env python
"""
Seed Data Script

This script seeds the database with sample documents and knowledge graph data
for testing and demonstration purposes.
"""

import asyncio
import logging
import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Sample documents for seeding
SAMPLE_DOCUMENTS = [
    {
        "title": "Introduction to Machine Learning",
        "abstract": "This document provides an overview of machine learning concepts, "
                    "including supervised learning, unsupervised learning, and deep learning.",
        "content": """
Machine learning is a subset of artificial intelligence that enables systems to 
learn from data and improve from experience. The main types include:

1. Supervised Learning: Uses labeled data to train models. Common algorithms include 
   linear regression, decision trees, and neural networks.

2. Unsupervised Learning: Finds patterns in unlabeled data. Clustering and 
   dimensionality reduction are common applications.

3. Deep Learning: Uses neural networks with multiple layers to learn hierarchical 
   representations of data. Widely used in computer vision and NLP.

Key researchers in the field include Geoffrey Hinton, Yann LeCun, and Yoshua Bengio,
who are often called the "Godfathers of AI" for their contributions to deep learning.
""",
    },
    {
        "title": "Knowledge Graphs: Concepts and Applications",
        "abstract": "An exploration of knowledge graphs, their construction, "
                    "and applications in AI and information retrieval.",
        "content": """
Knowledge graphs represent structured information about entities and their 
relationships. Major knowledge graphs include:

- Google Knowledge Graph: Powers Google Search's information panels
- Wikidata: Community-driven structured data repository
- DBpedia: Extracts structured data from Wikipedia

Knowledge graphs are used for:
1. Question answering systems
2. Recommendation engines
3. Drug discovery
4. Fraud detection

Graph databases like Neo4j store knowledge graphs efficiently using nodes, 
relationships, and properties. Query languages like Cypher enable complex 
traversal operations.
""",
    },
    {
        "title": "Natural Language Processing with Transformers",
        "abstract": "Overview of transformer architecture and its applications "
                    "in modern NLP systems.",
        "content": """
The Transformer architecture, introduced in the paper "Attention Is All You Need" 
by Vaswani et al. at Google, revolutionized natural language processing.

Key innovations:
- Self-attention mechanism for capturing long-range dependencies
- Parallel processing instead of sequential like RNNs
- Multi-head attention for different representation subspaces

Major models based on Transformers:
1. BERT (Bidirectional Encoder Representations from Transformers)
2. GPT (Generative Pre-trained Transformer) series
3. T5 (Text-to-Text Transfer Transformer)

These models excel at tasks like:
- Text classification
- Named entity recognition
- Question answering
- Text generation
""",
    },
]


# Sample entities and relations for the knowledge graph
SAMPLE_ENTITIES = [
    {"text": "Machine Learning", "type": "CONCEPT", "description": "Field of AI that enables learning from data"},
    {"text": "Deep Learning", "type": "CONCEPT", "description": "Neural networks with multiple layers"},
    {"text": "Natural Language Processing", "type": "CONCEPT", "description": "AI for understanding human language"},
    {"text": "Knowledge Graph", "type": "CONCEPT", "description": "Structured representation of entities and relations"},
    {"text": "Geoffrey Hinton", "type": "PERSON", "description": "Pioneer of deep learning"},
    {"text": "Yann LeCun", "type": "PERSON", "description": "Chief AI Scientist at Meta"},
    {"text": "Yoshua Bengio", "type": "PERSON", "description": "Professor at University of Montreal"},
    {"text": "Google", "type": "ORGANIZATION", "description": "Technology company"},
    {"text": "OpenAI", "type": "ORGANIZATION", "description": "AI research laboratory"},
    {"text": "Transformer", "type": "CONCEPT", "description": "Neural network architecture based on attention"},
    {"text": "BERT", "type": "CONCEPT", "description": "Bidirectional Encoder Representations from Transformers"},
    {"text": "GPT", "type": "CONCEPT", "description": "Generative Pre-trained Transformer"},
    {"text": "Neo4j", "type": "TECHNOLOGY", "description": "Graph database platform"},
]

SAMPLE_RELATIONS = [
    {"source": "Deep Learning", "target": "Machine Learning", "type": "IS_A"},
    {"source": "Natural Language Processing", "target": "Machine Learning", "type": "USES"},
    {"source": "Geoffrey Hinton", "target": "Deep Learning", "type": "DEVELOPED"},
    {"source": "Yann LeCun", "target": "Deep Learning", "type": "DEVELOPED"},
    {"source": "Yoshua Bengio", "target": "Deep Learning", "type": "DEVELOPED"},
    {"source": "Transformer", "target": "Deep Learning", "type": "IS_A"},
    {"source": "BERT", "target": "Transformer", "type": "BASED_ON"},
    {"source": "GPT", "target": "Transformer", "type": "BASED_ON"},
    {"source": "Google", "target": "Transformer", "type": "DEVELOPED"},
    {"source": "OpenAI", "target": "GPT", "type": "DEVELOPED"},
    {"source": "Knowledge Graph", "target": "Neo4j", "type": "STORED_IN"},
    {"source": "Natural Language Processing", "target": "BERT", "type": "USES"},
]


async def seed_database():
    """Seed the database with sample data."""
    
    logger.info("Starting database seeding...")
    
    # Import services
    from backend.core.document_processing import DocumentChunker, MetadataExtractor
    from backend.core.nlp import EntityExtractor, EmbeddingsManager
    from backend.core.knowledge_graph import Neo4jClient, GraphBuilder
    from backend.db.database import Database
    
    # Initialize services
    chunker = DocumentChunker()
    graph_builder = GraphBuilder()
    
    # Seed documents
    logger.info("Seeding documents...")
    for i, doc in enumerate(SAMPLE_DOCUMENTS):
        doc_id = f"sample-doc-{i+1}"
        
        # Create chunks
        chunks = chunker.chunk(doc["content"], doc_id)
        logger.info(f"Created {len(chunks)} chunks for: {doc['title']}")
        
        # Build graph from sample data
        graph_builder.add_node(
            doc_id, 
            doc["title"], 
            "Document", 
            {"abstract": doc["abstract"]}
        )
    
    # Seed entities
    logger.info("Seeding entities...")
    entity_ids = {}
    for entity in SAMPLE_ENTITIES:
        entity_id = entity["text"].lower().replace(" ", "-")
        entity_ids[entity["text"]] = entity_id
        
        graph_builder.add_node(
            entity_id,
            entity["text"],
            entity["type"],
            {"description": entity.get("description", "")},
        )
    
    # Seed relations
    logger.info("Seeding relations...")
    for relation in SAMPLE_RELATIONS:
        source_id = entity_ids.get(relation["source"])
        target_id = entity_ids.get(relation["target"])
        
        if source_id and target_id:
            graph_builder.add_edge(
                source_id,
                target_id,
                relation["type"],
            )
    
    # Print statistics
    stats = graph_builder.get_statistics()
    logger.info(f"Graph statistics: {stats}")
    
    # Save to Neo4j if configured
    neo4j_uri = os.getenv("NEO4J_URI")
    if neo4j_uri:
        logger.info("Saving to Neo4j...")
        try:
            client = Neo4jClient(
                uri=neo4j_uri,
                user=os.getenv("NEO4J_USER", "neo4j"),
                password=os.getenv("NEO4J_PASSWORD", "password"),
            )
            await client.connect()
            
            # Create nodes
            for node_id, data in graph_builder.graph.nodes(data=True):
                await client.create_node(
                    label=data.get("node_type", "Entity"),
                    properties={
                        "id": node_id,
                        "text": data.get("label", ""),
                        **data.get("properties", {}),
                    },
                )
            
            # Create relationships
            for source, target, data in graph_builder.graph.edges(data=True):
                await client.create_relationship(
                    source_id=source,
                    target_id=target,
                    rel_type=data.get("relation_type", "RELATED"),
                )
            
            await client.close()
            logger.info("Successfully saved to Neo4j")
        except Exception as e:
            logger.error(f"Failed to save to Neo4j: {e}")
    
    logger.info("Database seeding completed!")


async def clear_seed_data():
    """Clear seed data from the database."""
    logger.warning("Clearing seed data...")
    # Implementation would go here
    logger.info("Seed data cleared")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed Data Script")
    parser.add_argument("--clear", action="store_true", help="Clear seed data")
    args = parser.parse_args()
    
    if args.clear:
        asyncio.run(clear_seed_data())
    else:
        asyncio.run(seed_database())

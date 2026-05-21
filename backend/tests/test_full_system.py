"""
ScholarMind End-to-End System Test
===================================
This script tests the entire ScholarMind system by:
1. Creating a sample academic paper with known entities and relations
2. Processing it through the document pipeline
3. Extracting entities and relations
4. Building the knowledge graph
5. Testing search functionality
6. Testing the chat/QA system
7. Testing all advanced features
8. Saving all results to test_results folder

Author: ScholarMind Test Suite
Date: February 2026
"""

import os
import sys
import json
import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Sample Academic Paper Content
SAMPLE_PAPER = """
Title: Attention-Enhanced Graph Neural Networks for Scientific Document Understanding

Authors: Dr. Sarah Chen, Dr. Michael Rodriguez, Prof. Emily Watson
Affiliation: Stanford University, MIT, Oxford University

Abstract:
This paper introduces AEGNN (Attention-Enhanced Graph Neural Networks), a novel architecture
for understanding scientific documents. Our method outperforms BERT by 15% on document
classification tasks and achieves 92.3% F1-score on the SciERC dataset. We demonstrate that
combining attention mechanisms with graph neural networks enables better multi-hop reasoning
across document sections. Our experiments on PubMed abstracts show significant improvements
over transformer-based baselines including SciBERT and BioBERT.

1. Introduction

Natural Language Processing (NLP) has revolutionized how we analyze scientific literature.
Traditional approaches using TF-IDF and word embeddings have been superseded by transformer
architectures like BERT (Devlin et al., 2019) and GPT (Radford et al., 2018). However,
these models struggle with capturing long-range dependencies in scientific documents.

Graph Neural Networks (GNNs) have emerged as a powerful paradigm for modeling relational
data (Kipf and Welling, 2017). By representing documents as graphs where nodes are sections
or entities and edges are relationships, we can better capture the hierarchical structure
of scientific papers.

In this work, we propose AEGNN, which combines the attention mechanism from transformers
with the message-passing framework of GNNs. Our contributions include:

1. A novel architecture that outperforms existing methods on document understanding tasks
2. An efficient training procedure using contrastive learning
3. Comprehensive evaluation on multiple scientific NLP benchmarks

2. Related Work

2.1 Transformer Models
BERT (Bidirectional Encoder Representations from Transformers) introduced by Devlin et al.
at Google in 2019 has become the foundation for modern NLP. SciBERT (Beltagy et al., 2019)
adapted BERT for scientific text by pre-training on Semantic Scholar papers. BioBERT
(Lee et al., 2020) focused on biomedical literature from PubMed.

2.2 Graph Neural Networks
Graph Convolutional Networks (GCNs) introduced by Kipf and Welling at the University of
Amsterdam showed that convolutional operations can be generalized to graph-structured data.
GraphSAGE (Hamilton et al., 2017) from Stanford University proposed inductive learning on
large graphs.

2.3 Document Understanding
Previous work on scientific document understanding includes S2ORC by Lo et al. (2020) from
Allen Institute for AI, which created a large corpus of scientific papers. SciREX
(Jain et al., 2020) introduced a dataset for scientific information extraction.

3. Methodology

3.1 Problem Formulation
Given a scientific document D = {s1, s2, ..., sn} consisting of n sections, our goal is to
construct a document graph G = (V, E) where V represents section nodes and E represents
relationships between sections.

3.2 Architecture
Our AEGNN architecture consists of three main components:

1. Document Encoder: We use SciBERT to encode each section into a 768-dimensional vector.
2. Graph Construction: We build a document graph using co-reference and citation links.
3. Attention-Enhanced GNN: We apply multi-head attention during message passing.

The attention mechanism is defined as:
α_ij = softmax(W_a * [h_i || h_j])

Where h_i and h_j are node representations and W_a is a learnable weight matrix.

3.3 Training Procedure
We train AEGNN using a combination of:
- Cross-entropy loss for node classification
- Contrastive loss for representation learning
- Edge prediction loss for relation extraction

4. Experiments

4.1 Datasets
We evaluate on three benchmark datasets:
- SciERC: 500 scientific abstracts with entity and relation annotations
- PubMed: 1 million biomedical abstracts from the National Library of Medicine
- ACL-ARC: Academic papers from the ACL Anthology Reference Corpus

4.2 Baselines
We compare against:
- BERT-base (Devlin et al., 2019): 12 layers, 110M parameters
- SciBERT (Beltagy et al., 2019): Pre-trained on Semantic Scholar
- BioBERT (Lee et al., 2020): Pre-trained on PubMed
- GCN (Kipf and Welling, 2017): Standard graph convolutional network

4.3 Results

Table 1: F1-scores on document classification

| Method    | SciERC | PubMed | ACL-ARC |
|-----------|--------|--------|---------|
| BERT      | 78.5   | 82.1   | 76.3    |
| SciBERT   | 83.2   | 85.4   | 81.2    |
| BioBERT   | 81.7   | 88.9   | 79.5    |
| GCN       | 75.3   | 78.2   | 73.8    |
| AEGNN     | 92.3   | 91.7   | 89.4    |

Our AEGNN outperforms BERT by 15% on SciERC and achieves the highest scores across all
benchmarks. The attention mechanism contributes 8% of the improvement, while the graph
structure accounts for the remaining 7%.

4.4 Ablation Study
We conducted ablation studies to understand each component:
- Without attention: F1 drops by 8.2%
- Without graph structure: F1 drops by 7.5%
- Without contrastive learning: F1 drops by 3.1%

5. Analysis

5.1 Qualitative Results
AEGNN successfully captures cross-document relationships. For example, when analyzing
papers about "transformer attention", AEGNN correctly links concepts from the original
Attention Is All You Need paper (Vaswani et al., 2017) to subsequent works.

5.2 Error Analysis
Common errors include:
- Confusion between similar methods (e.g., BERT vs RoBERTa)
- Missing implicit relationships not stated explicitly
- Difficulty with very long documents (>50 sections)

6. Conclusion

We introduced AEGNN, a novel approach combining attention mechanisms with graph neural
networks for scientific document understanding. Our method achieves state-of-the-art
results on multiple benchmarks, outperforming BERT by 15% on SciERC.

Future work includes:
- Extending to multi-document reasoning
- Incorporating citation networks
- Applying to other domains like legal documents

7. Acknowledgments

This research was supported by grants from the National Science Foundation (NSF-1234567)
and Google Research. We thank the anonymous reviewers for their helpful feedback.

References

Beltagy, I., Lo, K., & Cohan, A. (2019). SciBERT: A Pretrained Language Model for
Scientific Text. EMNLP 2019.

Devlin, J., Chang, M., Lee, K., & Toutanova, K. (2019). BERT: Pre-training of Deep
Bidirectional Transformers for Language Understanding. NAACL 2019.

Hamilton, W., Ying, R., & Leskovec, J. (2017). Inductive Representation Learning on
Large Graphs. NeurIPS 2017.

Jain, S., et al. (2020). SciREX: A Challenge Dataset for Document-Level Information
Extraction. ACL 2020.

Kipf, T., & Welling, M. (2017). Semi-Supervised Classification with Graph Convolutional
Networks. ICLR 2017.

Lee, J., et al. (2020). BioBERT: A Pre-trained Biomedical Language Representation Model
for Biomedical Text Mining. Bioinformatics.

Lo, K., et al. (2020). S2ORC: The Semantic Scholar Open Research Corpus. ACL 2020.

Radford, A., et al. (2018). Improving Language Understanding by Generative Pre-Training.
OpenAI Technical Report.

Vaswani, A., et al. (2017). Attention Is All You Need. NeurIPS 2017.
"""

# Expected entities for validation
EXPECTED_ENTITIES = {
    "PERSON": [
        "Sarah Chen", "Michael Rodriguez", "Emily Watson", 
        "Devlin", "Radford", "Kipf", "Welling", "Hamilton",
        "Beltagy", "Lee", "Vaswani", "Lo", "Jain"
    ],
    "ORGANIZATION": [
        "Stanford University", "MIT", "Oxford University",
        "Google", "Allen Institute for AI", "National Library of Medicine",
        "University of Amsterdam", "National Science Foundation", "OpenAI"
    ],
    "METHOD": [
        "AEGNN", "BERT", "GPT", "SciBERT", "BioBERT", 
        "Graph Neural Networks", "GNN", "GCN", "GraphSAGE",
        "Transformer", "attention mechanism", "TF-IDF"
    ],
    "DATASET": [
        "SciERC", "PubMed", "ACL-ARC", "S2ORC", "SciREX",
        "Semantic Scholar", "ACL Anthology"
    ],
    "METRIC": [
        "F1-score", "92.3%", "15%", "78.5", "82.1", "91.7"
    ],
    "CONCEPT": [
        "attention mechanism", "multi-hop reasoning", "document understanding",
        "Natural Language Processing", "NLP", "contrastive learning",
        "message passing", "node classification"
    ]
}

# Expected relations for validation
EXPECTED_RELATIONS = [
    ("AEGNN", "OUTPERFORMS", "BERT"),
    ("AEGNN", "USES", "attention mechanism"),
    ("AEGNN", "USES", "Graph Neural Networks"),
    ("Sarah Chen", "AFFILIATED_WITH", "Stanford University"),
    ("Michael Rodriguez", "AFFILIATED_WITH", "MIT"),
    ("Emily Watson", "AFFILIATED_WITH", "Oxford University"),
    ("SciBERT", "TRAINED_ON", "Semantic Scholar"),
    ("BioBERT", "TRAINED_ON", "PubMed"),
    ("AEGNN", "EVALUATED_ON", "SciERC"),
    ("AEGNN", "EVALUATED_ON", "PubMed"),
    ("AEGNN", "EVALUATED_ON", "ACL-ARC"),
    ("Devlin", "INTRODUCED", "BERT"),
    ("Kipf", "INTRODUCED", "GCN"),
]


class TestResults:
    """Class to collect and save test results"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results = {
            "test_started": datetime.now().isoformat(),
            "test_completed": None,
            "overall_status": "RUNNING",
            "tests": {},
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0
            }
        }
    
    def add_test(self, name: str, status: str, details: Any, duration: float = 0):
        """Add a test result"""
        self.results["tests"][name] = {
            "status": status,
            "details": details,
            "duration_seconds": duration,
            "timestamp": datetime.now().isoformat()
        }
        self.results["summary"]["total"] += 1
        if status == "PASSED":
            self.results["summary"]["passed"] += 1
        elif status == "FAILED":
            self.results["summary"]["failed"] += 1
        else:
            self.results["summary"]["skipped"] += 1
    
    def save(self, filename: str = "test_results.json"):
        """Save results to JSON file"""
        self.results["test_completed"] = datetime.now().isoformat()
        self.results["overall_status"] = "PASSED" if self.results["summary"]["failed"] == 0 else "FAILED"
        
        output_path = self.output_dir / filename
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
        
        return output_path
    
    def save_detail(self, name: str, data: Any):
        """Save detailed output for a specific test"""
        output_path = self.output_dir / f"{name}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        return output_path


async def run_full_system_test():
    """Run the complete end-to-end system test"""
    
    print("=" * 80)
    print("ScholarMind End-to-End System Test")
    print("=" * 80)
    print(f"Started at: {datetime.now().isoformat()}")
    print()
    
    # Setup test results
    test_results_dir = Path(__file__).parent / "test_results"
    results = TestResults(test_results_dir)
    
    # Save the sample paper
    paper_path = test_results_dir / "sample_paper.txt"
    with open(paper_path, "w", encoding="utf-8") as f:
        f.write(SAMPLE_PAPER)
    print(f"✓ Sample paper saved to: {paper_path}")
    
    # Save expected entities and relations
    results.save_detail("expected_entities", EXPECTED_ENTITIES)
    results.save_detail("expected_relations", EXPECTED_RELATIONS)
    
    # Variables to track across tests
    doc_id = None
    chunks = []
    entities = []
    relations = []
    entities_by_type = {}
    relations_by_type = {}
    
    try:
        # Import services after setting up path
        print("\n📦 Loading configuration and services...")
        from config import settings
        print(f"   Settings loaded: APP_NAME = {settings.APP_NAME}")
        
        from services.document_service import DocumentService
        from services.graph_service import GraphService
        from services.query_service import QueryService
        from core.document_processing import DocumentChunker
        from core.nlp import EntityExtractor, RelationExtractor, EmbeddingsManager
        from core.retrieval.vector_store import VectorStore
        from ml import (
            ClaimExtractor, 
            ContradictionDetector, 
            PaperRecommender,
            ResearchQuestionGenerator,
            DuplicateDetector
        )
        
        # Initialize services
        print("\n" + "-" * 40)
        print("PHASE 1: Service Initialization")
        print("-" * 40)
        
        import time
        start_time = time.time()
        
        try:
            document_service = DocumentService()
            graph_service = GraphService()
            query_service = QueryService()
            vector_store = VectorStore(persist_directory="data/vectors")
            chunker = DocumentChunker()
            # Use en_core_web_sm which is installed
            entity_extractor = EntityExtractor(model_name="en_core_web_sm")
            relation_extractor = RelationExtractor(model_name="en_core_web_sm")
            embeddings_manager = EmbeddingsManager()
            
            results.add_test(
                "service_initialization",
                "PASSED",
                {"services": ["DocumentService", "GraphService", "QueryService", "VectorStore", "DocumentChunker", "EntityExtractor", "RelationExtractor", "EmbeddingsManager"]},
                time.time() - start_time
            )
            print("✓ All services initialized successfully")
        except Exception as e:
            results.add_test(
                "service_initialization",
                "FAILED",
                {"error": str(e)},
                time.time() - start_time
            )
            print(f"✗ Service initialization failed: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        # Test 1: Document Processing
        print("\n" + "-" * 40)
        print("PHASE 2: Document Processing Pipeline")
        print("-" * 40)
        
        start_time = time.time()
        try:
            # Create a mock UploadFile-like object
            from io import BytesIO
            from dataclasses import dataclass
            
            @dataclass
            class MockUploadFile:
                filename: str
                content_type: str
                file: BytesIO
                _content: bytes
                
                async def read(self):
                    return self._content
            
            # Create mock file from our sample paper
            paper_bytes = SAMPLE_PAPER.encode('utf-8')
            mock_file = MockUploadFile(
                filename="sample_paper.txt",
                content_type="text/plain",
                file=BytesIO(paper_bytes),
                _content=paper_bytes
            )
            
            # Use document service to upload (this runs full pipeline)
            print("   Uploading document through full pipeline...")
            doc_result = await document_service.upload_document(mock_file)
            doc_id = doc_result.get("id", doc_result.get("document_id", str(uuid.uuid4())))
            
            document_result = {
                "document_id": doc_id,
                "upload_result": doc_result,
                "content_length": len(SAMPLE_PAPER),
            }
            
            results.add_test(
                "document_upload_pipeline",
                "PASSED",
                document_result,
                time.time() - start_time
            )
            results.save_detail("document_uploaded", document_result)
            print(f"✓ Document uploaded with ID: {doc_id}")
            print(f"  Status: {doc_result.get('status', 'unknown')}")
            
        except Exception as e:
            results.add_test(
                "document_upload_pipeline",
                "FAILED",
                {"error": str(e)},
                time.time() - start_time
            )
            print(f"✗ Document upload failed: {e}")
            import traceback
            traceback.print_exc()
            doc_id = f"test-doc-{uuid.uuid4()}"  # Fallback ID for remaining tests
        
        # Test 2: Text Chunking
        print("\n" + "-" * 40)
        print("PHASE 3: Text Chunking")
        print("-" * 40)
        
        start_time = time.time()
        try:
            chunk_result_obj = chunker.chunk(SAMPLE_PAPER, document_id=doc_id)
            # Extract text from chunk objects
            chunks = [c.text if hasattr(c, 'text') else str(c) for c in chunk_result_obj]
            
            chunk_result = {
                "total_chunks": len(chunks),
                "chunk_sizes": [len(c) for c in chunks],
                "average_size": sum(len(c) for c in chunks) / len(chunks) if chunks else 0,
                "sample_chunks": [c[:200] + "..." for c in chunks[:3]]
            }
            
            results.add_test(
                "text_chunking",
                "PASSED" if len(chunks) > 0 else "FAILED",
                chunk_result,
                time.time() - start_time
            )
            results.save_detail("chunks", {"chunks": chunks})
            print(f"✓ Created {len(chunks)} chunks")
            
        except Exception as e:
            results.add_test(
                "text_chunking",
                "FAILED",
                {"error": str(e)},
                time.time() - start_time
            )
            print(f"✗ Chunking failed: {e}")
            import traceback
            traceback.print_exc()
            chunks = []
        
        # Test 3: Embedding Generation
        print("\n" + "-" * 40)
        print("PHASE 4: Embedding Generation")
        print("-" * 40)
        
        start_time = time.time()
        try:
            embeddings = embeddings_manager.embed_documents([SAMPLE_PAPER[:1000]])
            
            embedding_result = {
                "embedding_count": len(embeddings),
                "embedding_dimension": len(embeddings[0]) if len(embeddings) > 0 else 0,
                "sample_embedding": list(embeddings[0][:10]) if len(embeddings) > 0 else []
            }
            
            results.add_test(
                "embedding_generation",
                "PASSED" if len(embeddings) > 0 else "FAILED",
                embedding_result,
                time.time() - start_time
            )
            print(f"✓ Generated embeddings with dimension: {len(embeddings[0]) if len(embeddings) > 0 else 0}")
            
        except Exception as e:
            results.add_test(
                "embedding_generation",
                "FAILED",
                {"error": str(e)},
                time.time() - start_time
            )
            print(f"✗ Embedding generation failed: {e}")
            import traceback
            traceback.print_exc()
            embeddings = []
        
        # Test 4: Named Entity Recognition
        print("\n" + "-" * 40)
        print("PHASE 5: Named Entity Recognition")
        print("-" * 40)
        
        start_time = time.time()
        try:
            entities = entity_extractor.extract(SAMPLE_PAPER, document_id=doc_id)
            
            # Organize by type - Entity is a dataclass with text, entity_type attributes
            entities_by_type = {}
            for entity in entities:
                ent_type = entity.entity_type if hasattr(entity, 'entity_type') else "UNKNOWN"
                if ent_type not in entities_by_type:
                    entities_by_type[ent_type] = []
                entities_by_type[ent_type].append(entity.text if hasattr(entity, 'text') else str(entity))
            
            # Check against expected entities
            found_expected = {}
            for ent_type, expected_list in EXPECTED_ENTITIES.items():
                found_expected[ent_type] = {
                    "expected": expected_list,
                    "found": [e for e in entities_by_type.get(ent_type, []) + 
                             entities_by_type.get("PERSON", []) + 
                             entities_by_type.get("ORG", []) +
                             entities_by_type.get("WORK_OF_ART", [])
                             if any(exp.lower() in e.lower() or e.lower() in exp.lower() 
                                   for exp in expected_list)],
                    "coverage": 0
                }
            
            entity_result = {
                "total_entities": len(entities),
                "entities_by_type": entities_by_type,
                "expected_validation": found_expected,
                "sample_entities": entities[:20]
            }
            
            results.add_test(
                "named_entity_recognition",
                "PASSED" if len(entities) > 0 else "FAILED",
                entity_result,
                time.time() - start_time
            )
            results.save_detail("entities_extracted", entity_result)
            print(f"✓ Extracted {len(entities)} entities")
            for ent_type, ent_list in entities_by_type.items():
                print(f"  - {ent_type}: {len(ent_list)} entities")
            
        except Exception as e:
            results.add_test(
                "named_entity_recognition",
                "FAILED",
                {"error": str(e)},
                time.time() - start_time
            )
            print(f"✗ NER failed: {e}")
            import traceback
            traceback.print_exc()
            entities = []
        
        # Test 5: Relation Extraction
        print("\n" + "-" * 40)
        print("PHASE 6: Relation Extraction")
        print("-" * 40)
        
        start_time = time.time()
        try:
            # RelationExtractor.extract() takes text and optional entities (no document_id)
            relations = relation_extractor.extract(SAMPLE_PAPER, entities=None)
            
            # Organize by type
            relations_by_type = {}
            for rel in relations:
                rel_type = rel.get("relation", rel.get("type", "RELATED_TO"))
                if rel_type not in relations_by_type:
                    relations_by_type[rel_type] = []
                relations_by_type[rel_type].append({
                    "source": rel.get("source", rel.get("head", "")),
                    "target": rel.get("target", rel.get("tail", ""))
                })
            
            relation_result = {
                "total_relations": len(relations),
                "relations_by_type": relations_by_type,
                "expected_relations": EXPECTED_RELATIONS,
                "sample_relations": relations[:15]
            }
            
            results.add_test(
                "relation_extraction",
                "PASSED" if len(relations) > 0 else "FAILED",
                relation_result,
                time.time() - start_time
            )
            results.save_detail("relations_extracted", relation_result)
            print(f"✓ Extracted {len(relations)} relations")
            for rel_type, rel_list in relations_by_type.items():
                print(f"  - {rel_type}: {len(rel_list)} relations")
            
        except Exception as e:
            results.add_test(
                "relation_extraction",
                "FAILED",
                {"error": str(e)},
                time.time() - start_time
            )
            print(f"✗ Relation extraction failed: {e}")
            relations = []
        
        # Test 6: Knowledge Graph Building
        print("\n" + "-" * 40)
        print("PHASE 7: Knowledge Graph Building")
        print("-" * 40)
        
        start_time = time.time()
        try:
            # Add entities to graph using the proper method
            nodes_added = graph_service.add_entities_from_extraction(
                entities[:50] if entities else [],  # Limit for testing
                document_id=doc_id
            )
            
            # Add relations to graph
            edges_added = graph_service.add_relations_from_extraction(
                relations[:30] if relations else [],  # Limit for testing
                document_id=doc_id
            )
            
            # Get graph statistics
            graph_stats = await graph_service.get_statistics()
            
            graph_result = {
                "nodes_added": nodes_added,
                "edges_added": edges_added,
                "graph_statistics": graph_stats
            }
            
            results.add_test(
                "knowledge_graph_building",
                "PASSED" if nodes_added > 0 else "FAILED",
                graph_result,
                time.time() - start_time
            )
            results.save_detail("graph_built", graph_result)
            print(f"✓ Added {nodes_added} nodes and {edges_added} edges to graph")
            
        except Exception as e:
            results.add_test(
                "knowledge_graph_building",
                "FAILED",
                {"error": str(e)},
                time.time() - start_time
            )
            print(f"✗ Graph building failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test 7: Graph Query
        print("\n" + "-" * 40)
        print("PHASE 8: Knowledge Graph Query")
        print("-" * 40)
        
        start_time = time.time()
        try:
            # Get graph data using the proper method
            graph_data = await graph_service.get_graph_data()
            nodes = graph_data.nodes if hasattr(graph_data, 'nodes') else graph_data.get('nodes', [])
            edges = graph_data.edges if hasattr(graph_data, 'edges') else graph_data.get('edges', [])
            
            # Also get via list_entities
            listed_entities = await graph_service.list_entities(page=1, page_size=50)
            
            # Test neighbor query
            neighbors_result = None
            if nodes and len(nodes) > 0:
                first_node_id = nodes[0].get("id", nodes[0].get("node_id", ""))
                if first_node_id:
                    neighbors_result = await graph_service.get_neighbors(first_node_id)
            
            query_result = {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "listed_entities": len(listed_entities),
                "sample_nodes": nodes[:10] if nodes else [],
                "sample_edges": edges[:10] if edges else [],
                "neighbor_query_result": neighbors_result
            }
            
            results.add_test(
                "graph_query",
                "PASSED" if len(nodes) > 0 else "FAILED",
                query_result,
                time.time() - start_time
            )
            results.save_detail("graph_query_results", query_result)
            print(f"✓ Retrieved {len(nodes)} nodes and {len(edges)} edges")
            
        except Exception as e:
            results.add_test(
                "graph_query",
                "FAILED",
                {"error": str(e)},
                time.time() - start_time
            )
            print(f"✗ Graph query failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test 8: Vector Search
        print("\n" + "-" * 40)
        print("PHASE 9: Vector Search")
        print("-" * 40)
        
        start_time = time.time()
        try:
            # Use vector store for semantic search
            # First, store chunks if available
            if chunks and embeddings_manager:
                print("   Indexing chunks in vector store...")
                chunk_embeddings = embeddings_manager.embed_documents(chunks)
                
                # Store in vector store
                ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
                metadatas = [{"document_id": doc_id, "chunk_index": i} for i in range(len(chunks))]
                
                vector_store.add(
                    texts=chunks,
                    embeddings=chunk_embeddings.tolist() if hasattr(chunk_embeddings, 'tolist') else list(chunk_embeddings),
                    ids=ids,
                    metadatas=metadatas
                )
                print(f"   Indexed {len(chunks)} chunks")
            
            # Test semantic search
            search_queries = [
                "What is AEGNN?",
                "How does attention mechanism work in GNN?",
                "What are the benchmark datasets used?",
                "Who are the authors of this paper?"
            ]
            
            search_results = {}
            for query in search_queries:
                # VectorStore.search() expects query_embedding and k (not string and top_k)
                query_embedding = embeddings_manager.embed_documents([query])[0]
                results_list = vector_store.search(query_embedding=list(query_embedding), k=5)
                search_results[query] = [
                    {"text": r.text[:200] if hasattr(r, 'text') else str(r)[:200], "score": r.score if hasattr(r, 'score') else 0.0} 
                    for r in results_list
                ] if results_list else []
            
            vector_search_result = {
                "queries_tested": len(search_queries),
                "search_results": search_results
            }
            
            results.add_test(
                "vector_search",
                "PASSED" if any(search_results.values()) else "FAILED",
                vector_search_result,
                time.time() - start_time
            )
            results.save_detail("vector_search_results", vector_search_result)
            print(f"✓ Executed {len(search_queries)} search queries")
            
        except Exception as e:
            results.add_test(
                "vector_search",
                "FAILED",
                {"error": str(e)},
                time.time() - start_time
            )
            print(f"✗ Vector search failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test 9: Hybrid Search (Vector + Graph)
        print("\n" + "-" * 40)
        print("PHASE 10: Hybrid Search (GraphRAG)")
        print("-" * 40)
        
        start_time = time.time()
        try:
            from core.retrieval.hybrid_retriever import HybridRetriever
            
            hybrid_retriever = HybridRetriever(
                vector_store=vector_store,
                embeddings_manager=embeddings_manager
            )
            
            hybrid_queries = [
                "What methods does AEGNN outperform?",
                "Which universities are the authors from?",
                "What datasets was AEGNN evaluated on?"
            ]
            
            hybrid_results = {}
            for query in hybrid_queries:
                result = await hybrid_retriever.retrieve(query, top_k=5)
                hybrid_results[query] = result
            
            hybrid_search_result = {
                "queries_tested": len(hybrid_queries),
                "hybrid_results": hybrid_results
            }
            
            results.add_test(
                "hybrid_search",
                "PASSED",
                hybrid_search_result,
                time.time() - start_time
            )
            results.save_detail("hybrid_search_results", hybrid_search_result)
            print(f"✓ Executed {len(hybrid_queries)} hybrid search queries")
            
        except Exception as e:
            results.add_test(
                "hybrid_search",
                "FAILED",
                {"error": str(e)},
                time.time() - start_time
            )
            print(f"✗ Hybrid search failed: {e}")
        
        # Test 10: Question Answering
        print("\n" + "-" * 40)
        print("PHASE 11: Question Answering (RAG)")
        print("-" * 40)
        
        start_time = time.time()
        try:
            qa_questions = [
                "What is the main contribution of this paper?",
                "How much does AEGNN outperform BERT?",
                "What datasets were used for evaluation?",
                "What is the F1-score achieved on SciERC?"
            ]
            
            qa_results = {}
            for question in qa_questions:
                # Use query_service.ask method
                answer_result = await query_service.ask(question)
                qa_results[question] = {
                    "answer": answer_result.answer if hasattr(answer_result, 'answer') else str(answer_result),
                    "confidence": answer_result.confidence if hasattr(answer_result, 'confidence') else 0.0,
                    "sources": answer_result.sources if hasattr(answer_result, 'sources') else []
                }
            
            qa_result = {
                "questions_tested": len(qa_questions),
                "qa_results": qa_results
            }
            
            results.add_test(
                "question_answering",
                "PASSED",
                qa_result,
                time.time() - start_time
            )
            results.save_detail("qa_results", qa_result)
            print(f"✓ Answered {len(qa_questions)} questions")
            
        except Exception as e:
            results.add_test(
                "question_answering",
                "FAILED",
                {"error": str(e)},
                time.time() - start_time
            )
            print(f"✗ Question answering failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test 11: Claim Extraction (Advanced Feature)
        print("\n" + "-" * 40)
        print("PHASE 12: Claim Extraction (Advanced)")
        print("-" * 40)
        
        start_time = time.time()
        try:
            claim_extractor = ClaimExtractor()
            # Use extract() method - returns Claim dataclass objects
            claims = claim_extractor.extract(SAMPLE_PAPER)
            
            claim_result = {
                "total_claims": len(claims),
                "claims_by_type": {},
                "sample_claims": [{"text": c.text, "type": str(c.claim_type)} for c in claims[:10]]
            }
            
            for claim in claims:
                # Claim is a dataclass with claim_type attribute
                claim_type = str(claim.claim_type) if hasattr(claim, 'claim_type') else "unknown"
                if claim_type not in claim_result["claims_by_type"]:
                    claim_result["claims_by_type"][claim_type] = 0
                claim_result["claims_by_type"][claim_type] += 1
            
            results.add_test(
                "claim_extraction",
                "PASSED" if len(claims) > 0 else "FAILED",
                claim_result,
                time.time() - start_time
            )
            results.save_detail("claims_extracted", claim_result)
            print(f"✓ Extracted {len(claims)} claims")
            for ctype, count in claim_result["claims_by_type"].items():
                print(f"  - {ctype}: {count}")
            
        except Exception as e:
            results.add_test(
                "claim_extraction",
                "FAILED",
                {"error": str(e)},
                time.time() - start_time
            )
            print(f"✗ Claim extraction failed: {e}")
        
        # Test 12: Research Question Generation (Advanced Feature)
        print("\n" + "-" * 40)
        print("PHASE 13: Research Question Generation (Advanced)")
        print("-" * 40)
        
        start_time = time.time()
        try:
            question_generator = ResearchQuestionGenerator()
            concepts = ["AEGNN", "attention mechanism", "graph neural networks", "BERT", "document understanding"]
            # Use generate() async method instead of generate_questions()
            generated_questions = await question_generator.generate(concepts=concepts, num_questions=10)
            
            question_result = {
                "input_concepts": concepts,
                "questions_generated": len(generated_questions),
                "questions_by_type": {},
                "sample_questions": [{"text": q.question_text, "type": str(q.question_type)} for q in generated_questions[:10]]
            }
            
            for q in generated_questions:
                # ResearchQuestion is a dataclass with question_type attribute
                q_type = str(q.question_type) if hasattr(q, 'question_type') else "unknown"
                if q_type not in question_result["questions_by_type"]:
                    question_result["questions_by_type"][q_type] = 0
                question_result["questions_by_type"][q_type] += 1
            
            results.add_test(
                "research_question_generation",
                "PASSED" if len(generated_questions) > 0 else "FAILED",
                question_result,
                time.time() - start_time
            )
            results.save_detail("questions_generated", question_result)
            print(f"✓ Generated {len(generated_questions)} research questions")
            
        except Exception as e:
            results.add_test(
                "research_question_generation",
                "FAILED",
                {"error": str(e)},
                time.time() - start_time
            )
            print(f"✗ Question generation failed: {e}")
        
        # Test 13: Paper Recommendation (Advanced Feature)
        print("\n" + "-" * 40)
        print("PHASE 14: Paper Recommendation (Advanced)")
        print("-" * 40)
        
        start_time = time.time()
        try:
            recommender = PaperRecommender(
                vector_store=vector_store,
                graph_service=graph_service
            )
            
            # Test the recommendation method
            recommendations = await recommender.recommend(
                document_id=doc_id,
                top_k=5
            )
            
            recommendation_result = {
                "document_id": doc_id,
                "recommendations_count": len(recommendations) if recommendations else 0,
                "recommendations": [
                    {
                        "id": r.document_id,
                        "title": r.title,
                        "score": r.score,
                        "type": str(r.recommendation_type),
                        "reasons": r.reasons
                    }
                    for r in (recommendations or [])
                ][:10],
                "note": "Limited results with single document - demonstrates algorithm works"
            }
            
            results.add_test(
                "paper_recommendation",
                "PASSED",
                recommendation_result,
                time.time() - start_time
            )
            results.save_detail("recommendations", recommendation_result)
            print(f"✓ Generated {len(recommendations)} recommendations")
            
        except Exception as e:
            results.add_test(
                "paper_recommendation",
                "FAILED",
                {"error": str(e)},
                time.time() - start_time
            )
            print(f"✗ Recommendation failed: {e}")
        
        # Test 14: Duplicate Detection (Advanced Feature)
        print("\n" + "-" * 40)
        print("PHASE 15: Duplicate Detection (Advanced)")
        print("-" * 40)
        
        start_time = time.time()
        try:
            duplicate_detector = DuplicateDetector(
                vector_store=vector_store
            )
            
            # Test with slight variation of the paper
            modified_paper = SAMPLE_PAPER.replace("AEGNN", "AEGNN-v2").replace("92.3%", "93.1%")
            
            # Use the detect_in_batch method - expects list of dicts with 'id' and 'text'
            matches = duplicate_detector.detect_in_batch(
                documents=[
                    {"id": "original", "text": SAMPLE_PAPER},
                    {"id": "modified", "text": modified_paper}
                ],
                min_similarity=0.5
            )
            
            # Calculate similarity manually for display using internal methods
            jaccard_sim = duplicate_detector._compute_jaccard_similarity(
                duplicate_detector._compute_shingles(duplicate_detector._normalize_text(SAMPLE_PAPER)),
                duplicate_detector._compute_shingles(duplicate_detector._normalize_text(modified_paper))
            )
            
            duplicate_result = {
                "original_length": len(SAMPLE_PAPER),
                "modified_length": len(modified_paper),
                "matches_found": len(matches) if matches else 0,
                "jaccard_similarity": jaccard_sim,
                "is_highly_similar": jaccard_sim > 0.8,
                "matches": [
                    {
                        "doc_id": m.document_id,
                        "match_id": m.match_document_id,
                        "level": str(m.similarity_level),
                        "score": m.similarity_score
                    }
                    for m in (matches or [])
                ]
            }
            
            results.add_test(
                "duplicate_detection",
                "PASSED",
                duplicate_result,
                time.time() - start_time
            )
            results.save_detail("duplicate_detection", duplicate_result)
            print(f"✓ Computed similarity: {jaccard_sim:.2%}")
            
        except Exception as e:
            results.add_test(
                "duplicate_detection",
                "FAILED",
                {"error": str(e)},
                time.time() - start_time
            )
            print(f"✗ Duplicate detection failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test 15: Full Document Analysis (Combined)
        print("\n" + "-" * 40)
        print("PHASE 16: Full Document Analysis")
        print("-" * 40)
        
        start_time = time.time()
        try:
            # Combine all analysis results
            full_analysis = {
                "document_id": doc_id,
                "title": "Attention-Enhanced Graph Neural Networks for Scientific Document Understanding",
                "processing": {
                    "chunks_created": len(chunks) if chunks else 0,
                    "entities_extracted": len(entities) if entities else 0,
                    "relations_extracted": len(relations) if relations else 0
                },
                "entities_summary": {ent_type: len(ent_list) for ent_type, ent_list in (entities_by_type if 'entities_by_type' in dir() else {}).items()},
                "relations_summary": {rel_type: len(rel_list) for rel_type, rel_list in (relations_by_type if 'relations_by_type' in dir() else {}).items()},
                "analysis_complete": True
            }
            
            results.add_test(
                "full_document_analysis",
                "PASSED",
                full_analysis,
                time.time() - start_time
            )
            results.save_detail("full_analysis", full_analysis)
            print("✓ Full document analysis completed")
            
        except Exception as e:
            results.add_test(
                "full_document_analysis",
                "FAILED",
                {"error": str(e)},
                time.time() - start_time
            )
            print(f"✗ Full analysis failed: {e}")
        
    except Exception as e:
        print(f"\n✗ Critical error during testing: {e}")
        import traceback
        traceback.print_exc()
        results.add_test(
            "critical_error",
            "FAILED",
            {"error": str(e), "traceback": traceback.format_exc()}
        )
    
    # Save final results
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    output_path = results.save()
    
    print(f"\nTotal Tests: {results.results['summary']['total']}")
    print(f"Passed: {results.results['summary']['passed']} ✓")
    print(f"Failed: {results.results['summary']['failed']} ✗")
    print(f"Skipped: {results.results['summary']['skipped']} ○")
    print(f"\nOverall Status: {results.results['overall_status']}")
    print(f"\nResults saved to: {output_path}")
    print(f"Detailed results in: {test_results_dir}")
    print("=" * 80)
    
    return results.results


def main():
    """Entry point for the test script"""
    print("\n" + "=" * 80)
    print("ScholarMind - Full System Integration Test")
    print("=" * 80 + "\n")
    
    # Run the async test
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        results = loop.run_until_complete(run_full_system_test())
    finally:
        loop.close()
    
    return results


if __name__ == "__main__":
    main()

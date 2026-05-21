# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-05-21

### Added
- **Document Ingestion Pipeline:** Upload PDFs, Word docs, and text files with automatic parsing, chunking, and embedding
- **GraphRAG Engine:** Entity and relation extraction → Neo4j knowledge graph → graph-aware retrieval
- **Hybrid Search:** BM25 keyword search + semantic vector search with Reciprocal Rank Fusion (RRF)
- **Conversational AI:** Multi-turn chat powered by Google Gemini 2.0 Flash with conversation memory
- **Knowledge Graph Visualization:** Interactive D3.js graph with community detection
- **Multi-hop Reasoning:** Traverse the knowledge graph to answer complex cross-document questions
- **Research Analysis:** Document comparison, entity co-occurrence, citation network analysis
- **Async Processing:** Celery workers for background document processing with retry logic
- **API Documentation:** Full Swagger UI and ReDoc at `/docs` and `/redoc`
- **Infrastructure:** Docker Compose setup for PostgreSQL, Neo4j, Redis, and MinIO

### Security
- Scrubbed hardcoded API keys from `.env.example`
- Fixed CORS wildcard + credentials RFC violation
- Added SECRET_KEY production validator

### Fixed
- Neo4jClient constructor mismatch between DI and class definition
- VectorStore constructor kwarg name (`store_type` → `db_type`)
- `document_service.get()` always returning `None`
- `asyncio.run()` crash in LangGraph sync nodes when event loop is running
- Frontend API base URL missing `/api/v1` prefix
- Celery broker/backend sharing same Redis database

### DevOps
- GitHub Actions CI pipeline (lint, test, build)
- Makefile with dev/test/lint/build targets
- Pre-commit hooks (ruff, detect-secrets, mypy)
- Neo4j schema constraints file
- Deep health check endpoint (`/health`) with downstream service probes

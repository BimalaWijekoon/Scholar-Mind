<div align="center">

# 🧠 ScholarMind

### AI-Powered Research Assistant with GraphRAG Knowledge Graphs

[![CI](https://github.com/BimalaWijekoon/Scholar-Mind/actions/workflows/ci.yml/badge.svg)](https://github.com/BimalaWijekoon/Scholar-Mind/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/react-18-61DAFB.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**ScholarMind** is a full-stack GraphRAG (Graph Retrieval-Augmented Generation) research assistant that ingests academic papers, builds knowledge graphs, and answers complex multi-hop research questions with citations.

[Features](#-features) · [Architecture](#-architecture) · [Quick Start](#-quick-start) · [API Reference](#-api-reference) · [Contributing](#-contributing)

</div>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📄 **Document Ingestion** | Upload PDFs, Word docs, and text files — automatically parsed, chunked, and embedded |
| 🧠 **GraphRAG Pipeline** | Extracts entities & relations → builds a Neo4j knowledge graph → enables graph-aware retrieval |
| 🔍 **Hybrid Search** | Combines BM25 keyword search + semantic vector search with Reciprocal Rank Fusion (RRF) |
| 💬 **Conversational AI** | Multi-turn chat powered by Google Gemini 2.0 Flash with conversation memory |
| 🕸️ **Knowledge Graph Viz** | Interactive D3.js graph visualization with community detection |
| 🔗 **Multi-hop Reasoning** | Traverse the knowledge graph to answer complex cross-document questions |
| 📊 **Research Analysis** | Document comparison, entity co-occurrence, citation network analysis |
| ⚡ **Async Processing** | Celery workers for background document processing with retry logic |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    React 18 + Vite Frontend                 │
│         (Dashboard · Chat · Documents · Graph · Search)     │
└─────────────────────┬───────────────────────────────────────┘
                      │ REST API (axios)
┌─────────────────────▼───────────────────────────────────────┐
│                   FastAPI Backend (uvicorn)                  │
│  ┌──────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │ API      │  │ Services     │  │ Core Engine         │    │
│  │ Routes   │→ │ Document     │→ │ PDF Parser          │    │
│  │          │  │ Query        │  │ Entity Extractor    │    │
│  │          │  │ Graph        │  │ Relation Extractor  │    │
│  │          │  │ Report       │  │ Embeddings (MiniLM) │    │
│  └──────────┘  └──────────────┘  │ Hybrid Retriever    │    │
│                                   │ Reranker            │    │
│                                   │ LangGraph Agent     │    │
│                                   └────────────────────┘    │
└────┬──────────┬──────────┬──────────┬───────────────────────┘
     │          │          │          │
┌────▼────┐ ┌──▼───┐ ┌───▼────┐ ┌──▼─────┐
│Postgres │ │Neo4j │ │ChromaDB│ │ Redis  │
│  (SQL)  │ │(Graph)│ │(Vector)│ │(Cache) │
└─────────┘ └──────┘ └────────┘ └────────┘
                                     │
                              ┌──────▼──────┐
                              │Celery Worker│
                              │(Background) │
                              └─────────────┘
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, D3.js, Zustand, Radix UI |
| **Backend** | FastAPI, Python 3.11+, Pydantic v2, SQLAlchemy 2.0 (async) |
| **AI/LLM** | Google Gemini 2.0 Flash, LangChain, LangGraph |
| **NLP** | spaCy, sentence-transformers (all-MiniLM-L6-v2), cross-encoder reranking |
| **Databases** | PostgreSQL 16, Neo4j 5.x, ChromaDB, Redis 7 |
| **Task Queue** | Celery 5.x with Redis broker |
| **Storage** | MinIO (S3-compatible object storage) |
| **DevOps** | Docker Compose, GitHub Actions CI |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Google API Key ([get one here](https://makersuite.google.com/app/apikey))

### 1. Clone & Configure

```bash
git clone https://github.com/BimalaWijekoon/Scholar-Mind.git
cd Scholar-Mind

cp .env.example .env
# Edit .env → set GOOGLE_API_KEY + database credentials
```

### 2. Set Up Infrastructure

Choose **one** of two modes:

<details>
<summary>☁️ <b>Cloud Mode (No Docker Required)</b> — Recommended for quick start</summary>

Sign up for free-tier managed services:

| Service | Sign Up | Free Tier |
|---------|---------|-----------|
| **PostgreSQL** | [neon.tech](https://neon.tech) | 0.5 GB storage |
| **Neo4j** | [neo4j.com/aura](https://neo4j.com/cloud/platform/aura-graph-database/) | 1 free instance |
| **Redis** | [upstash.com](https://upstash.com) | 10K commands/day |

Then paste the connection strings into your `.env` file — see [`.env.example`](.env.example) for the exact format.

</details>

<details>
<summary>🐳 <b>Docker Mode (Local)</b> — Full local setup</summary>

```bash
docker compose up -d
# Starts: PostgreSQL, Neo4j, Redis, MinIO
```

Then use the Docker connection strings in `.env` (commented out in `.env.example`).

</details>

### 3. Start Backend

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Run the API server
uvicorn backend.main:app --reload --port 8000
```

### 4. Start Frontend

```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

### 5. (Optional) Start Background Workers

```bash
celery -A backend.tasks.celery_app worker --loglevel=info
```

---

## 📖 API Reference

Once running, full interactive API docs are available at:
- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/documents/upload` | Upload a document (PDF/DOCX/TXT) |
| `GET` | `/api/v1/documents/` | List all documents with pagination |
| `POST` | `/api/v1/query/ask` | Ask a research question (GraphRAG) |
| `POST` | `/api/v1/query/chat` | Conversational chat with context |
| `GET` | `/api/v1/graph` | Get knowledge graph data |
| `GET` | `/api/v1/graph/communities` | Get detected communities |
| `POST` | `/api/v1/search` | Hybrid search across documents |
| `GET` | `/health` | Deep health check (Postgres, Redis, Neo4j) |
| `GET` | `/ready` | Readiness probe |

---

## 🧪 Development

### Using Make

```bash
make install        # Install all dependencies
make dev            # Start backend dev server
make dev-frontend   # Start frontend dev server
make test           # Run backend tests
make lint           # Lint backend + frontend
make format         # Auto-format backend code
make docker-up      # Start infrastructure
make clean          # Clean generated files
```

### Project Structure

```
ScholarMind/
├── backend/
│   ├── main.py                 # FastAPI entry point
│   ├── config.py               # Pydantic settings
│   ├── api/
│   │   ├── routes/             # API endpoints
│   │   └── dependencies.py     # Dependency injection
│   ├── core/
│   │   ├── agents/             # LangGraph research agent
│   │   ├── document_processing/# PDF parsing, chunking
│   │   ├── knowledge_graph/    # Neo4j client, graph builder
│   │   ├── nlp/                # Entity/relation extraction, embeddings
│   │   └── retrieval/          # Hybrid search, vector store, reranker
│   ├── db/
│   │   ├── database.py         # Async PostgreSQL (SQLAlchemy)
│   │   └── models.py           # ORM models
│   ├── services/               # Business logic layer
│   └── tasks/                  # Celery background tasks
├── frontend/
│   ├── src/
│   │   ├── pages/              # React pages
│   │   ├── components/         # Reusable UI components
│   │   ├── services/api.ts     # API client
│   │   └── types/              # TypeScript types
│   └── package.json
├── docker-compose.yml          # Infrastructure services
├── neo4j_schema.cypher         # Neo4j constraints & indexes
├── Makefile                    # Dev commands
├── requirements.txt            # Python dependencies
└── .github/workflows/ci.yml   # CI pipeline
```

---

## ⚙️ Environment Variables

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `GOOGLE_API_KEY` | ✅ | — | Google Gemini API key |
| `DATABASE_URL` | — | `postgresql+asyncpg://...` | PostgreSQL connection string |
| `NEO4J_URI` | — | `bolt://localhost:7687` | Neo4j connection URI |
| `NEO4J_USER` | — | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | — | `scholarmind123` | Neo4j password |
| `REDIS_URL` | — | `redis://localhost:6379/0` | Redis connection URL |
| `CORS_ORIGINS` | — | `localhost:3000,5173` | Allowed CORS origins (comma-separated) |
| `SECRET_KEY` | ⚠️ | *insecure default* | JWT secret — **change in production** |
| `VECTOR_STORE_TYPE` | — | `chromadb` | Vector store backend |
| `EMBEDDING_MODEL` | — | `all-MiniLM-L6-v2` | Sentence transformer model |

See [.env.example](.env.example) for the complete list.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Install pre-commit hooks: `pip install pre-commit && pre-commit install`
4. Make your changes and add tests
5. Run the test suite: `make test`
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

Built with ❤️ by [Bimala Wijekoon](https://github.com/BimalaWijekoon)

</div>

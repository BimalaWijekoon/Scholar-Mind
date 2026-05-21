# Contributing to ScholarMind

Thank you for your interest in contributing to ScholarMind! This guide will help you get started.

## Development Setup

1. **Fork the repository** and clone your fork
2. **Install prerequisites:** Python 3.11+, Node.js 20+, Docker
3. **Set up the environment:**

```bash
# Start infrastructure
docker compose up -d

# Backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Frontend
cd frontend && npm install

# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

4. **Configure environment:** Copy `.env.example` to `.env` and set your `GOOGLE_API_KEY`

## Development Workflow

```bash
# Start backend
make dev

# Start frontend (separate terminal)
make dev-frontend

# Run tests
make test

# Lint & format
make lint
make format
```

## Code Style

- **Python:** Formatted with `ruff` (configured in `pyproject.toml`)
- **TypeScript:** ESLint + Prettier
- **Commits:** Use [Conventional Commits](https://www.conventionalcommits.org/) format
  - `feat:` New features
  - `fix:` Bug fixes
  - `docs:` Documentation changes
  - `refactor:` Code refactoring
  - `test:` Adding or updating tests
  - `chore:` Maintenance tasks

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with appropriate tests
3. Ensure all tests pass: `make test`
4. Ensure linting passes: `make lint`
5. Submit a PR with a clear description of your changes

## Architecture Overview

See the [README](README.md) for the full architecture diagram.

### Key directories:
- `backend/core/` — Core engine (NLP, retrieval, knowledge graph, agents)
- `backend/services/` — Business logic layer
- `backend/api/routes/` — FastAPI endpoints
- `frontend/src/pages/` — React pages
- `frontend/src/components/` — Reusable UI components

## Reporting Issues

- Use [GitHub Issues](https://github.com/BimalaWijekoon/Scholar-Mind/issues)
- Include steps to reproduce, expected vs actual behavior
- Attach relevant logs if applicable

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).

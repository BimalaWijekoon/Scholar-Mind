.PHONY: dev test lint format clean install docker-up docker-down migrate

# ============================================
# ScholarMind — Development Commands
# ============================================

# --- Setup ---
install:
	pip install -r requirements.txt
	python -m spacy download en_core_web_sm
	cd frontend && npm install

# --- Development ---
dev:
	uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

dev-worker:
	celery -A backend.tasks.celery_app worker --loglevel=info

dev-beat:
	celery -A backend.tasks.celery_app beat --loglevel=info

# --- Infrastructure ---
docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

# --- Database ---
migrate:
	alembic upgrade head

migrate-create:
	alembic revision --autogenerate -m "$(msg)"

# --- Testing ---
test:
	pytest backend/tests/ -v --tb=short

test-cov:
	pytest backend/tests/ -v --cov=backend --cov-report=html

test-frontend:
	cd frontend && npm run test -- --run

# --- Code Quality ---
lint:
	ruff check backend/
	cd frontend && npm run lint

format:
	ruff format backend/
	ruff check --fix backend/

type-check:
	mypy backend/ --ignore-missing-imports

# --- Build ---
build-frontend:
	cd frontend && npm run build

# --- Cleanup ---
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage coverage.xml
	rm -rf frontend/dist frontend/node_modules/.vite

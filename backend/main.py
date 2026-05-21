"""
ScholarMind - AI Research Assistant with Knowledge Graphs
FastAPI Application Entry Point
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.api.routes import documents, query, graph, search, reports, advanced
from backend.utils.logging_config import setup_logging
from backend.db.database import init_database
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    setup_logging()
    
    # Initialize PostgreSQL database
    db = init_database(settings.DATABASE_URL, echo=settings.DEBUG)
    try:
        await db.init()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning(f"Database initialization skipped (is PostgreSQL running?): {e}")
    
    yield
    
    # Shutdown — close database connections
    try:
        await db.close()
    except Exception:
        pass


app = FastAPI(
    title=settings.APP_NAME,
    description="AI Research Assistant with Knowledge Graphs - GraphRAG powered research tool",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware — Use configured origins (never wildcard in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include API routers
app.include_router(documents.router, prefix=f"{settings.API_PREFIX}/documents", tags=["Documents"])
app.include_router(query.router, prefix=f"{settings.API_PREFIX}/query", tags=["Query"])
app.include_router(graph.router, prefix=f"{settings.API_PREFIX}/graph", tags=["Graph"])
app.include_router(search.router, prefix=f"{settings.API_PREFIX}/search", tags=["Search"])
app.include_router(reports.router, prefix=f"{settings.API_PREFIX}/reports", tags=["Reports"])
app.include_router(advanced.router, prefix=f"{settings.API_PREFIX}/advanced", tags=["Advanced Features"])


@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {
        "name": settings.APP_NAME,
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Deep health check — verifies downstream service connectivity."""
    import redis as redis_lib
    
    checks = {}
    healthy = True
    
    # Check PostgreSQL
    try:
        from backend.db.database import get_db_session
        async for session in get_db_session():
            await session.execute("SELECT 1")
            checks["postgres"] = "ok"
            break
    except Exception as e:
        checks["postgres"] = f"error: {str(e)[:100]}"
        healthy = False
    
    # Check Redis
    try:
        r = redis_lib.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        r.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {str(e)[:100]}"
        healthy = False
    
    # Check Neo4j (non-blocking)
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        )
        driver.verify_connectivity()
        driver.close()
        checks["neo4j"] = "ok"
    except Exception as e:
        checks["neo4j"] = f"error: {str(e)[:100]}"
        # Neo4j is optional — don't mark unhealthy
    
    from fastapi.responses import JSONResponse
    status_code = 200 if healthy else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if healthy else "degraded",
            "checks": checks,
        },
    )


@app.get("/ready")
async def readiness_check():
    """Readiness probe — returns 200 when the app is ready to serve traffic."""
    return {"status": "ready"}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )

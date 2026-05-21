@echo off
title ScholarMind Full System
echo.
echo ================================================================
echo                    ScholarMind Full System
echo          AI Research Assistant with Knowledge Graphs
echo ================================================================
echo.
echo This will start the FULL system including:
echo   - PostgreSQL (metadata database)
echo   - Neo4j (knowledge graph)
echo   - Redis (caching ^& task queue)
echo   - MinIO (document storage)
echo   - Celery (background tasks)
echo   - FastAPI backend
echo   - React frontend
echo.
echo Prerequisites: Docker Desktop, Python 3.11+, Node.js 18+
echo.
echo Press any key to continue or Ctrl+C to cancel...
pause >nul

cd /d "%~dp0"

if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe scripts\quickstart.py
) else (
    python scripts\quickstart.py
)

pause

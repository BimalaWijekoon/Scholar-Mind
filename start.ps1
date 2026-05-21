# ScholarMind Full System Start Script (PowerShell)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "                    ScholarMind Full System" -ForegroundColor Cyan
Write-Host "          AI Research Assistant with Knowledge Graphs" -ForegroundColor Cyan  
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will start the FULL system including:" -ForegroundColor Yellow
Write-Host "  - PostgreSQL (metadata database)"
Write-Host "  - Neo4j (knowledge graph)"
Write-Host "  - Redis (caching & task queue)"
Write-Host "  - MinIO (document storage)"
Write-Host "  - Celery (background tasks)"
Write-Host "  - FastAPI backend"
Write-Host "  - React frontend"
Write-Host ""
Write-Host "Prerequisites: Docker Desktop, Python 3.11+, Node.js 18+" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Enter to continue or Ctrl+C to cancel..." -ForegroundColor Gray
Read-Host

Set-Location $PSScriptRoot

if (Test-Path "venv\Scripts\python.exe") {
    & "venv\Scripts\python.exe" "scripts\quickstart.py"
} else {
    python "scripts\quickstart.py"
}

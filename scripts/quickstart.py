#!/usr/bin/env python
"""
ScholarMind Full System Quick Start

This script sets up and runs the COMPLETE ScholarMind system with:
- PostgreSQL (metadata storage)
- Neo4j (knowledge graph)
- Redis (caching & task queue)
- MinIO (document storage)
- Celery (background tasks)
- FastAPI backend
- React frontend
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import time
import socket

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_banner():
    """Print the ScholarMind banner."""
    banner = f"""
{Colors.CYAN}{Colors.BOLD}
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ███████╗ ██████╗██╗  ██╗ ██████╗ ██╗      █████╗ ██████╗   ║
║   ██╔════╝██╔════╝██║  ██║██╔═══██╗██║     ██╔══██╗██╔══██╗  ║
║   ███████╗██║     ███████║██║   ██║██║     ███████║██████╔╝  ║
║   ╚════██║██║     ██╔══██║██║   ██║██║     ██╔══██║██╔══██╗  ║
║   ███████║╚██████╗██║  ██║╚██████╔╝███████╗██║  ██║██║  ██║  ║
║   ╚══════╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝  ║
║                                                               ║
║         AI Research Assistant with Knowledge Graphs           ║
║                      FULL SYSTEM SETUP                        ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
{Colors.END}
"""
    print(banner)

def print_step(step: int, total: int, message: str):
    """Print a step message."""
    print(f"\n{Colors.BOLD}[{step}/{total}]{Colors.END} {Colors.GREEN}{message}{Colors.END}")

def print_info(message: str):
    """Print an info message."""
    print(f"    {Colors.BLUE}ℹ{Colors.END} {message}")

def print_warning(message: str):
    """Print a warning message."""
    print(f"    {Colors.YELLOW}⚠{Colors.END} {message}")

def print_error(message: str):
    """Print an error message."""
    print(f"    {Colors.RED}✗{Colors.END} {message}")

def print_success(message: str):
    """Print a success message."""
    print(f"    {Colors.GREEN}✓{Colors.END} {message}")

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent

def is_port_open(host: str, port: int) -> bool:
    """Check if a port is open."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    try:
        sock.connect((host, port))
        sock.close()
        return True
    except:
        return False

def is_http_ready(url: str) -> bool:
    """Check if an HTTP endpoint is responding."""
    import urllib.request
    try:
        req = urllib.request.Request(url, method='HEAD')
        urllib.request.urlopen(req, timeout=2)
        return True
    except:
        return False

def wait_for_service(name: str, host: str, port: int, timeout: int = 60, use_http: bool = False):
    """Wait for a service to be available."""
    print_info(f"Waiting for {name} on port {port}...")
    start = time.time()
    url = f"http://{host}:{port}/"
    
    while time.time() - start < timeout:
        if use_http:
            if is_http_ready(url):
                print_success(f"{name} is ready")
                return True
        else:
            if is_port_open(host, port):
                print_success(f"{name} is ready")
                return True
        time.sleep(2)
    print_error(f"{name} did not start within {timeout} seconds")
    return False

def check_docker():
    """Check if Docker is installed and running."""
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print_success(f"Docker: {result.stdout.strip()}")
            
            # Check if Docker daemon is running
            result = subprocess.run(["docker", "info"], capture_output=True, text=True)
            if result.returncode == 0:
                print_success("Docker daemon is running")
                return True
            else:
                print_error("Docker daemon is not running. Please start Docker Desktop.")
                return False
    except FileNotFoundError:
        pass
    
    print_error("Docker not found. Please install Docker Desktop from https://docker.com")
    return False

def check_docker_compose():
    """Check if Docker Compose is available."""
    try:
        # Try docker compose (v2)
        result = subprocess.run(["docker", "compose", "version"], capture_output=True, text=True)
        if result.returncode == 0:
            print_success(f"Docker Compose: {result.stdout.strip()}")
            return "docker compose"
    except:
        pass
    
    try:
        # Try docker-compose (v1)
        result = subprocess.run(["docker-compose", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print_success(f"Docker Compose: {result.stdout.strip()}")
            return "docker-compose"
    except:
        pass
    
    print_error("Docker Compose not found")
    return None

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print_error(f"Python 3.11+ required. Found: {version.major}.{version.minor}")
        return False
    print_success(f"Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_node():
    """Check if Node.js is installed."""
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print_success(f"Node.js {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    print_error("Node.js not found. Install from https://nodejs.org/")
    return False

def start_docker_services(project_root: Path, compose_cmd: str):
    """Start Docker services."""
    print_info("Starting Docker containers (PostgreSQL, Neo4j, Redis, MinIO)...")
    
    cmd = compose_cmd.split() + ["up", "-d"]
    result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
    
    if result.returncode != 0:
        print_error(f"Failed to start containers: {result.stderr}")
        return False
    
    print_success("Docker containers started")
    return True

def create_env_file(project_root: Path):
    """Create .env file with full configuration."""
    env_file = project_root / ".env"
    
    env_content = """# ScholarMind Full Configuration
# Generated by quickstart.py

# ============================================================
# APPLICATION SETTINGS
# ============================================================
APP_NAME=ScholarMind
APP_ENV=development
DEBUG=true
SECRET_KEY=change-this-in-production-use-a-random-string
LOG_LEVEL=INFO

# ============================================================
# API SETTINGS
# ============================================================
API_HOST=0.0.0.0
API_PORT=8000
API_PREFIX=/api/v1

# ============================================================
# DATABASE - PostgreSQL
# ============================================================
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=scholarmind
POSTGRES_USER=scholarmind
POSTGRES_PASSWORD=scholarmind123
DATABASE_URL=postgresql+asyncpg://scholarmind:scholarmind123@localhost:5432/scholarmind

# ============================================================
# KNOWLEDGE GRAPH - Neo4j
# ============================================================
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=scholarmind123

# ============================================================
# CACHE & MESSAGE BROKER - Redis
# ============================================================
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# ============================================================
# OBJECT STORAGE - MinIO
# ============================================================
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=scholarmind
MINIO_SECRET_KEY=scholarmind123
MINIO_BUCKET=documents
MINIO_SECURE=false

# ============================================================
# VECTOR STORE - ChromaDB
# ============================================================
VECTOR_STORE_TYPE=chromadb
CHROMA_PERSIST_DIRECTORY=./data/chroma
CHROMA_COLLECTION_NAME=scholarmind_docs

# ============================================================
# LLM - Google Gemini
# ============================================================
# Get your API key from: https://makersuite.google.com/app/apikey
GOOGLE_API_KEY=

# ============================================================
# ML MODELS
# ============================================================
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
SPACY_MODEL=en_core_web_sm
RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2

# ============================================================
# FILE STORAGE
# ============================================================
UPLOAD_DIR=./data/uploads
PROCESSED_DIR=./data/processed
EMBEDDINGS_DIR=./data/embeddings
MAX_UPLOAD_SIZE_MB=100

# ============================================================
# FRONTEND
# ============================================================
VITE_API_URL=http://localhost:8000/api
"""
    
    if env_file.exists():
        print_info(".env file already exists, preserving API keys...")
        existing = env_file.read_text()
        # Extract existing API key
        for line in existing.split("\n"):
            if line.startswith("GOOGLE_API_KEY=") and len(line) > 16:
                api_key = line.split("=", 1)[1].strip()
                if api_key:
                    env_content = env_content.replace("GOOGLE_API_KEY=\n", f"GOOGLE_API_KEY={api_key}\n")
                    break
    
    env_file.write_text(env_content)
    print_success("Created/updated .env file with full configuration")
    
    # Check for API key
    if "GOOGLE_API_KEY=\n" in env_content:
        print_warning("GOOGLE_API_KEY is not set - LLM features will not work!")
        print_warning("Get your key at: https://makersuite.google.com/app/apikey")
    
    return True

def create_data_directories(project_root: Path):
    """Create necessary data directories."""
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "embeddings",
        project_root / "data" / "exports",
        project_root / "data" / "chroma",
        project_root / "data" / "uploads",
        project_root / "logs",
    ]
    
    for dir_path in directories:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    print_success("Created data directories")
    return True

def get_venv_python(project_root: Path) -> Path:
    """Get the path to the virtual environment Python."""
    venv_path = project_root / "venv"
    if sys.platform == "win32":
        return venv_path / "Scripts" / "python.exe"
    return venv_path / "bin" / "python"

def get_venv_pip(project_root: Path) -> Path:
    """Get the path to the virtual environment pip."""
    venv_path = project_root / "venv"
    if sys.platform == "win32":
        return venv_path / "Scripts" / "pip.exe"
    return venv_path / "bin" / "pip"

def setup_python_environment(project_root: Path):
    """Set up Python virtual environment and install dependencies."""
    venv_path = project_root / "venv"
    python_path = get_venv_python(project_root)
    pip_path = get_venv_pip(project_root)
    
    # Check if venv exists
    if not venv_path.exists():
        print_info("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
        print_success("Virtual environment created")
    
    # Check if dependencies are installed
    result = subprocess.run(
        [str(python_path), "-c", "import fastapi; import neo4j; import langchain; import chromadb"],
        capture_output=True
    )
    
    if result.returncode != 0:
        print_info("Installing Python dependencies (this may take several minutes)...")
        subprocess.run([str(pip_path), "install", "--upgrade", "pip"], check=True)
        subprocess.run([str(pip_path), "install", "-r", str(project_root / "requirements.txt")], check=True)
        print_success("Python dependencies installed")
    else:
        print_success("Python dependencies already installed")
    
    # Download spaCy model
    result = subprocess.run(
        [str(python_path), "-c", "import spacy; spacy.load('en_core_web_sm')"],
        capture_output=True
    )
    if result.returncode != 0:
        print_info("Downloading spaCy language model...")
        subprocess.run([str(python_path), "-m", "spacy", "download", "en_core_web_sm"], check=True)
        print_success("spaCy model downloaded")
    else:
        print_success("spaCy model ready")
    
    return True

def setup_frontend(project_root: Path):
    """Install frontend dependencies."""
    frontend_path = project_root / "frontend"
    node_modules = frontend_path / "node_modules"
    
    if not node_modules.exists():
        print_info("Installing frontend dependencies...")
        subprocess.run(["npm", "install"], cwd=frontend_path, check=True, shell=True)
    
    print_success("Frontend dependencies ready")
    return True

def setup_neo4j(project_root: Path):
    """Set up Neo4j constraints and indexes."""
    python_path = get_venv_python(project_root)
    
    print_info("Setting up Neo4j schema...")
    
    result = subprocess.run(
        [str(python_path), str(project_root / "scripts" / "setup_neo4j.py")],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print_success("Neo4j schema ready")
    else:
        print_warning("Neo4j setup had warnings (may be normal if already set up)")
    
    return True

def start_celery_worker(project_root: Path):
    """Start Celery worker for background tasks."""
    if sys.platform == "win32":
        celery_path = project_root / "venv" / "Scripts" / "celery.exe"
    else:
        celery_path = project_root / "venv" / "bin" / "celery"
    
    print_info("Starting Celery worker...")
    
    # Start with output visible in terminal
    process = subprocess.Popen(
        [str(celery_path), "-A", "backend.tasks.celery_app", "worker", "--loglevel=info", "--pool=solo"],
        cwd=project_root,
        stdout=None,  # Output goes to terminal
        stderr=None   # Errors go to terminal
    )
    
    time.sleep(3)
    
    if process.poll() is None:
        print_success(f"Celery worker started (PID: {process.pid})")
        return process
    else:
        print_warning("Celery worker may not have started correctly")
        return None

def start_backend(project_root: Path):
    """Start the FastAPI backend server."""
    python_path = get_venv_python(project_root)
    
    print_info("Starting backend server on http://localhost:8000")
    print_info("API docs available at http://localhost:8000/docs")
    print_info("Backend output will appear below...")
    print("")
    
    # Start backend with output visible in terminal (stdout=None means inherit)
    backend_process = subprocess.Popen(
        [str(python_path), "-m", "uvicorn", "backend.main:app", 
         "--host", "0.0.0.0", "--port", "8000"],
        cwd=project_root,
        stdout=None,  # Output goes to terminal
        stderr=None   # Errors go to terminal
    )
    
    
    return backend_process

def start_frontend(project_root: Path):
    """Start the frontend development server."""
    frontend_path = project_root / "frontend"
    
    print_info("Starting frontend on http://localhost:3000")
    
    # Start frontend with output visible in terminal
    frontend_process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=frontend_path,
        shell=True,
        stdout=None,  # Output goes to terminal
        stderr=None   # Errors go to terminal
    )
    
    return frontend_process

def print_status_table():
    """Print the status of all services."""
    services = [
        ("PostgreSQL", "localhost", 5432),
        ("Neo4j HTTP", "localhost", 7474),
        ("Neo4j Bolt", "localhost", 7687),
        ("Redis", "localhost", 6379),
        ("MinIO API", "localhost", 9000),
        ("MinIO Console", "localhost", 9001),
        ("Backend API", "localhost", 8000),
        ("Frontend", "localhost", 3000),
    ]
    
    print(f"\n{Colors.BOLD}Service Status:{Colors.END}")
    print("─" * 40)
    
    for name, host, port in services:
        is_running = is_port_open(host, port)
        status = f"{Colors.GREEN}● Running{Colors.END}" if is_running else f"{Colors.RED}○ Stopped{Colors.END}"
        print(f"  {name:20} {status}")
    
    print("─" * 40)

def main():
    """Main entry point."""
    print_banner()
    
    project_root = get_project_root()
    os.chdir(project_root)
    
    total_steps = 12
    
    # Step 1: Check prerequisites
    print_step(1, total_steps, "Checking prerequisites...")
    
    if not check_python_version():
        return 1
    
    if not check_node():
        return 1
    
    if not check_docker():
        return 1
    
    compose_cmd = check_docker_compose()
    if not compose_cmd:
        return 1
    
    # Step 2: Create configuration
    print_step(2, total_steps, "Creating configuration...")
    create_env_file(project_root)
    
    # Step 3: Create directories
    print_step(3, total_steps, "Creating directories...")
    create_data_directories(project_root)
    
    # Step 4: Start Docker services
    print_step(4, total_steps, "Starting Docker services...")
    if not start_docker_services(project_root, compose_cmd):
        return 1
    
    # Step 5: Wait for services
    print_step(5, total_steps, "Waiting for services to be ready...")
    services_ok = True
    services_ok &= wait_for_service("PostgreSQL", "localhost", 5432, 30)
    services_ok &= wait_for_service("Neo4j", "localhost", 7687, 60)
    services_ok &= wait_for_service("Redis", "localhost", 6379, 30)
    services_ok &= wait_for_service("MinIO", "localhost", 9000, 30)
    
    if not services_ok:
        print_error("Some services failed to start")
        return 1
    
    # Step 6: Setup Python environment
    print_step(6, total_steps, "Setting up Python environment...")
    try:
        setup_python_environment(project_root)
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to setup Python: {e}")
        return 1
    
    # Step 7: Setup frontend
    print_step(7, total_steps, "Setting up frontend...")
    try:
        setup_frontend(project_root)
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to setup frontend: {e}")
        return 1
    
    # Step 8: Setup Neo4j
    print_step(8, total_steps, "Setting up Neo4j schema...")
    setup_neo4j(project_root)
    
    # Step 9: Start Celery worker
    print_step(9, total_steps, "Starting background task worker...")
    celery_process = start_celery_worker(project_root)
    
    # Step 10: Start backend
    print_step(10, total_steps, "Starting backend server...")
    backend_process = start_backend(project_root)
    
    # Step 11: Start frontend
    print_step(11, total_steps, "Starting frontend server...")
    frontend_process = start_frontend(project_root)
    
    # Give servers a moment to start
    time.sleep(5)
    
    # Step 12: Done!
    print_step(12, total_steps, "All services started!")
    
    # Print success message
    print(f"""
{Colors.GREEN}{Colors.BOLD}
╔═══════════════════════════════════════════════════════════════════╗
║                  ScholarMind is Running!                          ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║   🌐 Frontend:        http://localhost:3000                       ║
║   🔧 Backend API:     http://localhost:8000                       ║
║   📚 API Docs:        http://localhost:8000/docs                  ║
║   🔷 Neo4j Browser:   http://localhost:7474                       ║
║   📦 MinIO Console:   http://localhost:9001                       ║
║                                                                   ║
║   Press Ctrl+C to stop all services                               ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
{Colors.END}
""")
    
    print_status_table()
    
    # Check API key warning
    env_file = project_root / ".env"
    env_content = env_file.read_text()
    if "GOOGLE_API_KEY=\n" in env_content:
        print(f"""
{Colors.YELLOW}
┌───────────────────────────────────────────────────────────────────┐
│  ⚠ IMPORTANT: Set your GOOGLE_API_KEY in .env for LLM features   │
│                                                                   │
│  Get your free API key at:                                        │
│  https://makersuite.google.com/app/apikey                         │
└───────────────────────────────────────────────────────────────────┘
{Colors.END}
""")
    
    try:
        # Wait for processes
        backend_process.wait()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Shutting down...{Colors.END}")
        
        backend_process.terminate()
        frontend_process.terminate()
        if celery_process:
            celery_process.terminate()
        
        # Ask about Docker
        print(f"\n{Colors.YELLOW}Stop Docker containers? (y/n): {Colors.END}", end="")
        try:
            response = input().strip().lower()
            if response == 'y':
                cmd = compose_cmd.split() + ["down"]
                subprocess.run(cmd, cwd=project_root)
                print_success("Docker containers stopped")
        except:
            pass
        
        print(f"{Colors.GREEN}Goodbye!{Colors.END}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

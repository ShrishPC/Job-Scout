#!/bin/bash

# Exit on error
set -e

# Define colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Initializing Job Scout Dev Stack (Plug & Play Bootstrap)...${NC}"

# 1. Check if Docker is installed and running
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}❌ Error: Docker is not running or not installed. PostgreSQL and Redis require Docker to be active.${NC}"
    echo -e "${YELLOW}Please start Docker and try again.${NC}"
    exit 1
fi

# 2. Set up environment config files (.env)
if [ ! -f ".env" ]; then
    echo -e "${BLUE}[Setup] Root .env file not found. Creating from .env.example...${NC}"
    cp .env.example .env
fi

if [ ! -f "backend/.env" ]; then
    echo -e "${BLUE}[Setup] Backend .env file not found. Creating from .env.example...${NC}"
    cp .env.example backend/.env
fi

# 3. Setup Backend Virtual Environment
if [ ! -d "backend/venv" ]; then
    echo -e "${YELLOW}[Setup] Creating backend virtual environment...${NC}"
    python3 -m venv backend/venv
    echo -e "${YELLOW}[Setup] Installing backend dependencies (pip install)...${NC}"
    backend/venv/bin/pip install --upgrade pip
    backend/venv/bin/pip install -r backend/requirements.txt
else
    echo -e "${GREEN}✓ Backend virtual environment detected.${NC}"
fi

# 4. Setup Playwright in Backend Virtual Environment
echo -e "${YELLOW}[Setup] Installing Playwright Chromium browser binaries...${NC}"
backend/venv/bin/playwright install chromium

# 5. Setup Frontend Dependencies
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}[Setup] Installing frontend dependencies (npm install)...${NC}"
    cd frontend
    npm install
    cd ..
else
    echo -e "${GREEN}✓ Frontend dependencies (node_modules) detected.${NC}"
fi

# 6. Pre-cache Local AI Models (Free, local embeddings & parser)
# Check if cached files exist. If not, pre-download to avoid API/web request timeouts.
TINYLLAMA_CACHE="models/models--TinyLlama--TinyLlama-1.1B-Chat-v1.0"
MINILM_CACHE="models/models--sentence-transformers--all-MiniLM-L6-v2"
if [ ! -d "$TINYLLAMA_CACHE" ] || [ ! -d "$MINILM_CACHE" ]; then
    echo -e "${BLUE}[Setup] Cache folders for local models not found. Pre-downloading models...${NC}"
    backend/venv/bin/python scripts/download_models.py
else
    echo -e "${GREEN}✓ Local AI models (TinyLlama & MiniLM) are already cached locally.${NC}"
fi

echo -e "${GREEN}✨ Bootstrapping complete! Launching services...${NC}"

# Clean up any stale local development processes first
echo -e "${BLUE}[System] Cleaning up stale uvicorn or celery processes...${NC}"
pkill -f "uvicorn app.main:app" || true
pkill -f "celery -A celery_app" || true

# 7. Start Docker containers (DB and Redis)
echo -e "${BLUE}[Docker] Starting Database and Redis...${NC}"
docker compose up -d db redis

# Wait for database to be ready
echo -e "${BLUE}[Docker] Waiting for PostgreSQL and Redis to be healthy...${NC}"
sleep 2

# 8. Run Database Migrations/Initialization
echo -e "${YELLOW}[Database] Running database initialization...${NC}"
cd backend
./venv/bin/python init_db.py
cd ..

# Array to store PIDs of background processes
PIDS=()

# Cleanup function to kill all spawned processes on exit
cleanup() {
    echo -e "\n${RED}🛑 Shutting down Job Scout services...${NC}"
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${RED}[System] Terminating process $pid...${NC}"
            kill -TERM "$pid" 2>/dev/null
        fi
    done
    exit 0
}

# Trap Ctrl+C (SIGINT) and SIGTERM to run cleanup
trap cleanup SIGINT SIGTERM

# 9. Start Backend FastAPI
echo -e "${CYAN}[Backend] Starting FastAPI server on port 8000...${NC}"
cd backend
./venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
PIDS+=($!)
cd ..

# 10. Start Celery Worker
echo -e "${MAGENTA}[Celery] Starting Celery worker...${NC}"
cd scraper
../backend/venv/bin/python -m celery -A celery_app worker --loglevel=info > celery_worker.log 2>&1 &
PIDS+=($!)
cd ..

# 11. Start Celery Beat
echo -e "${MAGENTA}[Celery] Starting Celery beat...${NC}"
cd scraper
../backend/venv/bin/python -m celery -A celery_app beat --loglevel=info > celery_beat.log 2>&1 &
PIDS+=($!)
cd ..

# 12. Start Frontend (Next.js)
echo -e "${GREEN}[Frontend] Starting Next.js dev server on port 3000...${NC}"
cd frontend
npm run dev &
PIDS+=($!)
cd ..

echo -e "${GREEN}====================================================${NC}"
echo -e "${GREEN}   Job Scout is up and running!                      ${NC}"
echo -e "${GREEN}   - Frontend: http://localhost:3000                 ${NC}"
echo -e "${GREEN}   - Backend Docs: http://localhost:8000/docs        ${NC}"
echo -e "${GREEN}====================================================${NC}"
echo -e "${YELLOW}Logs are written to:${NC}"
echo -e "  - Backend: backend/backend.log"
echo -e "  - Celery Worker: scraper/celery_worker.log"
echo -e "  - Celery Beat: scraper/celery_beat.log"
echo -e "  - Frontend output is streaming below..."
echo -e "${YELLOW}Press Ctrl+C to shut down all services.${NC}"
echo -e "${GREEN}====================================================${NC}"

# Wait for the frontend process (keeps the script running in foreground)
wait ${PIDS[3]}

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

echo -e "${GREEN}🚀 Initializing Job Scout Dev Stack (Full Dockerized)...${NC}"

# 1. Check if Docker is installed and running
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}❌ Error: Docker is not running or not installed. Docker is required to run the stack.${NC}"
    exit 1
fi

# 2. Set up environment config files (.env)
if [ ! -f ".env" ]; then
    echo -e "${BLUE}[Setup] Root .env file not found. Creating from .env.example...${NC}"
    cp .env.example .env || true
fi

if [ ! -f "backend/.env" ]; then
    echo -e "${BLUE}[Setup] Backend .env file not found. Creating from .env.example...${NC}"
    cp .env.example backend/.env || true
fi

# 3. Pre-cache Local AI Models (Free, local embeddings & parser)
# Check if cached files exist. If not, pre-download to avoid API/web request timeouts.
LLAMA3_CACHE="models/models--unsloth--Llama-3.2-3B-Instruct"
MINILM_CACHE="models/models--sentence-transformers--all-MiniLM-L6-v2"
if [ ! -d "$LLAMA3_CACHE" ] || [ ! -d "$MINILM_CACHE" ]; then
    echo -e "${BLUE}[Setup] Cache folders for local models not found.${NC}"
    echo -e "${YELLOW}Please run 'python scripts/download_models.py' locally first if you want them pre-cached!${NC}"
else
    echo -e "${GREEN}✓ Local AI models (Llama 3.2 & MiniLM) are already cached locally.${NC}"
fi

# 4. Cleanup any existing zombie processes just in case before migrating to docker
echo -e "${BLUE}[System] Cleaning up any old local dev processes...${NC}"
pkill -f "uvicorn app.main:app" || true
pkill -f "celery -A celery_app" || true
pkill -f "next dev" || true

echo -e "${GREEN}✨ Building and launching services with Docker Compose...${NC}"

# 5. Start Docker containers
docker compose up -d --build

echo -e "${GREEN}====================================================${NC}"
echo -e "${GREEN}   Job Scout is up and running via Docker!           ${NC}"
echo -e "${GREEN}   - Frontend: http://localhost:3000                 ${NC}"
echo -e "${GREEN}   - Backend Docs: http://localhost:8001/docs        ${NC}"
echo -e "${GREEN}====================================================${NC}"
echo -e "${YELLOW}To view logs, run:${NC}"
echo -e "  docker compose logs -f"
echo -e "${YELLOW}To shut down all services, run:${NC}"
echo -e "  docker compose down"
echo -e "${GREEN}====================================================${NC}"

#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Terminal colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${GREEN}${BOLD}🚀 Initializing Job Scout AI Stack (Docker Compose)...${NC}"

# 1. Check if Docker is installed and daemon is running
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}❌ Error: Docker is not running or not installed. Docker is required to run the stack.${NC}"
    echo -e "${YELLOW}Please start Docker Desktop or the dockerd daemon and try again.${NC}"
    exit 1
fi

# 2. Check if Docker Compose plugin is available
if ! docker compose version >/dev/null 2>&1; then
    echo -e "${RED}❌ Error: 'docker compose' plugin is not available. Please install docker-compose-plugin.${NC}"
    exit 1
fi

# 3. Set up environment config files (.env)
if [ ! -f ".env" ]; then
    echo -e "${BLUE}[Setup] Root .env file not found. Creating from .env.example...${NC}"
    cp .env.example .env || true
fi

if [ ! -f "backend/.env" ]; then
    echo -e "${BLUE}[Setup] Backend .env file not found. Creating from .env.example...${NC}"
    cp .env.example backend/.env || true
fi

# 4. Pre-cache Local AI Models Check
LLAMA3_CACHE="models/models--unsloth--Llama-3.2-3B-Instruct"
MINILM_CACHE="models/models--sentence-transformers--all-MiniLM-L6-v2"
if [ ! -d "$LLAMA3_CACHE" ] || [ ! -d "$MINILM_CACHE" ]; then
    echo -e "${BLUE}[Setup] Cache folders for local models not detected.${NC}"
    echo -e "${YELLOW}Tip: Models will run in optimized DEMO mode by default. Run 'python scripts/download_models.py' if you want full offline HuggingFace models.${NC}"
else
    echo -e "${GREEN}✓ Local AI models (Llama 3.2 & MiniLM) are cached locally in ./models.${NC}"
fi

# 5. Clean up old host development processes before container launch
echo -e "${BLUE}[System] Cleaning up any conflicting host dev processes...${NC}"
pkill -f "uvicorn app.main:app" 2>/dev/null || true
pkill -f "celery -A celery_app" 2>/dev/null || true

echo -e "${GREEN}✨ Building and launching services with Docker Compose...${NC}"

# 6. Start Docker containers with build check
docker compose up -d --build

# 7. Wait briefly for backend health check
echo -e "${CYAN}[Health] Waiting for backend API and database to initialize...${NC}"
sleep 3

echo -e "\n${GREEN}====================================================${NC}"
echo -e "${GREEN}${BOLD}   Job Scout is up and running via Docker!          ${NC}"
echo -e "${GREEN}   - Web App:      http://localhost:3000            ${NC}"
echo -e "${GREEN}   - Admin Panel:  http://localhost:3000/admin       ${NC}"
echo -e "${GREEN}   - API Docs:     http://localhost:8001/docs        ${NC}"
echo -e "${GREEN}   - Redis:        localhost:6380                    ${NC}"
echo -e "${GREEN}   - PostgreSQL:   localhost:5435                    ${NC}"
echo -e "${GREEN}====================================================${NC}"
echo -e "${YELLOW}Useful Commands:${NC}"
echo -e "  • View live logs:     ${BOLD}docker compose logs -f${NC}"
echo -e "  • Check status:       ${BOLD}docker compose ps${NC}"
echo -e "  • Restart backend:    ${BOLD}docker compose restart backend${NC}"
echo -e "  • Stop all services:  ${BOLD}docker compose down${NC}"
echo -e "${GREEN}====================================================${NC}\n"

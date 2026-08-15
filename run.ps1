# Job Scout Windows PowerShell Bootstrapper
param (
    [switch]$Local = $false
)

$ErrorActionPreference = "Stop"

Write-Host "====================================================" -ForegroundColor Green
Write-Host "🚀 Initializing Job Scout Dev Stack (PowerShell)..." -ForegroundColor Green
Write-Host "====================================================" -ForegroundColor Green

# 1. Check if Docker is installed and running
try {
    docker info > $null 2>&1
    Write-Host "[OK] Docker daemon is running." -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Docker is not running or not installed. Docker is required to run the stack." -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again." -ForegroundColor Yellow
    exit 1
}

# 2. Set up environment config files (.env)
if (-Not (Test-Path ".env")) {
    Write-Host "[Setup] Root .env file not found. Creating from .env.example..." -ForegroundColor Cyan
    Copy-Item ".env.example" ".env"
}

if (-Not (Test-Path "backend/.env")) {
    Write-Host "[Setup] Backend .env file not found. Creating from .env.example..." -ForegroundColor Cyan
    Copy-Item ".env.example" "backend/.env"
}

# Check if user requested Full Docker Mode (Default) or Local Host Mode
if (-Not $Local) {
    Write-Host "[Docker] Launching Full Job Scout Stack via Docker Compose..." -ForegroundColor Cyan
    docker compose up -d --build

    Start-Sleep -Seconds 3

    Write-Host "`n====================================================" -ForegroundColor Green
    Write-Host "   Job Scout is up and running via Docker!          " -ForegroundColor Green
    Write-Host "   - Web App:      http://localhost:3000            " -ForegroundColor Green
    Write-Host "   - Admin Panel:  http://localhost:3000/admin       " -ForegroundColor Green
    Write-Host "   - API Docs:     http://localhost:8001/docs        " -ForegroundColor Green
    Write-Host "   - Redis:        localhost:6380                    " -ForegroundColor Green
    Write-Host "   - PostgreSQL:   localhost:5435                    " -ForegroundColor Green
    Write-Host "====================================================" -ForegroundColor Green
    Write-Host "Useful Commands:" -ForegroundColor Yellow
    Write-Host "  • View live logs:     docker compose logs -f"
    Write-Host "  • Check status:       docker compose ps"
    Write-Host "  • Stop all services:  docker compose down"
    Write-Host "====================================================`n" -ForegroundColor Green
    exit 0
}

# Optional Local Host Mode execution (-Local switch)
Write-Host "[Local] Setting up local Python & Node environment..." -ForegroundColor Yellow

if (-Not (Test-Path "backend/venv")) {
    Write-Host "[Setup] Creating backend virtual environment..." -ForegroundColor Yellow
    python -m venv backend/venv
    Write-Host "[Setup] Installing backend dependencies (pip install)..." -ForegroundColor Yellow
    & .\backend\venv\Scripts\python.exe -m pip install --upgrade pip
    & .\backend\venv\Scripts\python.exe -m pip install -r backend/requirements.txt
}

if (-Not (Test-Path "frontend/node_modules")) {
    Write-Host "[Setup] Installing frontend dependencies (npm install)..." -ForegroundColor Yellow
    Push-Location frontend
    npm install
    Pop-Location
}

# Start DB and Redis containers for local backend
Write-Host "[Docker] Starting Database and Redis services..." -ForegroundColor Cyan
docker compose up -d db redis
Start-Sleep -Seconds 3

# Run DB migrations
Push-Location backend
& .\venv\Scripts\python.exe init_db.py
Pop-Location

$pidsToKill = @()

# Start Backend FastAPI on port 8001
Write-Host "[Backend] Starting FastAPI server on port 8001..." -ForegroundColor Cyan
$backendProcess = Start-Process -FilePath ".\backend\venv\Scripts\python.exe" -ArgumentList "-m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload" -WorkingDirectory ".\backend" -RedirectStandardOutput ".\backend\backend.log" -RedirectStandardError ".\backend\backend_errors.log" -PassThru -WindowStyle Hidden
$pidsToKill += $backendProcess.Id

# Start Celery Worker
Write-Host "[Celery] Starting Celery worker..." -ForegroundColor Magenta
$celeryWorker = Start-Process -FilePath ".\backend\venv\Scripts\python.exe" -ArgumentList "-m celery -A celery_app worker --pool=solo --loglevel=info" -WorkingDirectory ".\scraper" -RedirectStandardOutput ".\scraper\celery_worker.log" -RedirectStandardError ".\scraper\celery_worker_errors.log" -PassThru -WindowStyle Hidden
$pidsToKill += $celeryWorker.Id

Write-Host "====================================================" -ForegroundColor Green
Write-Host "   Job Scout Local Stack Active!                     " -ForegroundColor Green
Write-Host "   - Frontend: http://localhost:3000                 " -ForegroundColor Green
Write-Host "   - Backend:  http://localhost:8001/docs             " -ForegroundColor Green
Write-Host "====================================================" -ForegroundColor Green

try {
    Push-Location frontend
    npm run dev
    Pop-Location
} finally {
    Write-Host "`n[EXIT] Shutting down Job Scout local services..." -ForegroundColor Red
    foreach ($pidToKill in $pidsToKill) {
        Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
    }
    Write-Host "Cleanup complete." -ForegroundColor Green
}

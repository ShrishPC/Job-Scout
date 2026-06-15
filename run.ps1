$ErrorActionPreference = "Stop"

Write-Host "[INIT] Initializing Job Scout Dev Stack (Windows PowerShell)..." -ForegroundColor Green

# 1. Check if Docker is installed and running
try {
    docker info > $null 2>&1
} catch {
    Write-Host "[ERROR] Docker is not running or not installed. PostgreSQL and Redis require Docker to be active." -ForegroundColor Red
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

# 3. Setup Backend Virtual Environment
if (-Not (Test-Path "backend/venv")) {
    Write-Host "[Setup] Creating backend virtual environment..." -ForegroundColor Yellow
    python -m venv backend/venv
    Write-Host "[Setup] Installing backend dependencies (pip install)..." -ForegroundColor Yellow
    & .\backend\venv\Scripts\python.exe -m pip install --upgrade pip
    & .\backend\venv\Scripts\python.exe -m pip install -r backend/requirements.txt
} else {
    Write-Host "[OK] Backend virtual environment detected." -ForegroundColor Green
}

# 4. Setup Playwright in Backend Virtual Environment
Write-Host "[Setup] Installing Playwright Chromium browser binaries..." -ForegroundColor Yellow
& .\backend\venv\Scripts\playwright.exe install chromium

# 5. Setup Frontend Dependencies
if (-Not (Test-Path "frontend/node_modules")) {
    Write-Host "[Setup] Installing frontend dependencies (npm install)..." -ForegroundColor Yellow
    Push-Location frontend
    npm install
    Pop-Location
} else {
    Write-Host "[OK] Frontend dependencies (node_modules) detected." -ForegroundColor Green
}

# 6. Pre-cache Local AI Models
$TINYLLAMA_CACHE = "models/models--TinyLlama--TinyLlama-1.1B-Chat-v1.0"
$MINILM_CACHE = "models/models--sentence-transformers--all-MiniLM-L6-v2"
if ((-Not (Test-Path $TINYLLAMA_CACHE)) -or (-Not (Test-Path $MINILM_CACHE))) {
    Write-Host "[Setup] Cache folders for local models not found. Pre-downloading models..." -ForegroundColor Cyan
    & .\backend\venv\Scripts\python.exe scripts/download_models.py
} else {
    Write-Host "[OK] Local AI models (TinyLlama & MiniLM) are already cached locally." -ForegroundColor Green
}

Write-Host "[DONE] Bootstrapping complete! Launching services..." -ForegroundColor Green

# 7. Start Docker containers (DB and Redis)
Write-Host "[Docker] Starting Database and Redis..." -ForegroundColor Cyan
docker compose up -d db redis

Write-Host "[Docker] Waiting for PostgreSQL and Redis to be healthy..." -ForegroundColor Cyan
Start-Sleep -Seconds 2

# 8. Run Database Migrations/Initialization
Write-Host "[Database] Running database initialization..." -ForegroundColor Yellow
Push-Location backend
& .\venv\Scripts\python.exe init_db.py
Pop-Location

$pidsToKill = @()

# 9. Start Backend FastAPI
Write-Host "[Backend] Starting FastAPI server on port 8000..." -ForegroundColor Cyan
$backendProcess = Start-Process -FilePath ".\backend\venv\Scripts\python.exe" -ArgumentList "-m uvicorn app.main:app --host 0.0.0.0 --port 8000" -WorkingDirectory ".\backend" -RedirectStandardOutput ".\backend\backend.log" -RedirectStandardError ".\backend\backend_errors.log" -PassThru -WindowStyle Hidden
$pidsToKill += $backendProcess.Id

# 10. Start Celery Worker (Crucial: using --pool=solo for Windows)
Write-Host "[Celery] Starting Celery worker..." -ForegroundColor Magenta
$celeryWorker = Start-Process -FilePath ".\backend\venv\Scripts\python.exe" -ArgumentList "-m celery -A celery_app worker --pool=solo --loglevel=info" -WorkingDirectory ".\scraper" -RedirectStandardOutput ".\scraper\celery_worker.log" -RedirectStandardError ".\scraper\celery_worker_errors.log" -PassThru -WindowStyle Hidden
$pidsToKill += $celeryWorker.Id

# 11. Start Celery Beat
Write-Host "[Celery] Starting Celery beat..." -ForegroundColor Magenta
$celeryBeat = Start-Process -FilePath ".\backend\venv\Scripts\python.exe" -ArgumentList "-m celery -A celery_app beat --loglevel=info" -WorkingDirectory ".\scraper" -RedirectStandardOutput ".\scraper\celery_beat.log" -RedirectStandardError ".\scraper\celery_beat_errors.log" -PassThru -WindowStyle Hidden
$pidsToKill += $celeryBeat.Id

Write-Host "====================================================" -ForegroundColor Green
Write-Host "   Job Scout is up and running!                      " -ForegroundColor Green
Write-Host "   - Frontend: http://localhost:3000                 " -ForegroundColor Green
Write-Host "   - Backend Docs: http://localhost:8000/docs        " -ForegroundColor Green
Write-Host "====================================================" -ForegroundColor Green
Write-Host "Logs are written to:" -ForegroundColor Yellow
Write-Host "  - Backend: backend/backend.log"
Write-Host "  - Celery Worker: scraper/celery_worker.log"
Write-Host "  - Celery Beat: scraper/celery_beat.log"
Write-Host "Frontend output is streaming below..." -ForegroundColor Yellow
Write-Host "Press Ctrl+C to shut down all services." -ForegroundColor Yellow
Write-Host "====================================================" -ForegroundColor Green

try {
    # 12. Start Frontend (Next.js) in the foreground
    Push-Location frontend
    npm run dev
    Pop-Location
} finally {
    Write-Host "`n[EXIT] Shutting down Job Scout services..." -ForegroundColor Red
    foreach ($pidToKill in $pidsToKill) {
        Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
    }
    Write-Host "Cleanup complete." -ForegroundColor Green
}

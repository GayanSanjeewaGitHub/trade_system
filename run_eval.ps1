# Ground Truth Evaluation Runner
# Simple PowerShell script to run evaluation via API

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "  Ground Truth Evaluation System" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if backend is running
Write-Host "Checking backend status..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method GET -TimeoutSec 5 -UseBasicParsing
    Write-Host "✅ Backend is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Backend is not running!" -ForegroundColor Red
    Write-Host "   Please start the backend first:" -ForegroundColor Yellow
    Write-Host "   docker-compose -f docker/docker-compose.yml up -d" -ForegroundColor White
    Write-Host ""
    exit 1
}

Write-Host ""

# Ask user for test type
Write-Host "Select evaluation type:" -ForegroundColor Yellow
Write-Host "  1. Quick Test (5 cases)"
Write-Host "  2. Medium Test (10 cases)"
Write-Host "  3. Full Evaluation (all 31 cases)"
Write-Host ""

$choice = Read-Host "Enter choice (1-3)"

$limit = switch ($choice) {
    "1" { 5 }
    "2" { 10 }
    "3" { $null }
    default { 5 }
}

Write-Host ""
Write-Host "Starting evaluation..." -ForegroundColor Yellow
Write-Host ""

# Run evaluation (use simple client with no external dependencies)
if ($limit) {
    python eval_client_simple.py --limit $limit --save
} else {
    python eval_client_simple.py --save
}

$exitCode = $LASTEXITCODE

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
if ($exitCode -eq 0) {
    Write-Host "  Evaluation Complete" -ForegroundColor Green
} else {
    Write-Host "  Evaluation Failed (Exit Code: $exitCode)" -ForegroundColor Red
}
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

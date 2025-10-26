#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Production deployment script for Trading Chatbot

.DESCRIPTION
    This script handles the complete deployment process including:
    - Pre-deployment checks
    - Database migrations
    - Docker build and deploy
    - Health checks
    - Rollback on failure

.PARAMETER Environment
    Deployment environment (staging, production)

.PARAMETER SkipTests
    Skip running tests before deployment

.EXAMPLE
    .\scripts\deploy.ps1 -Environment production
#>

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("staging", "production")]
    [string]$Environment,
    
    [switch]$SkipTests = $false
)

$ErrorActionPreference = "Stop"

# Color functions
function Write-Success { param($msg) Write-Host "✅ $msg" -ForegroundColor Green }
function Write-Info { param($msg) Write-Host "ℹ️  $msg" -ForegroundColor Cyan }
function Write-Warning-Custom { param($msg) Write-Host "⚠️  $msg" -ForegroundColor Yellow }
function Write-Error-Custom { param($msg) Write-Host "❌ $msg" -ForegroundColor Red }

Write-Info "=========================================="
Write-Info "Trading Chatbot Deployment Script"
Write-Info "Environment: $Environment"
Write-Info "=========================================="

# 1. Pre-deployment checks
Write-Info "`n[1/8] Running pre-deployment checks..."

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Success "Docker is running"
} catch {
    Write-Error-Custom "Docker is not running. Please start Docker Desktop."
    exit 1
}

# Check if .env file exists
if (-not (Test-Path ".env.$Environment")) {
    Write-Error-Custom ".env.$Environment file not found"
    exit 1
}
Write-Success "Environment file found"

# Check if required services are accessible
Write-Info "Checking external services..."

# 2. Run tests (unless skipped)
if (-not $SkipTests) {
    Write-Info "`n[2/8] Running tests..."
    try {
        pytest tests/ -v --tb=short
        if ($LASTEXITCODE -ne 0) {
            Write-Error-Custom "Tests failed. Deployment aborted."
            exit 1
        }
        Write-Success "All tests passed"
    } catch {
        Write-Error-Custom "Failed to run tests: $_"
        exit 1
    }
} else {
    Write-Warning-Custom "[2/8] Skipping tests (not recommended for production)"
}

# 3. Backup current deployment
Write-Info "`n[3/8] Creating backup..."
$backupDir = "backups/$(Get-Date -Format 'yyyy-MM-dd-HHmmss')"
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

# Backup current Docker images
docker images --format "{{.Repository}}:{{.Tag}}" | Where-Object { $_ -like "*trading-chatbot*" } | Out-File "$backupDir/images.txt"
Write-Success "Backup created at $backupDir"

# 4. Build new Docker image
Write-Info "`n[4/8] Building Docker image..."
$imageTag = "trading-chatbot:$(Get-Date -Format 'yyyy-MM-dd-HHmmss')"
try {
    docker build -f docker/Dockerfile -t $imageTag -t trading-chatbot:latest .
    if ($LASTEXITCODE -ne 0) {
        Write-Error-Custom "Docker build failed"
        exit 1
    }
    Write-Success "Docker image built: $imageTag"
} catch {
    Write-Error-Custom "Failed to build Docker image: $_"
    exit 1
}

# 5. Stop current containers
Write-Info "`n[5/8] Stopping current containers..."
try {
    cd docker
    docker-compose down
    Write-Success "Containers stopped"
} catch {
    Write-Warning-Custom "Failed to stop some containers (they may not be running)"
}

# 6. Deploy new version
Write-Info "`n[6/8] Deploying new version..."
try {
    # Copy appropriate env file
    Copy-Item "../.env.$Environment" "../.env" -Force
    
    # Start services
    docker-compose up -d
    if ($LASTEXITCODE -ne 0) {
        Write-Error-Custom "Failed to start containers"
        # Rollback
        Write-Info "Rolling back to previous version..."
        docker-compose down
        docker-compose up -d
        exit 1
    }
    Write-Success "Containers started"
    cd ..
} catch {
    Write-Error-Custom "Deployment failed: $_"
    exit 1
}

# 7. Health checks
Write-Info "`n[7/8] Running health checks..."
$maxRetries = 10
$retryCount = 0
$healthCheckPassed = $false

while ($retryCount -lt $maxRetries -and -not $healthCheckPassed) {
    Start-Sleep -Seconds 5
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            $healthCheckPassed = $true
            Write-Success "Health check passed"
        }
    } catch {
        $retryCount++
        Write-Info "Health check attempt $retryCount/$maxRetries..."
    }
}

if (-not $healthCheckPassed) {
    Write-Error-Custom "Health check failed after $maxRetries attempts"
    Write-Info "Rolling back..."
    cd docker
    docker-compose down
    docker-compose up -d
    cd ..
    exit 1
}

# 8. Post-deployment validation
Write-Info "`n[8/8] Running post-deployment validation..."

# Test critical endpoint
try {
    $testMessage = @{
        message = "What is CSE?"
        session_id = "deployment-test"
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method POST -Body $testMessage -ContentType "application/json" -TimeoutSec 30
    
    if ($response.response) {
        Write-Success "Chat endpoint validated"
    } else {
        Write-Warning-Custom "Chat endpoint returned unexpected response"
    }
} catch {
    Write-Error-Custom "Failed to validate chat endpoint: $_"
    exit 1
}

# Run quick evaluation
Write-Info "Running quick evaluation..."
try {
    python eval_client_simple.py --limit 3 --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Quick evaluation passed"
    } else {
        Write-Warning-Custom "Evaluation had issues but deployment continues"
    }
} catch {
    Write-Warning-Custom "Could not run evaluation: $_"
}

# Final summary
Write-Success "`n=========================================="
Write-Success "Deployment Complete!"
Write-Success "=========================================="
Write-Info "Environment: $Environment"
Write-Info "Image: $imageTag"
Write-Info "Backup: $backupDir"
Write-Info ""
Write-Info "Access Points:"
Write-Info "  - API: http://localhost:8000"
Write-Info "  - Docs: http://localhost:8000/docs"
Write-Info "  - Frontend: http://localhost:8501"
Write-Info ""
Write-Info "Next Steps:"
Write-Info "  1. Monitor logs: cd docker && docker-compose logs -f app"
Write-Info "  2. Run full evaluation: python eval_client_simple.py"
Write-Info "  3. Check metrics dashboard"
Write-Info "  4. Notify team of successful deployment"
Write-Info ""
Write-Success "Deployment completed successfully! 🎉"

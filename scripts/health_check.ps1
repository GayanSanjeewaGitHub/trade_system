#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Health check script for Trading Chatbot

.DESCRIPTION
    Comprehensive health checks for all system components
    
.EXAMPLE
    .\scripts\health_check.ps1
#>

$ErrorActionPreference = "Continue"

function Write-Success { param($msg) Write-Host "✅ $msg" -ForegroundColor Green }
function Write-Fail { param($msg) Write-Host "❌ $msg" -ForegroundColor Red }
function Write-Info-Custom { param($msg) Write-Host "ℹ️  $msg" -ForegroundColor Cyan }

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Trading Chatbot Health Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$allHealthy = $true

# 1. Docker Containers
Write-Info-Custom "[1/7] Checking Docker containers..."
try {
    cd docker
    $containers = docker-compose ps --format json | ConvertFrom-Json
    
    $requiredServices = @("trading-chatbot", "trading-chatbot-postgres", "trading-chatbot-redis", "trading-chatbot-langfuse")
    
    foreach ($service in $requiredServices) {
        $container = $containers | Where-Object { $_.Service -eq $service.Replace("trading-chatbot-", "").Replace("trading-chatbot", "app") }
        if ($container -and $container.State -eq "running") {
            Write-Success "$service is running"
        } else {
            Write-Fail "$service is NOT running"
            $allHealthy = $false
        }
    }
    cd ..
} catch {
    Write-Fail "Failed to check Docker containers: $_"
    $allHealthy = $false
    cd ..
}

# 2. Backend API Health
Write-Host ""
Write-Info-Custom "[2/7] Checking backend API..."
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET -TimeoutSec 10
    
    if ($response.status -eq "healthy") {
        Write-Success "Backend API is healthy"
        Write-Host "  Version: $($response.version)" -ForegroundColor Gray
        Write-Host "  Environment: $($response.environment)" -ForegroundColor Gray
        
        # Check components
        foreach ($component in $response.components.PSObject.Properties) {
            if ($component.Value) {
                Write-Success "  $($component.Name): OK"
            } else {
                Write-Fail "  $($component.Name): NOT OK"
                $allHealthy = $false
            }
        }
    } else {
        Write-Fail "Backend API is unhealthy: $($response.status)"
        $allHealthy = $false
    }
} catch {
    Write-Fail "Backend API is not responding: $_"
    $allHealthy = $false
}

# 3. Database Connectivity
Write-Host ""
Write-Info-Custom "[3/7] Checking PostgreSQL..."
try {
    cd docker
    $result = docker-compose exec -T postgres pg_isready -U langfuse 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "PostgreSQL is ready"
    } else {
        Write-Fail "PostgreSQL is not ready"
        $allHealthy = $false
    }
    cd ..
} catch {
    Write-Fail "Failed to check PostgreSQL: $_"
    $allHealthy = $false
    cd ..
}

# 4. Redis Connectivity
Write-Host ""
Write-Info-Custom "[4/7] Checking Redis..."
try {
    cd docker
    $result = docker-compose exec -T redis redis-cli ping 2>&1
    if ($result -match "PONG") {
        Write-Success "Redis is responsive"
    } else {
        Write-Fail "Redis is not responsive"
        $allHealthy = $false
    }
    cd ..
} catch {
    Write-Fail "Failed to check Redis: $_"
    $allHealthy = $false
    cd ..
}

# 5. Langfuse
Write-Host ""
Write-Info-Custom "[5/7] Checking Langfuse..."
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Success "Langfuse is accessible"
    } else {
        Write-Fail "Langfuse returned status code: $($response.StatusCode)"
        $allHealthy = $false
    }
} catch {
    Write-Fail "Langfuse is not accessible: $_"
    $allHealthy = $false
}

# 6. Frontend (if running)
Write-Host ""
Write-Info-Custom "[6/7] Checking Streamlit frontend..."
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8501" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Success "Frontend is accessible"
    } else {
        Write-Host "  ⚠️  Frontend status: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ℹ️  Frontend is not running (optional)" -ForegroundColor Gray
}

# 7. Critical Endpoint Test
Write-Host ""
Write-Info-Custom "[7/7] Testing critical endpoint..."
try {
    $testBody = @{
        message = "Test health check"
        session_id = "health-check-$(Get-Date -Format 'yyyyMMddHHmmss')"
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method POST -Body $testBody -ContentType "application/json" -TimeoutSec 30
    
    if ($response.response) {
        Write-Success "Chat endpoint is functional"
        Write-Host "  Response received in test" -ForegroundColor Gray
    } else {
        Write-Fail "Chat endpoint returned empty response"
        $allHealthy = $false
    }
} catch {
    Write-Fail "Chat endpoint test failed: $_"
    $allHealthy = $false
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
if ($allHealthy) {
    Write-Success "All Health Checks Passed ✓"
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "System Status: HEALTHY" -ForegroundColor Green
    Write-Host ""
    exit 0
} else {
    Write-Fail "Some Health Checks Failed ✗"
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "System Status: UNHEALTHY" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "  1. Check Docker services: cd docker && docker-compose ps"
    Write-Host "  2. View logs: cd docker && docker-compose logs -f"
    Write-Host "  3. Restart services: cd docker && docker-compose restart"
    Write-Host "  4. Full rebuild: cd docker && docker-compose up --build -d"
    Write-Host ""
    exit 1
}

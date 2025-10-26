@echo off
REM Ground Truth Evaluation Runner for Windows

echo.
echo ================================================================================
echo   Ground Truth Evaluation System
echo ================================================================================
echo.

REM Check if backend is running
echo Checking backend status...
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Backend is not running!
    echo Please start the backend first:
    echo   docker-compose -f docker/docker-compose.yml up -d
    echo.
    pause
    exit /b 1
)
echo [OK] Backend is running
echo.

REM Ask user for test type
echo Select evaluation type:
echo   1. Quick Test (5 cases)
echo   2. Medium Test (10 cases)
echo   3. Full Evaluation (all 31 cases)
echo.

set /p choice="Enter choice (1-3): "

if "%choice%"=="1" (
    set limit=5
) else if "%choice%"=="2" (
    set limit=10
) else (
    set limit=
)

echo.
echo Starting evaluation...
echo.

REM Run evaluation
if defined limit (
    python eval_client.py --limit %limit% --save
) else (
    python eval_client.py --save
)

echo.
echo ================================================================================
echo   Evaluation Complete
echo ================================================================================
echo.
pause

# Start Streamlit Frontend
Write-Host "Starting Trading Chatbot Frontend..." -ForegroundColor Green
Write-Host ""
Write-Host "Make sure the backend is running first:" -ForegroundColor Yellow
Write-Host "  docker-compose -f docker/docker-compose.yml up" -ForegroundColor Yellow
Write-Host ""
Write-Host "Starting Streamlit on http://localhost:8501" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Cyan
Write-Host ""

# Run Streamlit
& "$PSScriptRoot\.venv\Scripts\streamlit.exe" run "$PSScriptRoot\app.py"

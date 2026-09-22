# JudiQ AI Unified Platform Launcher
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   JUDIQ AI - UNIFIED LITIGATION INTELLIGENCE PLATFORM (LOCAL)  " -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  [*] Web Application:   http://localhost:8000" -ForegroundColor Green
Write-Host "  [*] Swagger API Docs:  http://localhost:8000/docs" -ForegroundColor Green
Write-Host "  [*] Health Probe:      http://localhost:8000/health" -ForegroundColor Green
Write-Host ""
Write-Host "  [*] Launching browser interface..." -ForegroundColor Yellow

Start-Process "http://localhost:8000"

Set-Location "$PSScriptRoot/backend"
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

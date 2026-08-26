# JudiQ AI Unified Platform Launcher
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  Starting JudiQ AI Unified Platform (Localhost)  " -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Application: http://localhost:8000" -ForegroundColor Green
Write-Host "Swagger UI:  http://localhost:8000/docs" -ForegroundColor Green
Write-Host "Health:      http://localhost:8000/health" -ForegroundColor Green
Write-Host ""

Set-Location "$PSScriptRoot/backend"
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

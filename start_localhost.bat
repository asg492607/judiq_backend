@echo off
setlocal
title JudiQ AI Unified Platform (Localhost:8000)

echo ================================================================
echo   JUDIQ AI - UNIFIED LITIGATION INTELLIGENCE PLATFORM (LOCAL)
echo ================================================================
echo.
echo   [*] Web Application:   http://localhost:8000
echo   [*] Swagger API Docs:  http://localhost:8000/docs
echo   [*] Health Probe:      http://localhost:8000/health
echo.
echo   [*] Launching browser interface...
start "" "http://localhost:8000"
echo.

cd /d "%~dp0backend"
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Server terminated or Python is not found.
    pause
)

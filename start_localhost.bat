@echo off
echo ===================================================
echo   Starting JudiQ AI Unified Platform (Localhost)
echo ===================================================
echo.
echo Application will be live at: http://localhost:8000
echo API Docs (Swagger):          http://localhost:8000/docs
echo Health Check:               http://localhost:8000/health
echo.
cd /d "%~dp0backend"
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
pause

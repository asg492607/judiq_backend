@echo off
echo ===================================================
echo   Compiling JudiQ AI Standalone Android APK
echo ===================================================
echo.
cd /d "%~dp0"
python build_apk.py
pause

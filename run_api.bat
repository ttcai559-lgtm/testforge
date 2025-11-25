@echo off
echo Starting TestForge API Server...
echo.

cd /d "%~dp0"

python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

pause

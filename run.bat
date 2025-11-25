@echo off
echo Starting TestForge...
cd /d %~dp0
python -m streamlit run src/ui/app.py
pause

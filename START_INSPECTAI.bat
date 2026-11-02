@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv-inspect\Scripts\python.exe" (
 echo Run setup_windows.bat first.
 pause
 exit /b 1
)
set OMP_NUM_THREADS=4
set MKL_NUM_THREADS=4
echo Open http://127.0.0.1:8000 in Chrome after startup completes.
echo Keep this window open. Press Ctrl+C to stop the app.
.venv-inspect\Scripts\python.exe -m uvicorn inspection.api:app --host 127.0.0.1 --port 8000
pause

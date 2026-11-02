@echo off
setlocal
cd /d "%~dp0"
echo Creating a Python 3.12 environment for InspectAI...
py -3.12 -m venv .venv-inspect
if errorlevel 1 goto fail
.venv-inspect\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 goto fail
.venv-inspect\Scripts\python.exe -m pip install torch==2.15.0 torchvision==0.29.2 --index-url https://download.pytorch.org/whl/cpu
if errorlevel 1 goto fail
.venv-inspect\Scripts\python.exe -m pip install -r requirements-dev.txt
if errorlevel 1 goto fail
echo.
echo Setup complete. Double-click START_INSPECTAI.bat next.
pause
exit /b 0
:fail
echo.
echo Setup failed. Install Python 3.12 with the Python Launcher, then retry.
echo Copy the error above if you need help. Internet is needed for installation.
pause
exit /b 1

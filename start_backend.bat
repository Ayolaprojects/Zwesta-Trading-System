@echo off
setlocal
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set ZWESTA_SKIP_PYTHON_REEXEC=1
set MT5_STARTUP_WARMUP=0
if not defined PORT set PORT=9000

set "PYTHON_EXE=%~dp0venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"

start "ZwestaBackend" /B "%PYTHON_EXE%" "%~dp0multi_broker_backend_updated.py"

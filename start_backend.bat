@echo off
setlocal
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
start "ZwestaBackend" /B ""C:\zwesta-trader\.venv\Scripts\python.exe" "%~dp0multi_broker_backend_updated.py"

@echo off
cd /d "C:\zwesta-trader\Zwesta Flutter App"
set PYTHONIOENCODING=utf-8
set ZWESTA_SKIP_PYTHON_REEXEC=1
set MT5_STARTUP_WARMUP=0
if not defined PORT set PORT=9000
start "Zwesta Backend" ".venv\Scripts\python.exe" -u "multi_broker_backend_updated.py" > "C:\backend\backend_fast.log" 2>&1

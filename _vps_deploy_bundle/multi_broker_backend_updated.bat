@echo off
setlocal

set "BACKEND_DIR=%~dp0"
if "%BACKEND_DIR:~-1%"=="\" set "BACKEND_DIR=%BACKEND_DIR:~0,-1%"

set "PYTHON_EXE=c:\zwesta-trader\.venv\Scripts\python.exe"
set "BACKEND_SCRIPT=%BACKEND_DIR%\multi_broker_backend_updated.py"
set "SAFE_STARTER=%BACKEND_DIR%\start_zwesta.bat"

if not exist "%BACKEND_SCRIPT%" (
    echo ERROR: %BACKEND_SCRIPT% was not found.
    exit /b 1
)

if "%~1"=="" (
    if exist "%SAFE_STARTER%" (
        call "%SAFE_STARTER%"
        exit /b %ERRORLEVEL%
    )
)

if /I "%~1"=="/?" (
    echo Usage:
    echo   multi_broker_backend_updated        Starts or reuses the managed backend service
    echo   multi_broker_backend_updated [args] Runs multi_broker_backend_updated.py with the project virtualenv Python
    exit /b 0
)

if not exist "%PYTHON_EXE%" (
    echo ERROR: %PYTHON_EXE% was not found.
    echo Start the backend with start_zwesta.bat after restoring the project virtualenv.
    exit /b 1
)

pushd "%BACKEND_DIR%"
"%PYTHON_EXE%" "%BACKEND_SCRIPT%" %*
set "EXIT_CODE=%ERRORLEVEL%"
popd

exit /b %EXIT_CODE%
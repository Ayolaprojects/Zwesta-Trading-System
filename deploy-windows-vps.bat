@echo off
REM Zwesta Trading System - Windows VPS Deployment Script
REM This script deploys the application to a Windows VPS

setlocal enabledelayedexpansion

REM Colors simulation
for /F %%A in ('copy /Z "%~f0" nul') do set "BS=%%A"

cls
echo.
echo ================================================================================
echo   Zwesta Trading System - WINDOWS VPS DEPLOYMENT
echo ================================================================================
echo.
echo This script will:
echo   1. Check prerequisites
echo   2. Setup Python environment
echo   3. Install dependencies
echo   4. Configure Windows services
echo   5. Setup Nginx reverse proxy
echo   6. Generate SSL certificates
echo   7. Start services
echo.
echo Press any key to continue...
pause >nul

REM Check if running as Administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] This script must be run as Administrator!
    color 07
    pause
    exit /b 1
)

echo [OK] Running as Administrator

REM ============================================================================
REM STEP 1: Check Prerequisites
REM ============================================================================
echo.
echo ================================================================================
echo   STEP 1: Checking Prerequisites
echo ================================================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Installing Python 3.11...
    REM Download and install Python (requires user interaction or automation)
    echo Please download Python 3.11 from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
)
echo [OK] Python found

REM ============================================================================
REM STEP 2: Setup Virtual Environment
REM ============================================================================
echo.
echo ================================================================================
echo   STEP 2: Creating Virtual Environment
echo ================================================================================
echo.

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
)

call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment activated

REM ============================================================================
REM STEP 3: Install Python Dependencies
REM ============================================================================
echo.
echo ================================================================================
echo   STEP 3: Installing Python Dependencies
echo ================================================================================
echo.

pip install --upgrade pip --quiet
pip install -r requirements-production.txt --quiet
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Python dependencies installed

REM ============================================================================
REM STEP 4: Create Windows Service
REM ============================================================================
echo.
echo ================================================================================
echo   STEP 4: Creating Windows Service
echo ================================================================================
echo.

REM Check if NSSM is available (Non-Sucking Service Manager)
where nssm >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] NSSM not found. Installing NSSM for service management...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "iwr https://nssm.cc/download/nssm-2.24-101-g897c7ad.zip -OutFile nssm.zip; Expand-Archive nssm.zip; move nssm-*\win64\nssm.exe .; rm -r nssm*"
    if %errorlevel% neq 0 (
        echo [WARN] Failed to install NSSM. Service creation skipped.
        echo You will need to manually create a service or use Task Scheduler.
        pause
    )
)

REM Create service if NSSM is available
where nssm >nul 2>&1
if %errorlevel% equ 0 (
    echo Creating 'zwesta-trading' service...
    nssm install zwesta-trading "%CD%\venv\Scripts\python.exe" "%CD%\multi_broker_backend_updated.py"
    nssm set zwesta-trading AppDirectory "%CD%"
    nssm set zwesta-trading AppEnvironmentExtra "PATH=!PATH!"
    nssm start zwesta-trading
    echo [OK] Service created and started
)

REM ============================================================================
REM STEP 5: Download and Setup Nginx
REM ============================================================================
echo.
echo ================================================================================
echo   STEP 5: Setting Up Nginx Reverse Proxy
echo ================================================================================
echo.

if not exist "nginx" (
    echo Downloading Nginx...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "iwr http://nginx.org/download/nginx-1.25.4.zip -OutFile nginx.zip; Expand-Archive nginx.zip; mv nginx-* nginx"
    if %errorlevel% neq 0 (
        echo [WARN] Failed to download Nginx. Skipping reverse proxy setup.
    ) else (
        echo [OK] Nginx downloaded and extracted
        
        REM Copy production config
        echo Configuring Nginx...
        copy /Y nginx-prod.conf nginx\conf\nginx.conf
        if %errorlevel% equ 0 (
            echo [OK] Nginx configured
        )
    )
)

REM ============================================================================
REM STEP 6: Create Self-Signed SSL Certificate
REM ============================================================================
echo.
echo ================================================================================
echo   STEP 6: Generating SSL Certificate
echo ================================================================================
echo.

if not exist "certs" mkdir certs

if not exist "certs\fullchain.pem" (
    echo Generating self-signed certificate (valid for 365 days)...
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "$params = @{ DnsName='localhost'; FriendlyName='Zwesta LocalHost'; NotAfter=(Get-Date).AddDays(365) }; " ^
        "$cert = New-SelfSignedCertificate @params -KeyExportPolicy Exportable -KeySpec KeyExchange -KeyLength 2048; " ^
        "Export-Certificate -Cert $cert -FilePath 'certs\fullchain.cer' -Force"
    
    echo [OK] SSL certificate generated
    echo Location: certs\fullchain.cer
) else (
    echo [OK] SSL certificate already exists
)

REM ============================================================================
REM STEP 7: Setup Firewall Rules
REM ============================================================================
echo.
echo ================================================================================
echo   STEP 7: Configuring Windows Firewall
echo ================================================================================
echo.

netsh advfirewall firewall show rule name="Zwesta Trading Port 9000" >nul 2>&1
if %errorlevel% neq 0 (
    echo Adding firewall rule for port 9000...
    netsh advfirewall firewall add rule name="Zwesta Trading Port 9000" dir=in action=allow protocol=tcp localport=9000
    echo [OK] Firewall rule added
) else (
    echo [OK] Firewall rule already exists
)

REM ============================================================================
REM STEP 8: Create Environment File
REM ============================================================================
echo.
echo ================================================================================
echo   STEP 8: Creating Configuration File
echo ================================================================================
echo.

if not exist ".env.production" (
    copy /Y .env.production.example .env.production
    echo [OK] Configuration file created (.env.production)
    echo IMPORTANT: Edit .env.production with your actual settings!
    echo.
) else (
    echo [OK] Configuration file exists
)

REM ============================================================================
REM STEP 9: Create Directories
REM ============================================================================
echo.
echo ================================================================================
echo   STEP 9: Creating Required Directories
echo ================================================================================
echo.

if not exist "logs" mkdir logs
if not exist "data" mkdir data
if not exist "backups" mkdir backups

echo [OK] Directories created

REM ============================================================================
REM STEP 10: Display Status and Instructions
REM ============================================================================
echo.
echo ================================================================================
echo   DEPLOYMENT COMPLETE
echo ================================================================================
echo.
echo Services Status:
echo ----------------------------

tasklist /FI "IMAGENAME eq gunicorn.exe" >nul 2>&1
if %errorlevel% equ 0 (
    echo [RUNNING] Backend API (port 9000)
) else (
    echo [STOPPED] Backend API (port 9000)
)

tasklist /FI "IMAGENAME eq nginx.exe" >nul 2>&1
if %errorlevel% equ 0 (
    echo [RUNNING] Nginx Reverse Proxy (port 80/443)
) else (
    echo [STOPPED] Nginx Reverse Proxy (port 80/443)
)

echo.
echo Access Points:
echo ----------------------------
echo   API Server:    http://localhost:9000/api/health
echo   Dashboard:     http://localhost/
echo   Logs:          logs\
echo   Configuration: .env.production
echo.
echo Next Steps:
echo ----------------------------
echo 1. Edit .env.production with your settings
echo 2. Start Nginx: nginx\nginx.exe
echo 3. Monitor logs: logs\trading_backend.log
echo 4. Configure brokers via API
echo.

pause

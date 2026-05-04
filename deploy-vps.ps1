# ZWESTA TRADING BOT - VPS AUTOMATED DEPLOYMENT SCRIPT
# Run as Administrator on Windows Server 148.113.5.39
# Purpose: Build and deploy the current React frontend to VPS

# =====================================================
# CONFIGURATION
# =====================================================
$VPS_WEB_ROOT = "C:\zwesta-trader-web"
$FRONTEND_ROOT = "C:\zwesta-trader\zwesta-v3-advanced\frontend"
$LOCAL_BUILD_PATH = Join-Path $FRONTEND_ROOT "dist"
$PYTHON_EXECUTABLE = "python"
$NPM_EXECUTABLE = "npm"
$HTTP_PORT = 80

Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  ZWESTA TRADING BOT - VPS DEPLOYMENT SCRIPT        ║" -ForegroundColor Cyan
Write-Host "║  Windows Server 148.113.5.39                       ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Cyan

# =====================================================
# STEP 1: VERIFY ADMINISTRATOR PRIVILEGES
# =====================================================
Write-Host "`n[1/8] Verifying Administrator privileges..." -ForegroundColor Yellow
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "❌ ERROR: This script requires Administrator privileges!" -ForegroundColor Red
    Write-Host "   Please right-click this script and select 'Run as Administrator'" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Administrator privileges confirmed" -ForegroundColor Green

# =====================================================
# STEP 2: BUILD FRONTEND FROM CURRENT REPO STATE
# =====================================================
Write-Host "`n[2/8] Building frontend from current repo state..." -ForegroundColor Yellow
if (-not (Test-Path (Join-Path $FRONTEND_ROOT "package.json"))) {
    Write-Host "❌ ERROR: Frontend package.json not found at: $FRONTEND_ROOT" -ForegroundColor Red
    exit 1
}

$previousLocation = Get-Location
Set-Location $FRONTEND_ROOT

if (-not (Test-Path (Join-Path $FRONTEND_ROOT "node_modules"))) {
    Write-Host "   Installing frontend dependencies..." -ForegroundColor Cyan
    & cmd /c "npm install"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ ERROR: npm install failed" -ForegroundColor Red
        Set-Location $previousLocation
        exit 1
    }
}

& cmd /c "npm run build"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ ERROR: npm run build failed" -ForegroundColor Red
    Set-Location $previousLocation
    exit 1
}

Set-Location $previousLocation

if (-not (Test-Path (Join-Path $LOCAL_BUILD_PATH "index.html"))) {
    Write-Host "❌ ERROR: Frontend build output not found at: $LOCAL_BUILD_PATH" -ForegroundColor Red
    exit 1
}

$fileCount = (Get-ChildItem -Path $LOCAL_BUILD_PATH -Recurse -File).Count
Write-Host "✅ Built $fileCount frontend files at $LOCAL_BUILD_PATH" -ForegroundColor Green

# =====================================================
# STEP 3: VERIFY PYTHON IS INSTALLED
# =====================================================
Write-Host "`n[3/8] Verifying runtime tools..." -ForegroundColor Yellow
try {
    $pythonVersion = & python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: Python not installed!" -ForegroundColor Red
    Write-Host "   Install Python from: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

try {
    $npmVersion = & cmd /c "npm --version" 2>&1
    Write-Host "✅ npm found: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: npm not installed!" -ForegroundColor Red
    Write-Host "   Install Node.js from: https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}

# =====================================================
# STEP 4: STOP EXISTING FRONTEND SERVER
# =====================================================
Write-Host "`n[4/8] Stopping existing frontend server on port $HTTP_PORT..." -ForegroundColor Yellow
$listener = Get-NetTCPConnection -LocalPort $HTTP_PORT -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if ($listener) {
    Write-Host "   Stopping process PID $($listener.OwningProcess) bound to port $HTTP_PORT..." -ForegroundColor Cyan
    Stop-Process -Id $listener.OwningProcess -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Write-Host "✅ Frontend server stopped" -ForegroundColor Green
} else {
    Write-Host "✅ No running frontend server found on port $HTTP_PORT" -ForegroundColor Green
}

# =====================================================
# STEP 5: CREATE/CLEAR VPS WEB DIRECTORY
# =====================================================
Write-Host "`n[5/8] Preparing VPS web directory..." -ForegroundColor Yellow
if (Test-Path $VPS_WEB_ROOT) {
    Write-Host "   Clearing existing files from: $VPS_WEB_ROOT" -ForegroundColor Cyan
    Remove-Item "$VPS_WEB_ROOT\*" -Recurse -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
} else {
    Write-Host "   Creating directory: $VPS_WEB_ROOT" -ForegroundColor Cyan
    New-Item -ItemType Directory -Path $VPS_WEB_ROOT -Force | Out-Null
}
Write-Host "✅ VPS directory ready" -ForegroundColor Green

# =====================================================
# STEP 6: COPY NEW BUILD FILES TO VPS
# =====================================================
Write-Host "`n[6/8] Copying build files to VPS..." -ForegroundColor Yellow
Write-Host "   Source: $LOCAL_BUILD_PATH" -ForegroundColor Cyan
Write-Host "   Destination: $VPS_WEB_ROOT" -ForegroundColor Cyan

try {
    Copy-Item "$LOCAL_BUILD_PATH\*" -Destination $VPS_WEB_ROOT -Recurse -Force
    Start-Sleep -Seconds 1
    
    $copiedFiles = (Get-ChildItem -Path $VPS_WEB_ROOT -Recurse -File).Count
    Write-Host "✅ Copied $copiedFiles files to VPS" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: Failed to copy files!" -ForegroundColor Red
    Write-Host "   Error: $_" -ForegroundColor Red
    exit 1
}

# =====================================================
# STEP 7: VERIFY CRITICAL FILES
# =====================================================
Write-Host "`n[7/8] Verifying critical files..." -ForegroundColor Yellow
$criticalFiles = @(
    "index.html",
    "assets"
)

$allFound = $true
foreach ($file in $criticalFiles) {
    $fullPath = Join-Path $VPS_WEB_ROOT $file
    if (Test-Path $fullPath) {
        Write-Host "   ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $file - NOT FOUND" -ForegroundColor Red
        $allFound = $false
    }
}

if (-not $allFound) {
    Write-Host "⚠️ WARNING: Some files are missing! Deployment may fail." -ForegroundColor Yellow
}

# =====================================================
# STEP 8: START FRONTEND STATIC SERVER
# =====================================================
Write-Host "`n[8/8] Starting Python HTTP server on port $HTTP_PORT..." -ForegroundColor Yellow
Write-Host "   Changing directory to: $VPS_WEB_ROOT" -ForegroundColor Cyan

# Start HTTP server in background
$pythonScript = @"
import os
os.chdir(r'$VPS_WEB_ROOT')
import http.server
import socketserver
import signal

class MyHTTPHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f'[HTTP] {format % args}')

PORT = $HTTP_PORT
Handler = MyHTTPHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f'✅ Server started on http://0.0.0.0:{PORT}')
    print('Press Ctrl+C to stop')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\\n✅ Server stopped gracefully')

"@

# Save and run Python script
$pythonScriptPath = "$VPS_WEB_ROOT\server.py"
Set-Content -Path $pythonScriptPath -Value $pythonScript

# Start server (will run in current PowerShell window)
Write-Host "`n" -ForegroundColor Cyan
Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  ✅ DEPLOYMENT SUCCESSFUL!                        ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host "`n📍 ACCESS YOUR APP:" -ForegroundColor Cyan
Write-Host "   🌍 http://148.113.5.39" -ForegroundColor Yellow
Write-Host "`n🔐 LOGIN CREDENTIALS:" -ForegroundColor Cyan
Write-Host "   Username: demo" -ForegroundColor Yellow
Write-Host "   Password: demo123" -ForegroundColor Yellow
Write-Host "`n📋 DEPLOYMENT SUMMARY:" -ForegroundColor Cyan
Write-Host "   Files Deployed: $(Get-ChildItem -Path $VPS_WEB_ROOT -Recurse -File | Measure-Object).Count" -ForegroundColor Yellow
Write-Host "   Server Port: $HTTP_PORT" -ForegroundColor Yellow
Write-Host "   VPS Address: 148.113.5.39" -ForegroundColor Yellow
Write-Host "`n⚠️  KEEP THIS WINDOW OPEN TO KEEP SERVER RUNNING" -ForegroundColor Magenta
Write-Host "   Press Ctrl+C to stop the server" -ForegroundColor Magenta
Write-Host "`n"

# Start the server
cd $VPS_WEB_ROOT
python -m http.server $HTTP_PORT

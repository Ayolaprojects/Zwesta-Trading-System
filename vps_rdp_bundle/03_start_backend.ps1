param(
    [string]$AppPath = 'C:\zwesta-app',
    [int]$Port = 9000
)

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $AppPath

$pythonPath = Join-Path $AppPath 'venv\Scripts\python.exe'
$backendPath = Join-Path $AppPath 'multi_broker_backend_updated.py'
$logDir = Join-Path $AppPath 'logs'
$stdoutLog = Join-Path $logDir 'backend_stdout.log'
$stderrLog = Join-Path $logDir 'backend_stderr.log'

if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw "Python executable not found: $pythonPath"
}

if (-not (Test-Path -LiteralPath $backendPath)) {
    throw "Backend script not found: $backendPath"
}

if (-not (Test-Path -LiteralPath $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

$env:ZWESTA_SKIP_PYTHON_REEXEC = '1'
$env:MT5_STARTUP_WARMUP = '0'
$env:PORT = "$Port"

Write-Host "Starting backend on port $Port..." -ForegroundColor Cyan
$process = Start-Process -FilePath $pythonPath -ArgumentList $backendPath -WorkingDirectory $AppPath -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog -PassThru
Write-Host "Backend process started. PID: $($process.Id)" -ForegroundColor Green
Write-Host "Stdout log: $stdoutLog" -ForegroundColor Yellow
Write-Host "Stderr log: $stderrLog" -ForegroundColor Yellow

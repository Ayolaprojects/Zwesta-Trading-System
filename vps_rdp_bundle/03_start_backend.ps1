param(
    [string]$AppPath = 'C:\zwesta-app',
    [int]$Port = 9000,
    [int]$RestartDelaySeconds = 5
)

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $AppPath

$pythonPath = Join-Path $AppPath 'venv\Scripts\python.exe'
$backendPath = Join-Path $AppPath 'multi_broker_backend_updated.py'
$logDir = Join-Path $AppPath 'logs'
$stdoutLog = Join-Path $logDir 'backend_stdout.log'
$stderrLog = Join-Path $logDir 'backend_stderr.log'
$supervisorLog = Join-Path $logDir 'backend_supervisor.log'

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

Write-Host "Starting backend supervisor on port $Port..." -ForegroundColor Cyan
Write-Host "Supervisor log: $supervisorLog" -ForegroundColor Yellow
Write-Host "Stdout log: $stdoutLog" -ForegroundColor Yellow
Write-Host "Stderr log: $stderrLog" -ForegroundColor Yellow

while ($true) {
    # Avoid duplicate backend launches when this script is triggered repeatedly.
    $existing = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object {
            $_.Name -match '^python(\.exe)?$' -and
            $_.CommandLine -like "*$backendPath*"
        } |
        Select-Object -First 1

    if ($existing) {
        $msg = "$(Get-Date -Format o) [SUPERVISOR] Backend already running (PID=$($existing.ProcessId)); exiting supervisor instance."
        $msg | Add-Content -Path $supervisorLog
        Write-Host $msg -ForegroundColor Yellow
        exit 0
    }

    $startMsg = "$(Get-Date -Format o) [SUPERVISOR] Launching backend"
    $startMsg | Add-Content -Path $supervisorLog
    Write-Host $startMsg -ForegroundColor Cyan

    $process = Start-Process -FilePath $pythonPath -ArgumentList $backendPath -WorkingDirectory $AppPath -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog -PassThru
    $launchMsg = "$(Get-Date -Format o) [SUPERVISOR] Backend PID=$($process.Id)"
    $launchMsg | Add-Content -Path $supervisorLog
    Write-Host $launchMsg -ForegroundColor Green

    Wait-Process -Id $process.Id
    $exitCode = $process.ExitCode
    $exitMsg = "$(Get-Date -Format o) [SUPERVISOR] Backend exited (code=$exitCode). Restarting in $RestartDelaySeconds s..."
    $exitMsg | Add-Content -Path $supervisorLog
    Write-Host $exitMsg -ForegroundColor Red

    Start-Sleep -Seconds $RestartDelaySeconds
}

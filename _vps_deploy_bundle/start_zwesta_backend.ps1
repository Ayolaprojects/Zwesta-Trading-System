$ErrorActionPreference = 'Stop'

$backendDir = 'C:\backend'
$backendUrl = 'http://127.0.0.1:9000'
$healthUrl = "$backendUrl/api/health"
$watchdogScript = Join-Path $backendDir 'watchdog.py'
$watchdogLauncher = Join-Path $backendDir 'start_watchdog.bat'
$pythonExe = 'c:\zwesta-trader\.venv\Scripts\python.exe'
$serviceNames = @('postgresql-x64-18', 'postgresql-x64-17')

function Get-PostgresService {
    $services = Get-Service -Name $serviceNames -ErrorAction SilentlyContinue
    if (-not $services) {
        return $null
    }

    $runningService = $services | Where-Object { $_.Status -eq 'Running' } | Select-Object -First 1
    if ($runningService) {
        return $runningService
    }

    foreach ($serviceName in $serviceNames) {
        $service = $services | Where-Object { $_.Name -eq $serviceName } | Select-Object -First 1
        if ($service) {
            return $service
        }
    }

    return $services | Select-Object -First 1
}

function Ensure-PostgresRunning {
    $service = Get-PostgresService
    if (-not $service) {
        throw 'No PostgreSQL Windows service found.'
    }

    if ($service.Status -ne 'Running') {
        Write-Host "Starting PostgreSQL service: $($service.Name)" -ForegroundColor Cyan
        Start-Service -Name $service.Name
        $service.WaitForStatus('Running', [TimeSpan]::FromSeconds(15))
    }

    Write-Host "PostgreSQL ready: $($service.Name)" -ForegroundColor Green
}

function Test-BackendHealthy {
    try {
        $response = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 5
        return $response.status -eq 'ok'
    } catch {
        return $false
    }
}

function Get-WatchdogProcess {
    return Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object {
            $_.Name -match '^python(w)?\.exe$' -and
            $_.CommandLine -like '*C:\backend\watchdog.py*'
        } |
        Select-Object -First 1
}

Set-Location $backendDir

Ensure-PostgresRunning

if (Test-BackendHealthy) {
    Write-Host 'Backend already healthy on http://127.0.0.1:9000' -ForegroundColor Green
    exit 0
}

$watchdogProcess = Get-WatchdogProcess
if ($watchdogProcess) {
    Write-Host "Watchdog already running (PID $($watchdogProcess.ProcessId)). Waiting for backend health..." -ForegroundColor Yellow
} else {
    if (-not (Test-Path $watchdogScript)) {
        throw "Missing watchdog script: $watchdogScript"
    }
    if (-not (Test-Path $watchdogLauncher)) {
        throw "Missing watchdog launcher: $watchdogLauncher"
    }
    if (-not (Test-Path $pythonExe)) {
        throw "Missing Python executable: $pythonExe"
    }

    Write-Host 'Starting Zwesta backend stack...' -ForegroundColor Cyan
    Start-Process -FilePath $watchdogLauncher -WorkingDirectory $backendDir -WindowStyle Minimized | Out-Null
}

for ($attempt = 1; $attempt -le 20; $attempt++) {
    if (Test-BackendHealthy) {
        Write-Host 'Backend healthy on http://127.0.0.1:9000' -ForegroundColor Green
        exit 0
    }
    Start-Sleep -Seconds 3
}

throw 'Backend did not become healthy within 60 seconds.'
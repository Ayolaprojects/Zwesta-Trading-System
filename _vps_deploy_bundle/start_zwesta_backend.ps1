$ErrorActionPreference = 'Stop'

$backendDir = 'C:\backend'
$backendUrl = 'http://127.0.0.1:9000'
$healthUrl = "$backendUrl/api/health"
$watchdogScript = Join-Path $backendDir 'watchdog.py'
$watchdogLauncher = Join-Path $backendDir 'start_watchdog.bat'
$serviceNames = @('postgresql-x64-18', 'postgresql-x64-17')

function Resolve-PythonExecutable {
    $candidates = @(
        'c:\zwesta-trader\.venv\Scripts\python.exe',
        'C:\Program Files\Python311\python.exe',
        'C:\Python312\python.exe',
        'C:\Python311\python.exe',
        'C:\Python310\python.exe',
        'C:\Python39\python.exe'
    )

    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path $candidate)) {
            return $candidate
        }
    }

    foreach ($commandName in @('python', 'py')) {
        try {
            $command = Get-Command $commandName -ErrorAction Stop | Select-Object -First 1
            if ($command -and $command.Source) {
                return $command.Source
            }
        } catch {
        }
    }

    return $null
}

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

function Get-BackendProcesses {
    return @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object {
            $_.Name -match '^python(w)?\.exe$' -and
            $_.CommandLine -like '*C:\backend\multi_broker_backend_updated.py*'
        })
}

Set-Location $backendDir

Ensure-PostgresRunning

$backendProcesses = Get-BackendProcesses
if ($backendProcesses.Count -gt 1) {
    $duplicateIds = ($backendProcesses | Select-Object -ExpandProperty ProcessId) -join ', '
    Write-Host "Duplicate backend processes detected ($duplicateIds). Stopping them before restart..." -ForegroundColor Yellow
    foreach ($proc in $backendProcesses) {
        try {
            Stop-Process -Id $proc.ProcessId -Force -ErrorAction Stop
        } catch {
            Write-Warning "Could not stop backend PID $($proc.ProcessId): $($_.Exception.Message)"
        }
    }
    Start-Sleep -Seconds 2
}

if (Test-BackendHealthy) {
    Write-Host 'Backend already healthy on http://127.0.0.1:9000' -ForegroundColor Green
    exit 0
}

$watchdogProcess = Get-WatchdogProcess
if ($watchdogProcess) {
    Write-Host "Watchdog already running (PID $($watchdogProcess.ProcessId)). Waiting for backend health..." -ForegroundColor Yellow
} else {
    $pythonExe = Resolve-PythonExecutable
    if (-not (Test-Path $watchdogScript)) {
        throw "Missing watchdog script: $watchdogScript"
    }
    if (-not (Test-Path $watchdogLauncher)) {
        throw "Missing watchdog launcher: $watchdogLauncher"
    }
    if (-not $pythonExe) {
        throw 'Missing Python executable: no supported Python interpreter was found on this machine.'
    }

    Write-Host "Using Python: $pythonExe" -ForegroundColor Cyan
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
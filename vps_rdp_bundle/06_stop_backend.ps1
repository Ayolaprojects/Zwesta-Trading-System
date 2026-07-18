param(
    [string]$Match = 'multi_broker_backend_updated.py'
)

$ErrorActionPreference = 'Stop'

$procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*$Match*" }
if (-not $procs) {
    Write-Host "No backend process found matching: $Match" -ForegroundColor Yellow
    exit 0
}

foreach ($p in $procs) {
    try {
        Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop
        Write-Host "Stopped PID $($p.ProcessId)" -ForegroundColor Green
    }
    catch {
        Write-Host "Failed to stop PID $($p.ProcessId): $($_.Exception.Message)" -ForegroundColor Red
    }
}

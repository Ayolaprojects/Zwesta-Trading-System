param(
    [string]$AppPath = 'C:\zwesta-app',
    [string]$TaskName = 'ZwestaBackend',
    [int]$Port = 9000
)

$ErrorActionPreference = 'Stop'

$scriptPath = Join-Path $AppPath 'vps_rdp_bundle\03_start_backend.ps1'
if (-not (Test-Path -LiteralPath $scriptPath)) {
    throw "Start script not found: $scriptPath"
}

$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`" -AppPath `"$AppPath`" -Port $Port"
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 12) -MultipleInstances IgnoreNew

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null

Write-Host "Scheduled task '$TaskName' registered." -ForegroundColor Green
Write-Host "Run now with: Start-ScheduledTask -TaskName $TaskName" -ForegroundColor Yellow

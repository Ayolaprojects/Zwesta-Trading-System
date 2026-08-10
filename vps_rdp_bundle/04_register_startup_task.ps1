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

# Also register the Exness MT5 terminal keep-alive supervisor so the backend can
# read live Exness positions via the MT5 IPC channel.
$terminalScript = Join-Path $AppPath 'vps_rdp_bundle\07_start_exness_terminals.ps1'
if (Test-Path -LiteralPath $terminalScript) {
    $terminalAction = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$terminalScript`" -AppPath `"$AppPath`""
    Register-ScheduledTask -TaskName 'ZwestaExnessTerminals' -Action $terminalAction -Trigger (New-ScheduledTaskTrigger -AtStartup) -Principal $principal -Settings $settings -Force | Out-Null
    Write-Host "Scheduled task 'ZwestaExnessTerminals' registered." -ForegroundColor Green
}
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Seconds 0) -MultipleInstances IgnoreNew

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null

Write-Host "Scheduled task '$TaskName' registered." -ForegroundColor Green
Write-Host "Run now with: Start-ScheduledTask -TaskName $TaskName" -ForegroundColor Yellow

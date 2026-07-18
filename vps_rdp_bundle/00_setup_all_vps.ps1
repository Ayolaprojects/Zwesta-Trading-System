param(
    [string]$AppPath = 'C:\zwesta-app',
    [string]$PythonExe = 'python',
    [string]$RequirementsFile = 'requirements-production.txt',
    [int]$Port = 9000,
    [string]$TaskName = 'ZwestaBackend',
    [switch]$StartNow
)

$ErrorActionPreference = 'Stop'

Write-Host '=== Zwesta VPS One-Click Setup ===' -ForegroundColor Cyan
Write-Host "AppPath: $AppPath"
Write-Host "Port: $Port"

if (-not (Test-Path -LiteralPath $AppPath)) {
    throw "AppPath not found: $AppPath"
}

$bundlePath = Join-Path $AppPath 'vps_rdp_bundle'
if (-not (Test-Path -LiteralPath $bundlePath)) {
    throw "vps_rdp_bundle not found in $AppPath"
}

Set-Location -LiteralPath $AppPath

$steps = @(
    @{ Name = 'Install PostgreSQL'; Script = '.\vps_rdp_bundle\01_install_postgresql.ps1'; Args = @() },
    @{ Name = 'Install dependencies'; Script = '.\vps_rdp_bundle\01_install_dependencies.ps1'; Args = @('-AppPath', $AppPath, '-PythonExe', $PythonExe, '-RequirementsFile', $RequirementsFile) },
    @{ Name = 'Prepare .env'; Script = '.\vps_rdp_bundle\02_prepare_env.ps1'; Args = @('-AppPath', $AppPath) },
    @{ Name = 'Open firewall'; Script = '.\vps_rdp_bundle\05_open_firewall_port.ps1'; Args = @('-Port', "$Port", '-RuleName', 'Zwesta Backend API') },
    @{ Name = 'Register startup task'; Script = '.\vps_rdp_bundle\04_register_startup_task.ps1'; Args = @('-AppPath', $AppPath, '-TaskName', $TaskName, '-Port', "$Port") }
)

foreach ($step in $steps) {
    Write-Host "`n>> $($step.Name)" -ForegroundColor Yellow
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $step.Script @($step.Args)
    if ($LASTEXITCODE -ne 0) {
        throw "$($step.Name) failed with exit code $LASTEXITCODE"
    }
}

Write-Host "`n=== Setup Complete ===" -ForegroundColor Green
Write-Host 'IMPORTANT: Edit your .env and replace placeholders before production use.' -ForegroundColor Yellow
Write-Host "Env file: $AppPath\.env"
Write-Host "Startup task: $TaskName"

if ($StartNow) {
    Write-Host "`nStarting task now..." -ForegroundColor Cyan
    Start-ScheduledTask -TaskName $TaskName
    Write-Host 'Startup task triggered.' -ForegroundColor Green
}
else {
    Write-Host "`nTo start now, run:" -ForegroundColor Cyan
    Write-Host "Start-ScheduledTask -TaskName '$TaskName'"
}

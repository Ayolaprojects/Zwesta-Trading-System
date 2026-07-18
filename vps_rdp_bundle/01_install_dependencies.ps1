param(
    [string]$AppPath = 'C:\zwesta-app',
    [string]$PythonExe = 'python',
    [string]$RequirementsFile = 'requirements-production.txt'
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $AppPath)) {
    throw "AppPath not found: $AppPath"
}

Set-Location -LiteralPath $AppPath

Write-Host "[1/4] Creating virtual environment..." -ForegroundColor Cyan
& $PythonExe -m venv venv

Write-Host "[2/4] Upgrading pip..." -ForegroundColor Cyan
& ".\venv\Scripts\python.exe" -m pip install --upgrade pip

if (-not (Test-Path -LiteralPath $RequirementsFile)) {
    throw "Requirements file not found: $RequirementsFile"
}

$requirementsText = Get-Content -LiteralPath $RequirementsFile -Raw
if ($requirementsText -match 'PyJWT==2\.8\.1') {
    Write-Host 'Updating stale PyJWT pin in requirements file to 2.13.0...' -ForegroundColor Yellow
    $requirementsText = $requirementsText -replace 'PyJWT==2\.8\.1', 'PyJWT==2.13.0'
    Set-Content -LiteralPath $RequirementsFile -Value $requirementsText -NoNewline
}

Write-Host "[3/4] Installing dependencies from $RequirementsFile..." -ForegroundColor Cyan
& ".\venv\Scripts\pip.exe" install -r $RequirementsFile

Write-Host "[4/4] Dependency install complete." -ForegroundColor Green
Write-Host "Next: run 02_prepare_env.ps1" -ForegroundColor Yellow

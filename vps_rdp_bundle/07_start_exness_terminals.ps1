param(
    [string]$AppPath = 'C:\zwesta-app',
    [int]$RestartDelaySeconds = 15
)

$ErrorActionPreference = 'Stop'

# Resolve terminal executable paths from environment (set in .env / system env).
# Order of preference: EXNESS_LIVE_PATH, EXNESS_DEMO_PATH, EXNESS_PATH, then the
# historical default install location.
$EnvFile = Join-Path $AppPath '.env'
$envVars = @{}
if (Test-Path -LiteralPath $EnvFile) {
    foreach ($line in (Get-Content -LiteralPath $EnvFile)) {
        if ($line -match '^\s*([A-Za-z0-9_]+)\s*=\s*(.*)\s*$') {
            $envVars[$Matches[1]] = $Matches[2].Trim('"').Trim("'")
        }
    }
}

$candidatePaths = @(
    $envVars['EXNESS_LIVE_PATH'],
    $envVars['EXNESS_DEMO_PATH'],
    $envVars['EXNESS_PATH'],
    'C:\MT5\Exness-Live\terminal64.exe',
    'C:\MT5\Exness-Demo\terminal64.exe',
    'C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe'
) | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique

if (-not $candidatePaths) {
    Write-Host '[EXNESS-TERMINAL] No Exness MT5 terminal executable found on disk. Skipping.' -ForegroundColor Yellow
    exit 0
}

Write-Host "[EXNESS-TERMINAL] Keeping alive: $($candidatePaths -join ', ')" -ForegroundColor Cyan

function Get-RunningTerminal ($path) {
    $name = [System.IO.Path]::GetFileName($path)
    return Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -eq $name -and $_.ExecutablePath -and $_.ExecutablePath.Replace('/', '\') -eq $path.Replace('/', '\') } |
        Select-Object -First 1
}

while ($true) {
    foreach ($termPath in $candidatePaths) {
        $existing = Get-RunningTerminal $termPath
        if (-not $existing) {
            try {
                Write-Host "[EXNESS-TERMINAL] Launching $termPath" -ForegroundColor Green
                Start-Process -FilePath $termPath -WorkingDirectory (Split-Path -Parent $termPath) -PassThru | Out-Null
            } catch {
                Write-Host "[EXNESS-TERMINAL] Failed to launch ${termPath}: $_" -ForegroundColor Red
            }
        }
    }
    Start-Sleep -Seconds $RestartDelaySeconds
}

param(
    [string]$AppPath = 'C:\zwesta-app',
    [string]$TemplatePath = '.\vps_rdp_bundle\env.vps.template',
    [string]$TargetEnvPath = '.\.env'
)

$ErrorActionPreference = 'Stop'

Set-Location -LiteralPath $AppPath

function Get-EnvKeySet {
    param([string]$Path)

    $keys = @{}
    if (-not (Test-Path -LiteralPath $Path)) {
        return $keys
    }

    foreach ($line in Get-Content -LiteralPath $Path) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith('#') -or $trimmed -notmatch '^[A-Za-z_][A-Za-z0-9_]*=') {
            continue
        }

        $key = $trimmed.Split('=', 2)[0]
        $keys[$key] = $true
    }

    return $keys
}

function Add-EnvSectionIfMissing {
    param(
        [string]$TargetPath,
        [string[]]$Lines,
        [hashtable]$ExistingKeys
    )

    $missingLines = New-Object System.Collections.Generic.List[string]
    foreach ($line in $Lines) {
        $trimmed = $line.Trim()
        if ($trimmed -match '^[A-Za-z_][A-Za-z0-9_]*=') {
            $key = $trimmed.Split('=', 2)[0]
            if (-not $ExistingKeys.ContainsKey($key)) {
                $missingLines.Add($line)
            }
        }
        elseif ($missingLines.Count -gt 0 -or $line.StartsWith('# ====================')) {
            $missingLines.Add($line)
        }
    }

    if ($missingLines.Count -gt 0) {
        Add-Content -LiteralPath $TargetPath -Value ""
        Add-Content -LiteralPath $TargetPath -Value ($missingLines -join "`r`n")
        return $true
    }

    return $false
}

if (Test-Path -LiteralPath $TargetEnvPath) {
    Write-Host ".env already exists at $TargetEnvPath" -ForegroundColor Yellow
    $existingKeys = Get-EnvKeySet -Path $TargetEnvPath
    $templateLines = Get-Content -LiteralPath $TemplatePath
    $merged = Add-EnvSectionIfMissing -TargetPath $TargetEnvPath -Lines $templateLines -ExistingKeys $existingKeys
    if ($merged) {
        Write-Host "Merged missing broker/runtime settings into existing .env" -ForegroundColor Green
    }
    else {
        Write-Host "Existing .env already contains the required broker/runtime settings." -ForegroundColor Green
    }
    Write-Host "Edit it manually if needed." -ForegroundColor Yellow
    exit 0
}

if (-not (Test-Path -LiteralPath $TemplatePath)) {
    throw "Template not found: $TemplatePath"
}

Copy-Item -LiteralPath $TemplatePath -Destination $TargetEnvPath -Force
Write-Host "Created .env from template: $TargetEnvPath" -ForegroundColor Green
Write-Host "IMPORTANT: Open .env and fill in real secrets and DB URL before starting." -ForegroundColor Yellow

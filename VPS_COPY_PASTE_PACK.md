# VPS Copy/Paste Pack

Use these files on `C:\zwesta-app` in this order.

## 1) Replace `C:\zwesta-app\.env`

Paste these VPS values into the PostgreSQL block and keep the rest of your VPS config the same:

```dotenv
TRADING_ENV=LIVE
ENVIRONMENT=LIVE
DEPLOYMENT_MODE=VPS

POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_DB=zwesta_trading_vps
POSTGRES_USER=zwesta_admin
POSTGRES_PASSWORD=ZwestaDB_2026!
DATABASE_URL=postgresql://zwesta_admin:ZwestaDB_2026!@127.0.0.1:5432/zwesta_trading_vps
API_KEY=zwesta_live_api_key_2026_secure
```

## 2) Replace `C:\zwesta-app\vps_rdp_bundle\01_install_postgresql.ps1`

This version detects PostgreSQL 18 under `C:\Program Files\PostgreSQL\18\bin`.

```powershell
param(
    [string]$Version = '16.3',
    [string]$InstallDir = 'C:\Program Files\PostgreSQL\16',
    [int]$Port = 5432,
    [string]$SuperUser = 'postgres',
    [string]$SuperPassword = 'ZwestaPostgres123!'
)

$ErrorActionPreference = 'Stop'

function Test-CommandExists {
    param([string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Get-PostgresPsqlPath {
    param([string]$PreferredInstallDir)

    $candidatePaths = @()

    if ($PreferredInstallDir) {
        $candidatePaths += (Join-Path $PreferredInstallDir 'bin\psql.exe')
    }

    $candidatePaths += @(
        'C:\Program Files\PostgreSQL\18\bin\psql.exe',
        'C:\Program Files\PostgreSQL\18.0\bin\psql.exe',
        'C:\Program Files\PostgreSQL\18.1\bin\psql.exe',
        'C:\Program Files\PostgreSQL\16\bin\psql.exe',
        'C:\Program Files\PostgreSQL\16.3\bin\psql.exe',
        'C:\Program Files\PostgreSQL\16.0\bin\psql.exe',
        'C:\Program Files\PostgreSQL\15\bin\psql.exe',
        'C:\Program Files (x86)\PostgreSQL\16\bin\psql.exe'
    )

    foreach ($candidate in $candidatePaths) {
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }

    $found = Get-ChildItem -Path 'C:\Program Files\PostgreSQL', 'C:\Program Files (x86)\PostgreSQL' -Filter psql.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) {
        return $found.FullName
    }

    return $null
}

if (Test-CommandExists 'psql') {
    Write-Host 'PostgreSQL client tools already available on PATH.' -ForegroundColor Green
    exit 0
}

$existingPsqlPath = Get-PostgresPsqlPath -PreferredInstallDir $InstallDir
if ($existingPsqlPath) {
    Write-Host 'Detected existing PostgreSQL installation. Skipping installer.' -ForegroundColor Green
    Write-Host "psql path: $existingPsqlPath"
    exit 0
}

$installerUrl = "https://get.enterprisedb.com/postgresql/postgresql-$Version-1-windows-x64.exe"
$installerPath = Join-Path $env:TEMP "postgresql-$Version-installer.exe"
$minInstallerBytes = 50MB

function Download-FileWithRetry {
    param(
        [string]$Url,
        [string]$Path,
        [int]$MaxAttempts = 3
    )

    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        try {
            if (Test-Path -LiteralPath $Path) {
                Remove-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
            }

            Write-Host "Download attempt $attempt/$MaxAttempts..." -ForegroundColor DarkCyan
            Invoke-WebRequest -Uri $Url -OutFile $Path -UseBasicParsing

            if (-not (Test-Path -LiteralPath $Path)) {
                throw "Installer file was not created."
            }

            $sizeBytes = (Get-Item -LiteralPath $Path).Length
            if ($sizeBytes -lt $minInstallerBytes) {
                throw "Downloaded file is too small ($sizeBytes bytes)."
            }

            return
        }
        catch {
            if ($attempt -eq $MaxAttempts) {
                throw
            }
            Write-Host "Download failed: $($_.Exception.Message)" -ForegroundColor Yellow
            Write-Host 'Retrying download...' -ForegroundColor Yellow
        }
    }
}

Write-Host "Downloading PostgreSQL $Version installer..." -ForegroundColor Cyan
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Download-FileWithRetry -Url $installerUrl -Path $installerPath -MaxAttempts 3

$installerSize = (Get-Item -LiteralPath $installerPath).Length
Write-Host "Installer download complete ($installerSize bytes)." -ForegroundColor Green

Write-Host 'Installing PostgreSQL silently...' -ForegroundColor Cyan
$arguments = @(
    '--mode', 'unattended',
    '--unattendedmodeui', 'minimal',
    '--superpassword', $SuperPassword,
    '--servicename', 'postgresql-x64-16',
    '--serviceaccount', 'NT AUTHORITY\NetworkService',
    '--serverport', $Port,
    '--datadir', "$InstallDir\data",
    '--prefix', $InstallDir
)

Write-Host "Installer path: $installerPath" -ForegroundColor DarkGray
$process = Start-Process -FilePath $installerPath -ArgumentList $arguments -Wait -PassThru
if ($process.ExitCode -ne 0) {
    throw "PostgreSQL installer exited with code $($process.ExitCode)"
}

$psqlPath = Get-PostgresPsqlPath -PreferredInstallDir $InstallDir
if (-not $psqlPath) {
    throw "psql.exe not found after install. Checked common PostgreSQL locations under Program Files."
}

Write-Host 'PostgreSQL installed successfully.' -ForegroundColor Green
Write-Host "psql path: $psqlPath"
```

## 3) Replace `C:\zwesta-app\vps_rdp_bundle\README_RDP_VPS_SETUP.md`

Keep the new VPS reset section that says:

- use `POSTGRES_HOST=127.0.0.1`
- use `POSTGRES_DB=zwesta_trading_vps`
- use `POSTGRES_USER=zwesta_admin`
- use `POSTGRES_PASSWORD=ZwestaDB_2026!`
- run `02_prepare_env.ps1`
- drop and recreate the database if the password is lost

## 4) Apply on the VPS

After copying files, run:

```powershell
cd C:\zwesta-app
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\vps_rdp_bundle\00_setup_all_vps.ps1 -AppPath "C:\zwesta-app" -PythonExe "python" -RequirementsFile "requirements-production.txt" -Port 9000 -TaskName "ZwestaBackend" -StartNow
```

If the password is lost and you want a clean reset, recreate the database with the values above, then restart the scheduled task.

Use this exact sequence on the VPS:

```powershell
$env:PGPASSWORD = 'ZwestaPostgres123!'
& 'C:\Program Files\PostgreSQL\18\bin\psql.exe' -h 127.0.0.1 -U postgres -p 5432 -d postgres -c "ALTER USER zwesta_admin WITH PASSWORD 'ZwestaDB_2026!';"
& 'C:\Program Files\PostgreSQL\18\bin\psql.exe' -h 127.0.0.1 -U postgres -p 5432 -d postgres -c "DROP DATABASE IF EXISTS zwesta_trading_vps;"
& 'C:\Program Files\PostgreSQL\18\bin\psql.exe' -h 127.0.0.1 -U postgres -p 5432 -d postgres -c "CREATE DATABASE zwesta_trading_vps OWNER zwesta_admin;"
Remove-Item Env:PGPASSWORD
```

If your PostgreSQL 18 install is in a different folder, update the `psql.exe` path to match your VPS.
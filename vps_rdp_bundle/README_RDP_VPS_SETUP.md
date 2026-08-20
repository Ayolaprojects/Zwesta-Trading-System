# Zwesta VPS RDP Deployment Bundle

Use these scripts on your Windows VPS after you copy the project to `C:\\zwesta-app`.

## One-click setup (new)
Run this single command in elevated PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
cd C:\zwesta-app
.\vps_rdp_bundle\00_setup_all_vps.ps1 -AppPath "C:\zwesta-app" -PythonExe "python" -RequirementsFile "requirements-production.txt" -Port 9000 -TaskName "ZwestaBackend" -StartNow
```

This will:
- install PostgreSQL locally on the VPS
- install dependencies
- create `.env` from template if missing
- open firewall port
- register startup task
- start the backend task immediately (when `-StartNow` is set)

If you copied the project to the VPS before these bundle updates, copy the updated `vps_rdp_bundle` folder and `requirements-production.txt` again before rerunning setup.

## 0) Recommended security first
1. Rotate your VPS password immediately.
2. Restrict RDP by IP if possible.
3. Use a separate database for VPS.

## 1) Copy project to VPS
- Target path: `C:\\zwesta-app`
- Make sure this folder contains:
  - `multi_broker_backend_updated.py`
  - `requirements-production.txt`
  - `vps_rdp_bundle` folder

## 2) Install dependencies
Run in elevated PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
cd C:\zwesta-app
.\vps_rdp_bundle\01_install_dependencies.ps1 -AppPath "C:\zwesta-app" -PythonExe "python" -RequirementsFile "requirements-production.txt"
```

## 3) Prepare .env
```powershell
cd C:\zwesta-app
.\vps_rdp_bundle\02_prepare_env.ps1 -AppPath "C:\zwesta-app"
notepad .env
```

Fill all required secrets and database values.

For Binance live profitability protection, set these in `.env` (already present in `env.vps.template`):
- `BINANCE_SPOT_FEE_RATE=0.001`
- `BINANCE_SPOT_MIN_NET_EXIT_PCT=0.12`
- `BINANCE_SPOT_MIN_NET_EXIT_AMOUNT=1.5`
- `BINANCE_SPOT_MIN_HOLD_MINUTES=5`
- `BINANCE_SPOT_ALLOW_LOSS_EXIT=false`

These settings help prevent closing trades where fees consume the edge.

PostgreSQL is installed automatically by the one-click setup. The default local superuser password in the script is `ZwestaPostgres123!` unless you change it.

The production requirements file now uses a PyJWT version that is available on PyPI for Python 3.12.

### VPS database reset when the password is lost

If you do not remember the VPS PostgreSQL password and you are fine clearing the database, use the fresh VPS profile values below and recreate the database on the server:

```text
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_DB=zwesta_trading_vps
POSTGRES_USER=zwesta_admin
POSTGRES_PASSWORD=ZwestaDB_2026!
```

Run these steps on the VPS:

```powershell
cd C:\zwesta-app
.\vps_rdp_bundle\02_prepare_env.ps1 -AppPath "C:\zwesta-app"
notepad .env
```

In PostgreSQL, drop and recreate the app database, then set the user password to `ZwestaDB_2026!`.

If you prefer a clean start, delete the existing app database before recreation and then restart the backend task after updating `.env`.

Use this exact sequence in an elevated PowerShell window on the VPS:

```powershell
$env:PGPASSWORD = 'ZwestaPostgres123!'
& 'C:\Program Files\PostgreSQL\18\bin\psql.exe' -h 127.0.0.1 -U postgres -p 5432 -d postgres -c "ALTER USER zwesta_admin WITH PASSWORD 'ZwestaDB_2026!';"
& 'C:\Program Files\PostgreSQL\18\bin\psql.exe' -h 127.0.0.1 -U postgres -p 5432 -d postgres -c "DROP DATABASE IF EXISTS zwesta_trading_vps;"
& 'C:\Program Files\PostgreSQL\18\bin\psql.exe' -h 127.0.0.1 -U postgres -p 5432 -d postgres -c "CREATE DATABASE zwesta_trading_vps OWNER zwesta_admin;"
Remove-Item Env:PGPASSWORD
```

If your PostgreSQL 18 install is under a different folder, replace the `C:\Program Files\PostgreSQL\18\bin\psql.exe` path with the actual `psql.exe` path on the VPS.

## 4) Start backend manually (first run)
```powershell
cd C:\zwesta-app
.\vps_rdp_bundle\03_start_backend.ps1 -AppPath "C:\zwesta-app" -Port 9000
```

Notes:
- `03_start_backend.ps1` now runs a lightweight supervisor loop. If Python exits/crashes, it auto-restarts after a short delay.
- Supervisor lifecycle log: `C:\zwesta-app\logs\backend_supervisor.log`
- Backend stdout/stderr logs:
  - `C:\zwesta-app\logs\backend_stdout.log`
  - `C:\zwesta-app\logs\backend_stderr.log`

## 5) Open firewall port (if needed)
```powershell
.\vps_rdp_bundle\05_open_firewall_port.ps1 -Port 9000 -RuleName "Zwesta Backend API"
```

## 6) Register startup task
```powershell
.\vps_rdp_bundle\04_register_startup_task.ps1 -AppPath "C:\zwesta-app" -TaskName "ZwestaBackend" -Port 9000
Start-ScheduledTask -TaskName "ZwestaBackend"
```

Task behavior:
- Startup task is configured with no execution time limit so it is not force-stopped after 12 hours.

## 7) Stop backend manually
```powershell
.\vps_rdp_bundle\06_stop_backend.ps1
```

## Notes
- This deployment is separate from your local machine.
- Keep `.env` on VPS different from local.
- Keep VPS DB separate from local DB to avoid collisions.

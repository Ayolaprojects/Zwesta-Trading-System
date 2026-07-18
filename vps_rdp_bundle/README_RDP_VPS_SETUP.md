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

## 4) Start backend manually (first run)
```powershell
cd C:\zwesta-app
.\vps_rdp_bundle\03_start_backend.ps1 -AppPath "C:\zwesta-app" -Port 9000
```

## 5) Open firewall port (if needed)
```powershell
.\vps_rdp_bundle\05_open_firewall_port.ps1 -Port 9000 -RuleName "Zwesta Backend API"
```

## 6) Register startup task
```powershell
.\vps_rdp_bundle\04_register_startup_task.ps1 -AppPath "C:\zwesta-app" -TaskName "ZwestaBackend" -Port 9000
Start-ScheduledTask -TaskName "ZwestaBackend"
```

## 7) Stop backend manually
```powershell
.\vps_rdp_bundle\06_stop_backend.ps1
```

## Notes
- This deployment is separate from your local machine.
- Keep `.env` on VPS different from local.
- Keep VPS DB separate from local DB to avoid collisions.

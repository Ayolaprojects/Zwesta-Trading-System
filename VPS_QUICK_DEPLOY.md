# VPS DEPLOYMENT - QUICK COPY LIST

## WHAT TO COPY TO VPS

### CORE BACKEND (Required)
```
_vps_deploy_bundle/
├── multi_broker_backend_updated.py    ← MAIN SERVER (1.8 MB)
├── binance_service.py                 ← Binance Bot Handler
├── runtime_infrastructure.py           ← Database Connection Manager
├── postgres_schema.py                  ← PostgreSQL Schema
├── fxcm_service.py                    ← FXCM Integration (optional)
├── .env                               ← Configuration File (EDIT THIS)
├── multi_broker_backend_updated.bat   ← Batch Launcher
└── start_zwesta_backend.ps1           ← PowerShell Launcher
```

### MANAGEMENT TOOLS
```
c:\zwesta-trader\
├── _diagnose_postgres_bots.py         ← Check Bot Status
├── _verify_bot_creation_system.py     ← Verify Bot System
├── _verify_user_registration.py       ← Verify User System
├── _auto_cleanup_disabled_bots.py     ← Clean Disabled Bots
├── FINAL_VERIFICATION.py              ← System Health Check
└── _enable_exness_bots.py             ← Enable Exness Bots
```

### DEPENDENCIES
```
c:\zwesta-trader\
└── requirements.txt                    ← Python Packages
```

---

## FILE SIZE SUMMARY
- **Backend Server**: 1.8 MB
- **Supporting Services**: 250 KB
- **Config + Schema**: 20 KB
- **Management Tools**: 26 KB
- **Requirements**: 1 KB
- **TOTAL**: ~2.1 MB

---

## INSTALLATION COMMAND (One-liner)

```bash
# Copy all backend files
scp -r /local/path/_vps_deploy_bundle/* vps_user@your.vps.ip:/vps/backend/

# Copy tools
scp /local/path/_diagnose_postgres_bots.py vps_user@your.vps.ip:/vps/tools/
scp /local/path/_verify_bot_creation_system.py vps_user@your.vps.ip:/vps/tools/
scp /local/path/_verify_user_registration.py vps_user@your.vps.ip:/vps/tools/
scp /local/path/_auto_cleanup_disabled_bots.py vps_user@your.vps.ip:/vps/tools/
scp /local/path/FINAL_VERIFICATION.py vps_user@your.vps.ip:/vps/tools/
scp /local/path/_enable_exness_bots.py vps_user@your.vps.ip:/vps/tools/

# Copy requirements
scp /local/path/requirements.txt vps_user@your.vps.ip:/vps/backend/
```

---

## INSTALLATION STEPS (5 Minutes)

```bash
# 1. Connect to VPS
ssh user@your.vps.ip

# 2. Navigate to backend directory
cd /vps/backend

# 3. Install Python packages
pip install -r requirements.txt

# 4. EDIT .env file with VPS settings
nano .env
# Change:
# - DB_HOST (if not localhost)
# - DB_PASSWORD (strong password)
# - API_HOST=0.0.0.0 (for external access)

# 5. Start backend server
python multi_broker_backend_updated.py
# OR with nohup (background)
nohup python multi_broker_backend_updated.py > api.log 2>&1 &
```

---

## VERIFY DEPLOYMENT (2 Minutes)

```bash
# Check if API is responding
curl http://your.vps.ip:9000/api/health

# Verify bots
cd /vps/tools && python FINAL_VERIFICATION.py

# Check system
python _verify_bot_creation_system.py
```

---

## WHAT HAPPENS AFTER STARTUP

1. ✓ API server listens on port 9000
2. ✓ Bots start trading if enabled
3. ✓ Database auto-initializes
4. ✓ Logs written to `api.log` and `bot_trades.log`
5. ✓ Ready to accept users and bot creation requests

---

## IMPORTANT ENV VARIABLES TO SET

```
# Minimum required
DB_HOST=localhost
DB_USER=zwesta_admin
DB_PASSWORD=YourPassword123
DB_NAME=zwesta_trading

# For external connections
API_HOST=0.0.0.0
API_PORT=9000

# For Exness bots (if on Linux, adjust paths)
EXNESS_LIVE_PATH=/path/to/MT5/terminal64.exe
EXNESS_ACCOUNT=295677214
EXNESS_SERVER=Exness-MT5Real27
```

---

## WINDOWS VPS DEPLOYMENT

If using Windows Server:

```powershell
# 1. Navigate to backend
cd C:\vps\backend

# 2. Run PowerShell launcher
.\start_zwesta_backend.ps1

# 3. Or run directly
python multi_broker_backend_updated.py
```

---

## BACKUP & RESTORE

```bash
# Backup database before moving to VPS
pg_dump zwesta_trading > backup_$(date +%Y%m%d).sql

# Or copy SQLite database
cp zwesta_trading.db zwesta_trading.db.backup

# Restore on VPS
psql zwesta_trading < backup_20260605.sql
# or copy the .db file
```

---

## VPS HOSTING RECOMMENDATIONS

✓ **Good for Trading Bots**:
- DigitalOcean ($5-20/month for VPS)
- Linode ($5-30/month for VPS)
- AWS EC2 (t2.small $12/month)
- UpCloud (from $5/month)

✓ **Requirements**:
- 4 GB RAM minimum
- Always-on (not auto-shutdown)
- Stable internet
- Consistent IP (if security rules needed)

---

## READY TO DEPLOY!

All files in `_vps_deploy_bundle/` are production-tested and ready.
Just copy, configure `.env`, install packages, and run!

Questions? Check `NEW_USER_BOT_WORKFLOW.md` for complete system details.

# EXACT FILES TO COPY TO VPS

## MASTER FILE LIST FROM _vps_deploy_bundle/

### MUST COPY (Core Backend)
```
✅ multi_broker_backend_updated.py    [1.8 MB]  Main API Server
✅ binance_service.py                  [120 KB] Binance Bot Handler
✅ runtime_infrastructure.py            [45 KB]  Database Connection Manager
✅ postgres_schema.py                   [15 KB]  PostgreSQL Schema Creator
✅ fxcm_service.py                     [80 KB]  FXCM Broker Integration
```
**Subtotal: ~2.1 MB** - **CRITICAL FOR OPERATION**

---

### SHOULD COPY (Configuration & Launchers)
```
✅ .env                                [2 KB]   Environment Variables
✅ start_zwesta_backend.ps1            [8 KB]   PowerShell Launcher
✅ multi_broker_backend_updated.bat    [1 KB]   Batch Launcher
```
**Subtotal: ~11 KB** - **NEEDED FOR STARTUP**

---

### OPTIONAL (Utilities & Fixes)
```
⚠️ _optimize_vps.py                   [12 KB]  Binance Optimization
⚠️ _optimize_exness.py                 [8 KB]   Exness Optimization
⚠️ _reset_profit_staircase.py          [5 KB]   Bot State Reset
⚠️ apply_bot_fixes.ps1                [4 KB]   PowerShell Fixes
⚠️ setup_auto_restart.bat              [2 KB]   Auto-Restart Setup
⚠️ start_watchdog.bat                  [1 KB]   Watchdog Launcher
⚠️ start_zwesta.bat                    [1 KB]   Alternative Launcher
⚠️ _vps_db_recover.py                 [8 KB]   Database Recovery
⚠️ _apply_binance_bot_1779229018996_aggressive_state.py  [3 KB]
```
**Subtotal: ~44 KB** - **Helpful for maintenance**

---

### REFERENCE ONLY (Don't Copy)
```
❌ zwesta_trading.db                          SQLite Database
❌ __pycache__/                               Python Cache
❌ system/                                    System Folder
❌ BOT_FIX_RUNBOOK.md                         Documentation
❌ DEPLOY_README.txt                          Documentation
```

---

## COPY STRATEGY

### Fastest Way (Copy Everything):
```bash
# Copy the entire folder
scp -r C:\zwesta-trader\_vps_deploy_bundle\* root@vps:/vps/backend/

# Then delete unnecessary files on VPS
cd /vps/backend
rm -rf __pycache__
rm zwesta_trading.db
rm -rf system
```

### Precise Way (Copy Only What You Need):
```bash
# Copy critical files only
scp C:\zwesta-trader\_vps_deploy_bundle\multi_broker_backend_updated.py root@vps:/vps/backend/
scp C:\zwesta-trader\_vps_deploy_bundle\binance_service.py root@vps:/vps/backend/
scp C:\zwesta-trader\_vps_deploy_bundle\runtime_infrastructure.py root@vps:/vps/backend/
scp C:\zwesta-trader\_vps_deploy_bundle\postgres_schema.py root@vps:/vps/backend/
scp C:\zwesta-trader\_vps_deploy_bundle\fxcm_service.py root@vps:/vps/backend/
scp C:\zwesta-trader\_vps_deploy_bundle\.env root@vps:/vps/backend/
scp C:\zwesta-trader\_vps_deploy_bundle\start_zwesta_backend.ps1 root@vps:/vps/backend/
scp C:\zwesta-trader\requirements.txt root@vps:/vps/backend/
```

---

## FILE IMPORTANCE MATRIX

| File | Size | Importance | Notes |
|------|------|-----------|-------|
| multi_broker_backend_updated.py | 1.8 MB | 🔴 CRITICAL | Main server - must copy |
| binance_service.py | 120 KB | 🔴 CRITICAL | Binance bot handler |
| runtime_infrastructure.py | 45 KB | 🔴 CRITICAL | DB connection |
| postgres_schema.py | 15 KB | 🟠 IMPORTANT | Schema setup |
| fxcm_service.py | 80 KB | 🟠 IMPORTANT | FXCM/MT5 handler |
| .env | 2 KB | 🔴 CRITICAL | Configuration |
| start_zwesta_backend.ps1 | 8 KB | 🟠 IMPORTANT | Startup script |
| requirements.txt | 1 KB | 🔴 CRITICAL | Dependencies |
| _optimize_vps.py | 12 KB | 🟡 USEFUL | Performance optimization |
| _reset_profit_staircase.py | 5 KB | 🟡 USEFUL | Bot state fixes |

---

## MINIMUM VIABLE VPS

**Absolute minimum to run** (2.1 MB):
1. multi_broker_backend_updated.py
2. binance_service.py
3. runtime_infrastructure.py
4. postgres_schema.py
5. fxcm_service.py
6. .env
7. requirements.txt

**Can skip everything else** - system will function perfectly

---

## RECOMMENDED VPS (2.15 MB):
Add to above:
- start_zwesta_backend.ps1 (for easy startup)
- _optimize_vps.py (performance)
- _reset_profit_staircase.py (troubleshooting)

**Total: ~2.2 MB**

---

## FULL VPS (Including Tools) (~2.3 MB):

From `_vps_deploy_bundle/`:
- All MUST COPY files
- All SHOULD COPY files
- Optional optimization/fix scripts

From root directory:
- requirements.txt
- All _diagnose_*.py files
- All _verify_*.py files
- FINAL_VERIFICATION.py
- .md documentation files

**Total: ~2.3 MB + Docs**

---

## INSTALLATION CHECKLIST

After copying files:

```bash
# 1. Install packages
pip install -r requirements.txt

# 2. Edit configuration
nano .env
# Edit:
# - DB_HOST
# - DB_PASSWORD
# - API_HOST

# 3. Create database (if PostgreSQL)
python postgres_schema.py

# 4. Start server
python multi_broker_backend_updated.py

# 5. Verify (in another terminal)
curl http://vps:9000/api/health
```

---

## VPS SYSTEM READY INDICATORS

✅ Files copied  
✅ Requirements installed  
✅ .env configured  
✅ Database initialized  
✅ API server running  
✅ Port 9000 accessible  
✅ Bots auto-starting  
✅ Trades executing  

→ **System is Production Ready!**

---

## POST-DEPLOYMENT

Once on VPS, you can also copy:

From `C:\zwesta-trader\`:
- `_diagnose_postgres_bots.py` - Monitor bot status
- `_verify_bot_creation_system.py` - System health
- `FINAL_VERIFICATION.py` - Quick status check
- Documentation files (for reference)

These help you maintain and monitor the system after deployment.

---

**Size Estimate for Full VPS: ~2.5 MB code + database**

Ready to deploy? Start with `_vps_deploy_bundle/` folder! 🚀

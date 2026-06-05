# COPY THIS FOLDER TO VPS

## Location on Your Computer
```
C:\zwesta-trader\_vps_deploy_bundle\
```

## What's Inside (Everything Needed)
```
_vps_deploy_bundle/
│
├── 📄 multi_broker_backend_updated.py       [MAIN SERVER - Start this]
├── 📄 binance_service.py                    [Binance Bot Handler]
├── 📄 runtime_infrastructure.py             [Database Manager]
├── 📄 postgres_schema.py                    [Schema Creator]
├── 📄 fxcm_service.py                       [FXCM Broker]
│
├── 🔧 Configuration Files
│   ├── .env                                 [EDIT: Database credentials]
│   ├── multi_broker_backend_updated.bat     [Windows launcher]
│   └── start_zwesta_backend.ps1             [PowerShell launcher]
│
├── 📚 Documentation
│   ├── DEPLOY_README.txt
│   ├── BOT_FIX_RUNBOOK.md
│   └── ...
│
└── (No subdirectories - flat structure)
```

---

## COPY COMMAND (Windows PowerShell)
```powershell
# Copy entire folder to VPS
scp -r "C:\zwesta-trader\_vps_deploy_bundle" vps_user@your.vps.ip:/vps/backend

# Or use WinSCP/PuTTY GUI
# Source: C:\zwesta-trader\_vps_deploy_bundle
# Destination: /vps/backend
```

---

## COPY COMMAND (Windows Command Prompt)
```cmd
# Using RDP (Remote Desktop)
# Copy via clipboard or use sftp

# Using sftp client
put -r "C:\zwesta-trader\_vps_deploy_bundle\*" /vps/backend/
```

---

## COPY COMMAND (Mac/Linux)
```bash
scp -r ~/zwesta-trader/_vps_deploy_bundle/* user@vps:/vps/backend/
```

---

## THEN ALSO COPY TOOLS (From Root)

```
From: C:\zwesta-trader\
Copy these files to VPS /vps/tools/:

❗ CRITICAL:
- requirements.txt        [Must have - Python packages]

📊 Tools (optional but recommended):
- FINAL_VERIFICATION.py
- _verify_bot_creation_system.py
- _verify_user_registration.py
- _diagnose_postgres_bots.py
- _auto_cleanup_disabled_bots.py
- _enable_exness_bots.py

📝 Docs (for reference):
- NEW_USER_BOT_WORKFLOW.md
- VPS_DEPLOYMENT_CHECKLIST.md
- VPS_QUICK_DEPLOY.md
- SYSTEM_SETUP_SUMMARY.md
```

---

## SIMPLE 3-STEP PROCESS

### Step 1: Copy Folder
Copy entire `_vps_deploy_bundle/` to VPS

### Step 2: Copy requirements.txt
Copy `requirements.txt` to same VPS folder

### Step 3: Edit .env on VPS
```
nano /vps/backend/.env

Change these:
DB_HOST=localhost       (or your DB IP)
DB_PASSWORD=YourPassword
API_HOST=0.0.0.0        (to allow external connections)
```

---

## THAT'S IT!

Then run:
```bash
pip install -r requirements.txt
python multi_broker_backend_updated.py
```

And your trading system is live! 🚀

---

## VERIFY IT'S WORKING

```bash
# In another terminal:
curl http://your.vps.ip:9000/api/health

# Should return: OK
```

---

## FILES YOU DON'T NEED

❌ Don't copy:
- Flutter app folder
- Test files
- Backup files
- Frontend code
- Development tools

---

## STORAGE NEEDED ON VPS

- **Code**: ~2 MB
- **Database**: 100 MB - 1 GB (grows with trades)
- **Logs**: 100 MB - 500 MB (rotates over time)
- **Total Recommended**: 50 GB

---

## QUICK FOLDER SUMMARY

| Folder | What | Need? |
|--------|------|-------|
| `_vps_deploy_bundle/` | API Server + All Services | ✅ REQUIRED |
| Root `requirements.txt` | Python Packages | ✅ REQUIRED |
| Root `_diagnose_*.py` | Diagnostic Tools | ⚠️ Recommended |
| `Zwesta Flutter App/` | Frontend | ❌ Only if using UI |
| `test_*.py` | Test Files | ❌ Development only |
| Backup files | Old versions | ❌ Not needed |

---

**TLDR: Copy `_vps_deploy_bundle/` + `requirements.txt`, edit `.env`, install & run! 🚀**

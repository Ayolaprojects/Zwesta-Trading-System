# VPS DEPLOYMENT CHECKLIST - What to Take

**Date**: June 5, 2026  
**For**: Production Trading System (Binance + Exness)

---

## CORE FILES TO COPY

### 1. BACKEND API SERVER (REQUIRED)
**Source**: `c:\zwesta-trader\_vps_deploy_bundle\`

Copy to VPS:
```
multi_broker_backend_updated.py         [1.8 MB] - Main API server
multi_broker_backend_updated.bat         [<1 KB] - Batch launcher
start_zwesta_backend.ps1               [8 KB]  - PowerShell launcher
postgres_schema.py                      [15 KB] - Database schema
runtime_infrastructure.py               [45 KB] - DB manager
binance_service.py                      [120 KB] - Binance integration
fxcm_service.py                         [80 KB] - FXCM integration (optional)
.env                                    [2 KB]  - Environment variables
```

**Total Size**: ~2.1 MB

### 2. BOT & TRADING SERVICES (REQUIRED)
Copy from root to VPS:
```
_diagnose_postgres_bots.py             [4 KB]  - Bot diagnostic
_verify_bot_creation_system.py          [6 KB]  - System verification
_verify_user_registration.py            [8 KB]  - User registration check
_auto_cleanup_disabled_bots.py           [3 KB]  - Bot cleanup utility
FINAL_VERIFICATION.py                   [2 KB]  - System health check
_enable_exness_bots.py                  [3 KB]  - Bot enablement
```

**Total Size**: ~26 KB

### 3. PYTHON DEPENDENCIES (REQUIRED)
```
requirements.txt                        [1 KB]  - All Python packages
```

**Key Packages**:
- Flask==2.2.5
- python-binance==1.0.17
- MetaTrader5==5.0.5735
- psycopg2-binary
- APScheduler
- requests
- cryptography

**Installation**:
```bash
pip install -r requirements.txt
```

---

## DATABASE SETUP (REQUIRED)

### Option A: PostgreSQL (Recommended for VPS)
**Required Files**:
```
_vps_deploy_bundle/postgres_schema.py      - Schema creation
_vps_deploy_bundle/.env                    - DB credentials
```

**Setup Steps**:
1. Install PostgreSQL Server
2. Create database: `zwesta_trading`
3. Create user: `zwesta_admin`
4. Run schema: `python postgres_schema.py`

### Option B: SQLite (Fallback)
**File**: Database auto-created at runtime
- Default location: `c:\backend\zwesta_trading.db`
- No setup needed - auto-initialize on first run

---

## ENVIRONMENT CONFIGURATION (CRITICAL)

### Copy `.env` file with these settings:

```
# =============================================================
# VPS DEPLOYMENT ENVIRONMENT
# =============================================================

# DEPLOYMENT
TRADING_ENV=LIVE
DEPLOYMENT_MODE=VPS
AUTO_RESTART_BOTS_ON_STARTUP=true

# DATABASE
DB_HOST=localhost          # or your VPS IP
DB_PORT=5432
DB_NAME=zwesta_trading
DB_USER=zwesta_admin
DB_PASSWORD=YourSecurePassword

# API SERVER
API_PORT=9000
API_HOST=0.0.0.0           # Accept external connections

# BINANCE
BINANCE_TIMEOUT=30
BINANCE_RETRIES=3

# EXNESS (MT5)
EXNESS_LIVE_PATH=/path/to/MT5/terminal64.exe    # Linux: ~/.wine/...
EXNESS_DEMO_PATH=/path/to/MT5Demo/terminal64.exe
EXNESS_ACCOUNT=295677214
EXNESS_SERVER=Exness-MT5Real27

# OPTIONAL
REDIS_URL=redis://localhost:6379
LOG_LEVEL=INFO
DEBUG=False
```

---

## DIRECTORY STRUCTURE ON VPS

```
/vps/
├── backend/
│   ├── multi_broker_backend_updated.py      [Main server]
│   ├── postgres_schema.py                   [Schema]
│   ├── runtime_infrastructure.py            [DB manager]
│   ├── binance_service.py                   [Binance bot service]
│   ├── fxcm_service.py                      [FXCM service]
│   ├── start_zwesta_backend.ps1             [Launcher]
│   ├── .env                                 [Config]
│   ├── requirements.txt                     [Dependencies]
│   └── zwesta_trading.db                    [SQLite DB - auto-created]
│
├── tools/
│   ├── _diagnose_postgres_bots.py
│   ├── _verify_bot_creation_system.py
│   ├── _verify_user_registration.py
│   ├── _auto_cleanup_disabled_bots.py
│   ├── FINAL_VERIFICATION.py
│   └── _enable_exness_bots.py
│
├── logs/
│   ├── bot_errors.log
│   ├── bot_trades.log
│   └── api.log
│
└── data/
    └── backups/
        └── zwesta_trading_backup.sql
```

---

## QUICK DEPLOYMENT STEPS

### 1. Prepare VPS
```bash
# Install Python 3.11+
python --version

# Install virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate      # Windows
```

### 2. Copy Files
```bash
# Copy all backend files
scp -r _vps_deploy_bundle/* root@vps:/vps/backend/

# Copy tools
scp _diagnose_postgres_bots.py root@vps:/vps/tools/
scp _verify_bot_creation_system.py root@vps:/vps/tools/
# ... copy other tools
```

### 3. Install Dependencies
```bash
cd /vps/backend
pip install -r requirements.txt
```

### 4. Setup Database
```bash
# PostgreSQL setup
python postgres_schema.py

# OR keep SQLite (auto-create)
```

### 5. Configure Environment
```bash
# Edit .env with your VPS settings
nano /vps/backend/.env

# Required changes:
# - DB_HOST: your VPS IP or "localhost"
# - DB_PASSWORD: secure password
# - EXNESS paths: adjust for Linux
# - API_HOST: set to 0.0.0.0 for external access
```

### 6. Start Backend Server
```bash
cd /vps/backend

# Using Python directly
python multi_broker_backend_updated.py

# OR using launcher (if PowerShell available)
./start_zwesta_backend.ps1
```

### 7. Verify System
```bash
cd /vps/tools

# Check bot status
python _verify_bot_creation_system.py

# Check user registration
python _verify_user_registration.py

# Final verification
python FINAL_VERIFICATION.py
```

---

## FILES NOT NEEDED FOR VPS

❌ Don't copy:
- Flutter app files (if using web dashboard)
- Test files (`test_*.py`)
- Backup files (`.backup`)
- Frontend code
- Development tools

---

## MINIMUM VIABLE VPS DEPLOYMENT

**Absolute minimum to run**:
1. `multi_broker_backend_updated.py` - API server
2. `binance_service.py` - Bot execution
3. `runtime_infrastructure.py` - DB connection
4. `requirements.txt` - Dependencies
5. `.env` - Configuration

**Size**: ~2 MB  
**Time to deploy**: ~10 minutes

---

## PRODUCTION CHECKLIST

- [ ] Python 3.11+ installed
- [ ] Virtual environment created and activated
- [ ] All files copied to VPS
- [ ] requirements.txt installed
- [ ] PostgreSQL server running (if using PG)
- [ ] Database created and schema applied
- [ ] `.env` file configured with VPS settings
- [ ] Port 9000 open for API access
- [ ] Backend server starts without errors
- [ ] Run system verification scripts
- [ ] Test bot creation works
- [ ] Monitor logs for trading activity
- [ ] Set up auto-restart on VPS reboot

---

## ESSENTIAL COMMANDS REFERENCE

```bash
# Start backend
python multi_broker_backend_updated.py

# Check system health
python FINAL_VERIFICATION.py

# Verify bots
python _verify_bot_creation_system.py

# Check users
python _verify_user_registration.py

# Cleanup disabled bots
python _auto_cleanup_disabled_bots.py

# View logs
tail -f bot_trades.log
tail -f api.log
```

---

## VPS SYSTEM REQUIREMENTS

- **OS**: Linux (Ubuntu 20.04+) or Windows Server 2019+
- **Python**: 3.11 or 3.12
- **RAM**: 4 GB minimum (8 GB recommended)
- **Storage**: 50 GB (for database growth)
- **Network**: 100+ Mbps stable connection
- **Database**: PostgreSQL 13+ OR SQLite
- **Broker Terminals**: MT5 (for Exness)

---

**Last Updated**: June 5, 2026  
**System Status**: Production Ready ✓

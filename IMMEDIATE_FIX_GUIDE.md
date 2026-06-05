# IMMEDIATE ACTION GUIDE - Critical System Fixes

## SUMMARY
**Status:** System has 2 blocking critical issues preventing operation
**Time to Fix:** ~30 minutes
**Downtime Required:** ~5 minutes (PostgreSQL restart)

---

## ISSUE 1: PostgreSQL max_connections (BLOCKING ALL CONNECTIONS)

### Current State
- PostgreSQL max: 100 connections
- Backend pool wants: 200 connections  
- Result: System crashes when connections exceed ~90

### FIX - PostgreSQL Configuration

**Step 1: Stop Backend (Optional - will help)**
```powershell
Stop-Process -Name python -Force
```

**Step 2: Edit PostgreSQL Config**
On the PostgreSQL server machine:
```bash
# For Linux:
sudo nano /etc/postgresql/15/main/postgresql.conf

# For Windows (if running local PostgreSQL):
# Edit: C:\Program Files\PostgreSQL\15\data\postgresql.conf
```

**Step 3: Find and Change max_connections**
```bash
# Find this line (around line 63):
# max_connections = 100

# Change to:
max_connections = 250

# Save and exit (Ctrl+X, Y, Enter in nano)
```

**Step 4: Restart PostgreSQL**
```bash
# Linux:
sudo systemctl restart postgresql

# Windows:
# Open Services.msc, find "PostgreSQL", right-click Restart
# OR:
net stop PostgreSQL15
net start PostgreSQL15

# macOS:
brew services restart postgresql
```

**Step 5: Verify**
```powershell
python -c "
import psycopg2
conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='zwesta_trading',
    user='zwesta_admin',
    password='Zwesta@Trading2026!'
)
cur = conn.cursor()
cur.execute('SELECT setting FROM pg_settings WHERE name=\'max_connections\';')
result = cur.fetchone()[0]
print(f'max_connections = {result}')
cur.close()
conn.close()
"
# Should print: max_connections = 250
```

---

## ISSUE 2: Database Schema - Ticket Column Type (BLOCKING TRADE STORAGE)

### Current State
- Column `ticket` is INTEGER
- Code stores STRING values ("SOLUSDT", "SPOT-BTC", etc.)
- Trades fail to insert

### FIX - Alter Table Schema

**Step 1: Connect to Database**
```powershell
# From any machine with psql:
psql -U zwesta_admin -d zwesta_trading -h localhost
# Password: Zwesta@Trading2026!
```

**Step 2: Run ALTER TABLE Command**
```sql
ALTER TABLE trades ALTER COLUMN ticket TYPE varchar(255);
```

**Step 3: Verify**
```sql
SELECT column_name, data_type FROM information_schema.columns 
WHERE table_name = 'trades' AND column_name = 'ticket';
-- Should show: ticket | character varying
```

**Step 4: Exit**
```sql
\q
```

---

## ISSUE 3: Connection Leak in Monitor Thread (HIGH PRIORITY)

### Current State
- Auto-withdrawal monitor thread not releasing connections properly
- Errors seen in logs repeatedly

### FIX - Code Change Required

**This requires finding and modifying the auto-withdrawal monitor code in:**
`/backend/multi_broker_backend_updated.py`

**Search for function and verify pattern:**
```python
# Find: def monitor_auto_withdrawal():
# Or: def auto_withdrawal_monitor():

# Current pattern (BAD):
def monitor_auto_withdrawal():
    while True:
        try:
            conn = self.pool.getconn()
            # ... do something ...
        except Exception as e:
            logger.error(f"Error: {e}")
            # Missing: conn.putconn()

# Should be (GOOD):
def monitor_auto_withdrawal():
    while True:
        conn = None
        try:
            conn = self.pool.getconn()
            # ... do something ...
        except Exception as e:
            logger.error(f"Error: {e}")
        finally:
            if conn:
                self.pool.putconn(conn)
            time.sleep(30)  # Add delay
```

**Action:** 
- Find the auto-withdrawal monitor in the file
- Wrap connection release in finally block
- Add sleep(30) to prevent rapid retries

---

## POST-FIX VERIFICATION

### Test 1: Database Connectivity
```powershell
python -c "
import psycopg2
conn = psycopg2.connect('postgresql://zwesta_admin:Zwesta@Trading2026!@localhost:5432/zwesta_trading')
print('✓ Database connected')
cur = conn.cursor()
cur.execute('SELECT setting FROM pg_settings WHERE name=\'max_connections\';')
print(f'✓ max_connections = {cur.fetchone()[0]}')
cur.execute('SELECT data_type FROM information_schema.columns WHERE table_name=\'trades\' AND column_name=\'ticket\';')
print(f'✓ ticket column type = {cur.fetchone()[0]}')
cur.close()
conn.close()
"
```

### Test 2: Start Backend
```powershell
cd c:\backend
python multi_broker_backend_updated.py

# Watch for errors (should be none):
# Monitor in another terminal:
Get-Content -Path c:\backend\backend.log -Wait | Select-String "ERROR.*connection"
```

### Test 3: Create Test Bot
```powershell
# In another terminal:
$body = @{
    "symbol" = "SOLUSDT"
    "broker" = "binance"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:9000/api/bot/create" `
  -Method POST `
  -Body $body `
  -Headers @{"Content-Type"="application/json"; "X-Session-Token"="test-token"}
```

---

## TROUBLESHOOTING

### If Still Getting "connection slots reserved for SUPERUSER"
1. Check max_connections again: `SHOW max_connections;`
2. Count current connections: `SELECT count(*) FROM pg_stat_activity;`
3. If >100, restart PostgreSQL again
4. Kill Python backend: `Stop-Process -Name python -Force`

### If Still Getting "invalid input syntax for type integer"
1. Check column type: `SELECT data_type FROM information_schema.columns WHERE table_name='trades' AND column_name='ticket';`
2. Should be: `character varying` or `varchar`
3. If still integer, rerun ALTER TABLE

### If Backend Still Has Connection Errors
1. Find auto-withdrawal monitor in code
2. Add finally block to release connections
3. Add sleep(30) delay
4. Restart backend

---

## NEXT STEPS AFTER FIXES

1. ✅ Fix PostgreSQL max_connections
2. ✅ Fix database ticket column type  
3. ✅ Fix connection leak in monitor
4. ✅ Restart backend
5. ✅ Verify logs show no ERROR entries
6. ✅ Test bot creation
7. ✅ Deploy to VPS with same fixes
8. ✅ Monitor for 24 hours

---

## QUICK COMMANDS REFERENCE

```powershell
# Stop backend
Stop-Process -Name python -Force

# Check logs for errors
Select-String "ERROR" c:\backend\backend.log | Select-Object -Last 20

# Verify DB connection
python diagnose_issues.py

# Start backend
cd c:\backend; python multi_broker_backend_updated.py

# Monitor in real-time
Get-Content -Path c:\backend\backend.log -Wait
```

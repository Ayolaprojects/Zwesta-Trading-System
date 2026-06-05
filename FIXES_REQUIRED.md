# Comprehensive Bug Fix Plan

## ISSUE 1: PostgreSQL max_connections Limit (CRITICAL)

### Problem
- PostgreSQL has `max_connections = 100` (default)
- Backend pool configured for `PG_POOL_MAX = 200`
- Result: System crashes when >90 connections (reserves ~10 for superuser)
- Seen in logs: 15+ connection exhaustion errors

### Root Cause
PostgreSQL cannot support more connections than `max_connections` setting. Once limit reached, only SUPERUSER can connect.

### Fix
```bash
# On PostgreSQL Server:
sudo nano /etc/postgresql/15/main/postgresql.conf

# Find line and change:
# OLD: max_connections = 100
# NEW: max_connections = 250

# Restart PostgreSQL:
sudo systemctl restart postgresql

# Verify:
psql -U zwesta_admin -d zwesta_trading -c "SELECT setting FROM pg_settings WHERE name='max_connections';"
# Should show: 250
```

### Justification
- We have backend pool of 200, need room for system connections
- Set to 250 for safety margin
- Single server, can safely allocate

### Testing After Fix
```bash
# Verify setting
psql -U zwesta_admin -d zwesta_trading -c "SHOW max_connections;"

# Test from app:
python -c "import psycopg2; conn = psycopg2.connect('...'); print('Connected')"
```

---

## ISSUE 2: Database Schema - Ticket Column Type (CRITICAL)

### Problem
- Column `ticket` defined as INTEGER
- Code stores STRING values like "SOLUSDT", "SPOT-BTC", "SPOT-SOL-14015"
- Database rejects with: `invalid input syntax for type integer: "SOLUSDT"`

### Root Cause
**Code Issue Locations:**
- **Line 9085:** Binance futures: `'ticket': pos.get('symbol', '')` 
  - Stores: "SOLUSDT", "ETHUSDT", etc.
- **Line 9118:** Binance spot holdings: `'ticket': f'SPOT-{asset}'`
  - Stores: "SPOT-BTC", "SPOT-ETH", etc.
- **Line 39516:** Binance spot orders (BUY): `pos_ticket = f"SPOT-{base_asset}-{str(bot_id)[-8:]}"`
  - Stores: "SPOT-SOL-1780415", etc.
- **Lines 39615, 39746:** Database INSERT statements try to store these strings in INTEGER column

### Fix Option 1: Schema Change (RECOMMENDED)
```sql
-- Simplest fix: Change column type
ALTER TABLE trades ALTER COLUMN ticket TYPE varchar(255);

-- Verify:
SELECT column_name, data_type FROM information_schema.columns 
WHERE table_name = 'trades' AND column_name = 'ticket';
-- Should show: ticket | character varying
```

**Pros:**
- One SQL command
- No code changes needed
- Supports all current patterns

**Cons:**
- Loses integer validation
- Trades table structure changed

### Fix Option 2: Code Change (COMPLEX)
Change all 5 code locations to use integer IDs instead of symbols:
- Line 9085: Use order ID from broker instead of symbol
- Line 9118: Generate/lookup integer position ID
- Line 39516: Use broker order ID
- Lines 39615, 39746: Ensure only integers stored

**Pros:**
- Maintains database integrity
- More semantic (ticket = integer ID)

**Cons:**
- Requires 10+ code changes
- May break existing trade lookups
- Need migration for existing trades

### Recommended Fix: Schema Change
**Action:**
```sql
-- Connect as superuser or zwesta_admin
psql -U zwesta_admin -d zwesta_trading

-- Run this SQL:
ALTER TABLE trades ALTER COLUMN ticket TYPE varchar(255);

-- Verify:
SELECT column_name, data_type FROM information_schema.columns 
WHERE table_name = 'trades' AND column_name = 'ticket';
```

---

## ISSUE 3: PostgreSQL Connection Leak in Auto-Withdrawal Monitor

### Problem
- Auto-withdrawal monitor thread repeatedly fails with connection exhaustion
- 15 errors in current log session
- Happens even with 200 connection pool

### Root Cause
Likely not properly releasing connections in error paths. Monitor thread runs every N seconds, and if each iteration creates a connection and doesn't release it on error, it will exhaust the pool.

### Suspected Location
Search for auto-withdrawal monitor thread in `multi_broker_backend_updated.py`:
```python
def monitor_auto_withdrawal():
    while True:
        try:
            conn = get_connection()  # May not be released on error
            # ... monitor logic ...
        except Exception as e:
            # Doesn't call putconn() in all paths
            pass
```

### Fix Pattern
```python
def monitor_auto_withdrawal():
    while True:
        conn = None
        try:
            conn = get_connection()
            # ... monitor logic ...
        except Exception as e:
            logger.error(f"Error in auto-withdrawal: {e}")
        finally:
            if conn:
                conn.putconn()  # Always release
            time.sleep(30)  # Prevent rapid retry
```

### Action
1. Find auto-withdrawal monitor code
2. Add `finally` block to guarantee `putconn()`
3. Add sleep delay to prevent rapid connection attempts
4. Test with backend running

---

## Implementation Order

### Phase 1: Immediate (Do First)
1. **Fix PostgreSQL max_connections**
   - Edit postgresql.conf
   - Set max_connections = 250
   - Restart PostgreSQL
   - This unblocks all operations

2. **Fix Database Schema**
   - ALTER TABLE trades ALTER COLUMN ticket TYPE varchar(255)
   - This unblocks trade storage

### Phase 2: Follow-up (After Verification)
1. Find and fix auto-withdrawal monitor connection leak
2. Test system under load
3. Verify no connection errors

### Phase 3: Long-term (Future)
1. Consider proper ticket ID management
2. Add connection pool monitoring/metrics
3. Set up alerts for connection pool exhaustion

---

## Verification Steps

### After Fix 1 (PostgreSQL)
```bash
# Check setting
psql -U zwesta_admin -d zwesta_trading -c "SHOW max_connections;"
# Should show: 250

# Check current connections
psql -U zwesta_admin -d zwesta_trading -c "SELECT count(*) FROM pg_stat_activity;"
# Should be reasonable (not 100+)
```

### After Fix 2 (Schema)
```bash
# Check column type
psql -U zwesta_admin -d zwesta_trading -c \
  "SELECT data_type FROM information_schema.columns 
   WHERE table_name='trades' AND column_name='ticket';"
# Should show: character varying

# Test insert
psql -U zwesta_admin -d zwesta_trading -c \
  "INSERT INTO trades (trade_id, bot_id, user_id, symbol, ticket) 
   VALUES ('t1', 'b1', 'u1', 'SOLUSDT', 'SOLUSDT');"
# Should succeed
```

### System Test
```bash
# Start backend
cd /backend && python multi_broker_backend_updated.py

# Monitor logs
tail -f /backend/backend.log | grep -E "ERROR|Connection"

# Should NOT see connection exhaustion errors
```

---

## Summary Table

| Issue | Severity | Location | Fix | Effort |
|-------|----------|----------|-----|--------|
| max_connections | CRITICAL | PostgreSQL config | Change setting + restart | 5 min |
| ticket type | CRITICAL | Database schema | ALTER TABLE | 2 min |
| Connection leak | HIGH | Monitor thread | Add finally block | 15 min |

**Total Fix Time: ~30 minutes**
**System Downtime: ~5 minutes (PostgreSQL restart)**

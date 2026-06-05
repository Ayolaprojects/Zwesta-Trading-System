# PostgreSQL Setup Guide for Exness & Binance Bot Execution

## Overview

The trading bot backend now supports PostgreSQL for improved scalability and concurrent bot execution. This guide explains how to set up PostgreSQL and verify that both Exness and Binance bots execute successfully.

## What Was Fixed

### Problem
The backend had 29 hardcoded `build_sqlite_connection()` calls that bypassed PostgreSQL entirely. When PostgreSQL was configured, these calls would fail and prevent:
- Bot loading from database
- Trade history retrieval  
- Credential resolution
- Open positions loading
- Runtime state persistence

### Solution
Modified the `build_sqlite_connection()` function to automatically detect PostgreSQL mode and delegate to the `_PostgresCompatConnection` abstraction layer. This single change fixes all 29 call sites.

## Prerequisites

1. **PostgreSQL Server**: Version 12 or later
   - Local installation, remote server, or managed service (AWS RDS, Azure Database, etc.)
   - Must be running and accessible

2. **Python Dependencies**:
   ```bash
   pip install psycopg2-binary
   pip install sqlalchemy
   ```

3. **Database User**: A PostgreSQL user with:
   - CREATE/DROP TABLE permissions
   - SELECT/INSERT/UPDATE/DELETE permissions
   - Default database creation privileges

## Configuration

### Step 1: Set DATABASE_URL Environment Variable

For **local PostgreSQL**:
```bash
set DATABASE_URL=postgresql://username:password@localhost:5432/zwesta_trader
```

For **remote PostgreSQL** (e.g., AWS RDS):
```bash
set DATABASE_URL=postgresql://username:password@your-host.rds.amazonaws.com:5432/zwesta_trader
```

### Step 2: Initialize Database Schema

Run the setup script:
```bash
cd c:\zwesta-trader
call setup_postgres.bat
```

Or manually initialize:
```bash
python -c "from multi_broker_backend_updated import init_database; init_database()"
```

### Step 3: Verify PostgreSQL Setup

Run the verification test:
```bash
python _test_postgres_setup.py
```

Expected output for successful setup:
```
=== Testing Database Connection ===
✅ PostgreSQL mode enabled
✅ Database connection successful

=== Testing Bot Loading ===
✅ Bot loading successful: N bots loaded
   - Exness bots: X
   - Binance bots: Y

=== Testing Credential Resolution ===
✅ Credential resolved successfully

=== Testing Trade History Access ===
✅ Trade history accessible

=== Testing Runtime State Persistence ===
✅ Runtime state persistence working
```

## Running the Backend with PostgreSQL

### Option 1: Using setup_auto_restart.bat
The existing `setup_auto_restart.bat` will automatically use PostgreSQL if DATABASE_URL is set:
```bash
call setup_auto_restart.bat
```

### Option 2: Manual Start
```bash
python multi_broker_backend_updated.py
```

## Verifying Bot Execution

### Check Logs
Monitor the backend logs for successful bot loading:
```
✅ Loaded N user-created bots from database
```

### Verify Specific Brokers

**For Exness Bots:**
- Logs should show: `Bot execution... Exness`
- Check for: `[Exness] Connected to account XXX`
- Trades should be placed when signals are generated

**For Binance Bots:**
- Logs should show: `Bot execution... Binance`
- For futures accounts: `[Binance-Futures] Connected to USDT account`
- For spot accounts: `[Binance-Spot] Connected to USDT/ZAR wallet`

## Troubleshooting

### Issue: "DATABASE_URL is required when PostgreSQL mode is enabled"

**Solution**: Set the DATABASE_URL environment variable before starting the backend
```bash
set DATABASE_URL=postgresql://user:password@host:5432/db
python multi_broker_backend_updated.py
```

### Issue: "psycopg2 is required when PostgreSQL mode is enabled"

**Solution**: Install psycopg2
```bash
pip install psycopg2-binary
```

### Issue: Bots not loading after switching to PostgreSQL

**Cause**: The database tables exist but are empty (credentials or bots not migrated)

**Solution**: 
1. Ensure your credentials are in the `broker_credentials` table
2. Ensure your bots are in the `user_bots` table
3. Check that `bot_credentials` links them properly
4. Verify credentials are marked `is_active = 1`

**Check data migration:**
```sql
-- Check Exness credentials
SELECT credential_id, broker_name, account_number, is_active 
FROM broker_credentials 
WHERE broker_name = 'Exness' AND is_active = 1;

-- Check Binance credentials  
SELECT credential_id, broker_name, account_number, account_currency, is_active
FROM broker_credentials
WHERE broker_name = 'Binance' AND is_active = 1;

-- Check bots
SELECT bot_id, user_id, enabled, is_live
FROM user_bots
WHERE enabled = 1;
```

### Issue: Performance slow with PostgreSQL

**Optimization**:
1. Increase connection pool size:
   ```bash
   set PG_POOL_MAX=30
   ```

2. Ensure PostgreSQL is properly indexed (automatic via `create_postgres_schema()`)

3. For large databases, enable connection pooling (pgBouncer) between backend and PostgreSQL

### Issue: Binance futures bot shows "0 trades" but was working in SQLite

**Cause**: Account currency might not be set correctly for USDT futures accounts

**Solution**:
1. Check broker_credentials table:
   ```sql
   SELECT credential_id, account_number, account_currency, server 
   FROM broker_credentials 
   WHERE broker_name = 'Binance';
   ```

2. For futures accounts, ensure:
   - `account_currency = 'USDT'` (not 'ZAR')
   - `server = 'spot'` or `'futures'` depending on account type

3. Update if needed:
   ```sql
   UPDATE broker_credentials 
   SET account_currency = 'USDT'
   WHERE broker_name = 'Binance' AND server = 'futures';
   ```

## Migration from SQLite

If you have an existing SQLite database and want to migrate to PostgreSQL:

### Automated Migration Script

Create `migrate_sqlite_to_postgres.py`:
```python
#!/usr/bin/env python3
import sqlite3
import psycopg2
from datetime import datetime

def migrate():
    # Connect to SQLite
    sqlite_conn = sqlite3.connect('trading_bot.db')
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    
    # Connect to PostgreSQL
    import os
    pg_url = os.getenv('DATABASE_URL')
    pg_conn = psycopg2.connect(pg_url)
    pg_cursor = pg_conn.cursor()
    
    # Tables to migrate (in dependency order)
    tables = ['users', 'broker_credentials', 'user_bots', 'bot_credentials', 'trades']
    
    for table in tables:
        print(f"Migrating {table}...")
        
        # Get data from SQLite
        sqlite_cursor.execute(f"SELECT * FROM {table}")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            print(f"  → {table} is empty, skipping")
            continue
        
        # Get column names
        columns = [description[0] for description in sqlite_cursor.description]
        
        # Insert into PostgreSQL
        placeholders = ','.join(['%s'] * len(columns))
        insert_sql = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
        
        for row in rows:
            pg_cursor.execute(insert_sql, tuple(row))
        
        pg_conn.commit()
        print(f"  ✅ Migrated {len(rows)} rows")
    
    print("\n✅ Migration complete!")
    sqlite_conn.close()
    pg_conn.close()

if __name__ == '__main__':
    import os
    if not os.getenv('DATABASE_URL'):
        print("ERROR: Set DATABASE_URL environment variable first")
        exit(1)
    migrate()
```

Run migration:
```bash
set DATABASE_URL=postgresql://user:password@host:5432/db
python migrate_sqlite_to_postgres.py
```

## Architecture

### Connection Pool
The backend maintains a PostgreSQL connection pool (configurable):
- Default: 2-20 connections
- Customize with `PG_POOL_MAX` environment variable
- Improves performance for concurrent bot execution

### Compatibility Layer
The `_PostgresCompatConnection` class provides:
- SQLite API compatibility for `cursor()` and `execute()` calls
- Automatic SQL translation (INSERT OR REPLACE → INSERT ... ON CONFLICT)
- Boolean column mapping (1/0 → true/false)
- Row factory for dict-like access

### Query Translation
Example SQL transformations:
```sql
-- SQLite
INSERT OR REPLACE INTO table (id, name) VALUES (?, ?)

-- PostgreSQL (auto-translated)
INSERT INTO table (id, name) VALUES (%s, %s) 
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name
```

## Support for Both Exness and Binance

### Exness Requirements
✅ Supported in PostgreSQL mode
- Account type: Any (Cent, Standard, Professional)
- Terminal: MT5
- Credentials stored: username, password, server, account_currency

### Binance Requirements  
✅ Supported in PostgreSQL mode
- Account type: Spot, Margin, or Futures
- Currency: USDT (futures), ZAR or other (spot)
- Credentials stored: api_key, api_secret, account_currency, server (spot/futures)
- Special handling: Futures accounts require `market = 'futures'` flag

## Additional Notes

1. **Always backup your SQLite database before migrating to PostgreSQL**
   ```bash
   copy trading_bot.db trading_bot.db.backup
   ```

2. **Test PostgreSQL in a non-production environment first**

3. **Monitor PostgreSQL logs** for any connection or permission issues

4. **Regular backups** of PostgreSQL are recommended:
   ```bash
   pg_dump -U username -d zwesta_trader > backup_$(date +%Y%m%d).sql
   ```

5. **Connection timeouts** can be adjusted:
   - `set SQLITE_CONNECTION_TIMEOUT_SECONDS=90` for longer operations
   - Default is 60 seconds

## Support

If you encounter issues:
1. Check the PostgreSQL server is running and accessible
2. Verify DATABASE_URL format is correct
3. Run `_test_postgres_setup.py` for diagnostics
4. Check backend logs for specific error messages
5. Ensure both Exness and Binance credentials are properly configured in the database

#!/usr/bin/env python
import sqlite3
import os

# Find the database
db_path = None
for root, dirs, files in os.walk('.'):
    if 'trader.db' in files:
        db_path = os.path.join(root, 'trader.db')
        break

if not db_path:
    print("❌ trader.db not found")
else:
    print(f"✅ Found database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Check if broker_credentials table exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='broker_credentials'")
    if not cur.fetchone():
        print("❌ broker_credentials table not found")
    else:
        print("✅ broker_credentials table exists")
        
        # Get all Exness credentials
        cur.execute("""
            SELECT credential_id, broker_name, account_number, is_live, server, is_active
            FROM broker_credentials 
            WHERE broker_name LIKE '%Exness%' OR broker_name LIKE '%MT5%'
            ORDER BY account_number
        """)
        
        rows = cur.fetchall()
        if not rows:
            print("❌ No Exness credentials found in database")
        else:
            print(f"\n✅ Found {len(rows)} Exness credentials:\n")
            for row in rows:
                is_live_label = "LIVE" if row['is_live'] == 1 else "DEMO"
                active_label = "✓ ACTIVE" if row['is_active'] == 1 else "✗ INACTIVE"
                print(f"  Account: {row['account_number']:12} | Mode: {is_live_label:4} | Server: {row['server']:25} | {active_label}")
    
    conn.close()

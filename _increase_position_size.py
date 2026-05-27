#!/usr/bin/env python3
import sqlite3
import json

DB_PATH = r'C:\backend\zwesta_trading.db'

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Get all bots
cur.execute("SELECT bot_id, runtime_state FROM user_bots")
all_bots = cur.fetchall()

# Filter for Exness bots
for bot_id, runtime_state in all_bots:
    rs = json.loads(runtime_state or '{}')
    
    # Skip non-Exness bots
    if 'Exness' not in rs.get('brokerName', ''):
        continue
    
    # Increase base position size
    old_size = rs.get('basePositionSize', 0.01)
    new_size = 0.02  # CHANGE THIS VALUE:
                     # 0.02 = 2x (conservative)
                     # 0.03 = 3x (moderate) 
                     # 0.05 = 5x (aggressive)
                     # 0.10 = 10x (VERY aggressive - with 10x symbol multiplier = 100x total!)
    
    rs['basePositionSize'] = new_size
    
    print(f"Bot {bot_id[:25]}...: {old_size} → {new_size}")
    
    cur.execute("UPDATE user_bots SET runtime_state = ? WHERE bot_id = ?", 
               (json.dumps(rs), bot_id))

conn.commit()
conn.close()

print("✅ Base position size updated")
print("⚠️  Restart backend to apply changes")

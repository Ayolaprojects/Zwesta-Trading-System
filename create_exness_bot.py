import sqlite3
import json
from datetime import datetime

DB_PATH = r'C:\zwesta-trader\Zwesta Flutter App\zwesta_trading.db'

# Create an Exness MT5 demo bot
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Get the user_id from first bot
cur.execute("SELECT user_id FROM user_bots LIMIT 1")
user_id = cur.fetchone()[0]

# Check if Exness bot already exists
cur.execute("SELECT bot_id FROM user_bots WHERE symbols LIKE '%EURUSDm%' OR symbols LIKE '%GBPUSD%' OR symbols LIKE '%XAUUSDm%'")
if cur.fetchone():
    print("Exness bot already exists")
else:
    # Create Exness MT5 bot with conservative settings
    bot_id = f'bot_exness_mt5_demo_{int(datetime.now().timestamp())}'
    
    runtime_state = {
        'recentProfitRiskGuardEnabled': True,
        'maxDailyLoss': 100.0,
        'riskPerTrade': 20.0,
        'maximumHoldMinutes': 360,  # 6 hours max hold
        'minimumHoldMinutes': 20.0,
        'perSymbolStopLossPips': {
            'EURUSDm': 50,
            'GBPUSDm': 50, 
            'XAUUSDm': 100,
            'BTCUSDm': 200,
            'ETHUSDm': 200,
        },
        'perSymbolTakeProfitPips': {
            'EURUSDm': 100,  # 1:2 R:R
            'GBPUSDm': 100,
            'XAUUSDm': 300,
            'BTCUSDm': 500,
            'ETHUSDm': 500,
        },
        'effectiveMaxOpenPositions': 3,
        'status': 'active',
    }
    
    cur.execute("""
        INSERT INTO user_bots (
            bot_id, user_id, name, strategy, status, enabled, 
            daily_profit, total_profit, symbols, is_live, runtime_state,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        bot_id, user_id, 'Exness MT5 Demo Bot', 'scalping', 'active', 1,
        0.0, 0.0, 'EURUSDm,GBPUSDm,XAUUSDm,BTCUSDm', 0,
        json.dumps(runtime_state),
        datetime.now().isoformat(), datetime.now().isoformat()
    ))
    
    conn.commit()
    print(f'Created Exness MT5 demo bot: {bot_id}')
    print('  Symbols: EURUSDm, GBPUSDm, XAUUSDm, BTCUSDm')
    print('  Server: Exness-MT5Trial9 (demo mode)')

conn.close()
print('\n[INFO] Restart the backend worker to load the new bot')
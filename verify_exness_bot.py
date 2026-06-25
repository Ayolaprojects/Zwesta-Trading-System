import sqlite3
import json
conn = sqlite3.connect(r'zwesta_trading.db')
cur = conn.cursor()
cur.execute("SELECT bot_id, symbols, status, runtime_state FROM user_bots WHERE symbols LIKE '%EURUSDm%'")
for bot_id, symbols, status, rs in cur.fetchall():
    print(f'Exness Bot: {bot_id}')
    print(f'  Status: {status}')
    print(f'  Symbols: {symbols}')
    if rs:
        data = json.loads(rs)
        print(f'  RiskGuardEnabled: {data.get("recentProfitRiskGuardEnabled")}')
        print(f'  MaxDailyLoss: {data.get("maxDailyLoss")}')
        print(f'  MaxHoldMinutes: {data.get("maximumHoldMinutes")}')
conn.close()
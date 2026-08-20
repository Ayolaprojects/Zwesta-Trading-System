import sqlite3, json

conn = sqlite3.connect(r'C:\backend\zwesta_trading.db')
c = conn.cursor()
c.execute('SELECT bot_id, name, symbols, runtime_state FROM user_bots')
rows = c.fetchall()
print(f'Total bots: {len(rows)}')
for r in rows:
    rt = json.loads(r[3]) if r[3] else {}
    syms = rt.get('symbols', r[2])
    broker = rt.get('brokerName', rt.get('broker_type', ''))
    is_exness = 'US30' in str(syms) or 'XAUUSD' in str(syms) or 'EURUSD' in str(syms) or 'Exness' in str(broker) or 'MT5' in str(broker)
    if is_exness:
        print(f"BOT: {r[0]} ({r[1]}) broker={broker}")
        print(f"  symbols={syms}")
        print(f"  profile={rt.get('managementProfile','N/A')} tradeAmt={rt.get('tradeAmount','N/A')} maxPos={rt.get('maxOpenPositions','N/A')} bpSize={rt.get('basePositionSize','N/A')}")
        print(f"  totalProfit={rt.get('totalProfit','N/A')} blocked={rt.get('blockedSymbols', rt.get('symbolBlacklist', []))}")
        print()
conn.close()

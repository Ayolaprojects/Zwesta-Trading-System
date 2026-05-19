import sqlite3, json
db = sqlite3.connect(r'C:\backend\zwesta_trading.db')
db.row_factory = sqlite3.Row
cur = db.cursor()

# ── Summary per bot ────────────────────────────────────────────────────────────
print('=== TRADE SUMMARY PER BOT ===')
cur.execute('''
    SELECT bot_id, COUNT(*) as total,
           SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) as wins,
           SUM(CASE WHEN profit < 0 THEN 1 ELSE 0 END) as losses,
           ROUND(SUM(profit), 2) as total_pnl,
           MAX(time_open) as last_trade
    FROM trades
    GROUP BY bot_id
    ORDER BY last_trade DESC
''')
for row in cur.fetchall():
    print(f'  {row["bot_id"][:35]} trades={row["total"]} W={row["wins"]} L={row["losses"]} PnL={row["total_pnl"]} last={str(row["last_trade"])[:16]}')

# ── Recent 25 trades ───────────────────────────────────────────────────────────
print()
print('=== RECENT 25 TRADES ===')
cur.execute('''
    SELECT t.bot_id, t.symbol, t.order_type, t.volume, t.price, t.profit,
           t.time_open, t.time_close, t.status, t.broker
    FROM trades t
    ORDER BY t.time_open DESC
    LIMIT 25
''')
for t in cur.fetchall():
    pnl = t['profit']
    sign = '+' if pnl and pnl > 0 else ''
    status = t['status'] or 'open'
    ts = str(t['time_open'])[:16]
    print(f'  [{status}] {t["bot_id"][:28]} {t["symbol"]:12} {t["order_type"]:4} vol={t["volume"]} pnl={sign}{pnl} @ {t["price"]} {ts}')

# ── Open trades ────────────────────────────────────────────────────────────────
print()
print('=== OPEN / PENDING TRADES ===')
cur.execute('''
    SELECT t.bot_id, t.symbol, t.order_type, t.volume, t.price, t.profit, t.time_open, t.broker
    FROM trades t
    WHERE t.status IN ('open','pending','OPEN','active','ACTIVE') OR t.time_close IS NULL
    ORDER BY t.time_open DESC
''')
opens = cur.fetchall()
if opens:
    for t in opens:
        print(f'  {t["bot_id"][:28]} {t["symbol"]:12} {t["order_type"]:4} vol={t["volume"]} unrealised={t["profit"]} opened={str(t["time_open"])[:16]}')
else:
    print('  None in DB (live positions tracked in memory by bot, not DB)')

db.close()

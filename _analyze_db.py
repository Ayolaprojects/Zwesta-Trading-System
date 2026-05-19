import sqlite3, json

db = sqlite3.connect('C:/backend/zwesta_trading.db')
db.row_factory = sqlite3.Row
cur = db.cursor()

# Tables + row counts
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r['name'] for r in cur.fetchall()]
print('=== TABLES ===')
for t in tables:
    cur.execute(f'SELECT COUNT(*) as n FROM [{t}]')
    n = cur.fetchone()['n']
    print(f'  {t}: {n} rows')

# Schemas for key tables
print()
for t in ['user_bots','broker_credentials','trades','users','bot_activation_pins','bot_credentials']:
    if t in tables:
        cur.execute(f'PRAGMA table_info([{t}])')
        cols = [r['name'] for r in cur.fetchall()]
        print(f'{t} cols: {cols}')

# User bots summary
print('\n=== USER BOTS ===')
cur.execute("""
    SELECT ub.bot_id, ub.name, ub.strategy, ub.enabled, ub.is_live,
           ub.daily_profit, ub.total_profit, ub.created_at, ub.updated_at,
           bcr.broker_name, bcr.account_number, bcr.account_currency, bcr.cached_balance
    FROM user_bots ub
    LEFT JOIN bot_credentials bc ON bc.bot_id = ub.bot_id
    LEFT JOIN broker_credentials bcr ON bcr.credential_id = bc.credential_id
    WHERE ub.status = 'active'
""")
for r in cur.fetchall():
    print(f"  {r['bot_id']} | {r['broker_name']} | acct={r['account_number']} | "
          f"enabled={r['enabled']} | live={r['is_live']} | "
          f"daily_profit={r['daily_profit']} | total_profit={r['total_profit']} | "
          f"balance={r['cached_balance']} | currency={r['account_currency']}")

# Recent trades last 48h
print('\n=== RECENT TRADES (last 48h) ===')
cur.execute("""
    SELECT t.bot_id, t.ticket, t.symbol, t.order_type, t.volume,
           t.price, t.profit, t.status, t.time_open, t.time_close, t.trade_data
    FROM trades t
    WHERE t.time_open >= datetime('now', '-2 days')
    ORDER BY t.time_open DESC
    LIMIT 30
""")
for r in cur.fetchall():
    td = {}
    try:
        td = json.loads(r['trade_data'] or '{}')
    except:
        pass
    reason = td.get('closeReason','')
    direction = td.get('direction','') or td.get('type','') or r['order_type']
    print(f"  [{r['status']}] {r['symbol']} {direction} vol={r['volume']} "
          f"profit={r['profit']} open={r['time_open'][:16]} close={r['time_close'] and r['time_close'][:16] or 'open'} "
          f"reason={reason} bot={r['bot_id'][:20]}")

# Daily profit summary
print('\n=== DAILY PROFIT BY BOT ===')
cur.execute("""
    SELECT bot_id, 
           SUM(CASE WHEN status='closed' THEN profit ELSE 0 END) as total,
           SUM(CASE WHEN status='closed' AND date(time_open)=date('now') THEN profit ELSE 0 END) as today,
           SUM(CASE WHEN status='closed' AND date(time_open)=date('now','-1 day') THEN profit ELSE 0 END) as yesterday,
           COUNT(CASE WHEN status='closed' THEN 1 END) as trades
    FROM trades
    GROUP BY bot_id
""")
for r in cur.fetchall():
    print(f"  {r['bot_id'][:25]} | total={r['total'] and round(r['total'],2)} | "
          f"today={r['today'] and round(r['today'],2)} | yesterday={r['yesterday'] and round(r['yesterday'],2)} | "
          f"closed_trades={r['trades']}")

db.close()

import sqlite3, json
db = sqlite3.connect(r'C:\backend\zwesta_trading.db')
db.row_factory = sqlite3.Row
cur = db.cursor()

# ── All credentials ───────────────────────────────────────────────────────────
print('=== ALL BROKER CREDENTIALS ===')
cur.execute('SELECT credential_id, broker_name, account_number, is_live, account_currency, cached_balance, label FROM broker_credentials ORDER BY broker_name')
for row in cur.fetchall():
    mode = 'LIVE' if row['is_live'] else 'DEMO'
    print(f'  [{mode}] {row["broker_name"]} acct={row["account_number"]} bal={row["cached_balance"]} {row["account_currency"]} id={str(row["credential_id"])[:20]} label={row["label"]}')

# ── All bots + linked credentials ─────────────────────────────────────────────
print()
print('=== ALL BOTS + LINKED CREDENTIALS ===')
cur.execute('''
    SELECT ub.bot_id, ub.is_live, ub.broker_account_id, ub.enabled, ub.total_profit,
           bc.credential_id, br.account_number, br.is_live as cred_live,
           br.account_currency, br.cached_balance, br.broker_name
    FROM user_bots ub
    LEFT JOIN bot_credentials bc ON ub.bot_id = bc.bot_id
    LEFT JOIN broker_credentials br ON bc.credential_id = br.credential_id
    ORDER BY ub.is_live DESC, ub.bot_id
''')
for row in cur.fetchall():
    bot_mode  = 'LIVE' if row['is_live'] else 'DEMO'
    cred_mode = 'LIVE' if row['cred_live'] else 'DEMO'
    match_flag = '✅' if row['is_live'] == row['cred_live'] else '❌MISMATCH'
    print(f'  {row["bot_id"][:35]} bot=[{bot_mode}] acct={row["broker_account_id"]} | cred_acct={row["account_number"]} [{cred_mode}] bal={row["cached_balance"]} {row["account_currency"]} {match_flag}')

# ── Recent trades ─────────────────────────────────────────────────────────────
print()
print('=== RECENT TRADES (last 20) ===')
cur.execute('''
    SELECT t.bot_id, t.symbol, t.order_type, t.profit, t.open_price, t.close_price,
           t.opened_at, t.closed_at, t.status
    FROM trades t
    ORDER BY t.opened_at DESC
    LIMIT 20
''')
rows = cur.fetchall()
if not rows:
    # try trade_log table
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    print('  No trades table — available tables:', tables)
else:
    for t in rows:
        pnl = t['profit']
        sign = '+' if pnl and pnl > 0 else ''
        status = t['status'] or 'open'
        print(f'  [{status}] {t["bot_id"][:25]} {t["symbol"]} {t["order_type"]} pnl={sign}{pnl} open={t["open_price"]} close={t["close_price"]} at={str(t["opened_at"])[:16]}')

db.close()

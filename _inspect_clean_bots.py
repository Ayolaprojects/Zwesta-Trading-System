import sqlite3, json

conn = sqlite3.connect('C:/backend/zwesta_trading.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Join user_bots + bot_credentials + broker_credentials
cur.execute("""
SELECT 
    ub.bot_id, ub.name, ub.strategy, ub.enabled, ub.status,
    ub.is_live, ub.broker_account_id, ub.symbols,
    ub.daily_profit, ub.total_profit, ub.created_at, ub.updated_at,
    bc.credential_id,
    brc.broker_name, brc.account_number, brc.server, brc.is_live as cred_live,
    brc.account_currency, brc.cached_balance, brc.cached_equity,
    brc.is_active as cred_active
FROM user_bots ub
LEFT JOIN bot_credentials bc ON bc.bot_id = ub.bot_id
LEFT JOIN broker_credentials brc ON brc.credential_id = bc.credential_id
ORDER BY ub.created_at
""")
rows = cur.fetchall()
print(f'Total bots: {len(rows)}')
print()

for r in rows:
    rs = {}
    cur2 = conn.cursor()
    cur2.execute("SELECT runtime_state FROM user_bots WHERE bot_id = ?", (r['bot_id'],))
    rs_row = cur2.fetchone()
    if rs_row and rs_row[0]:
        try:
            rs = json.loads(rs_row[0])
        except:
            pass
    
    # Detect demo-promoted
    demo_keys = {k: rs[k] for k in rs if any(x in k.lower() for x in ['demo', 'promot', 'source', 'peer'])}
    demo_id = rs.get('demoBotId') or rs.get('sourceBotId') or rs.get('behaviorProfileSourceBotId')
    mode_in_rs = rs.get('mode')
    
    print(f"BOT: {r['bot_id']}")
    print(f"  name={r['name']} | strategy={r['strategy']}")
    print(f"  broker={r['broker_name']} | acct={r['account_number']} | server={r['server']}")
    print(f"  is_live(ub)={r['is_live']} | cred_live={r['cred_live']} | mode(rs)={mode_in_rs}")
    print(f"  enabled={r['enabled']} | status={r['status']}")
    print(f"  currency={r['account_currency']} | balance={r['cached_balance']} | equity={r['cached_equity']}")
    print(f"  symbols={r['symbols']}")
    print(f"  daily_profit={r['daily_profit']} | total_profit={r['total_profit']}")
    print(f"  credential_id={r['credential_id']} | cred_active={r['cred_active']}")
    print(f"  created={r['created_at']}")
    if demo_keys:
        print(f"  ** DEMO/PROMO RS KEYS: {demo_keys}")
    if demo_id:
        print(f"  ** SOURCE DEMO BOT: {demo_id}")
    print()

print()
print('=== BROKER CREDENTIALS ===')
cur.execute("""
SELECT credential_id, broker_name, account_number, server, is_live, is_active,
       account_currency, cached_balance, cached_equity, label, updated_at
FROM broker_credentials
ORDER BY created_at
""")
for cr in cur.fetchall():
    print(f"  [{cr['credential_id']}]")
    print(f"    broker={cr['broker_name']} | acct={cr['account_number']} | server={cr['server']}")
    print(f"    is_live={cr['is_live']} | is_active={cr['is_active']} | label={cr['label']}")
    print(f"    currency={cr['account_currency']} | balance={cr['cached_balance']} | equity={cr['cached_equity']}")
    print(f"    updated={cr['updated_at']}")
    print()

print()
print('=== BOT STRATEGIES (parameters) ===')
cur.execute("SELECT bot_id, strategy_name, parameters, is_active, updated_at FROM bot_strategies ORDER BY created_at")
for s in cur.fetchall():
    params = {}
    try:
        params = json.loads(s['parameters'] or '{}')
    except:
        pass
    
    demo_p = {k: params[k] for k in params if any(x in k.lower() for x in ['demo', 'promot', 'source'])}
    print(f"  bot_id={s['bot_id']} | strategy={s['strategy_name']} | is_active={s['is_active']}")
    print(f"    tradeAmount={params.get('tradeAmount')} | maxDailyLoss={params.get('maxDailyLoss')}")
    if demo_p:
        print(f"    ** DEMO params: {demo_p}")
    print()

conn.close()

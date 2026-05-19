import sqlite3, json
DB = r'C:\backend\zwesta_trading.db'
c = sqlite3.connect(DB); cur = c.cursor()
cur.execute("SELECT bot_id, runtime_state FROM user_bots")
for r in cur.fetchall():
    bid, rs = r
    d = json.loads(rs) if rs else {}
    op = d.get('open_positions', {})
    lsr = d.get('lastScanResults') or {}
    print(f'\n=== {bid} ===')
    print('  lastScanResults timestamp:', lsr.get('timestamp'))
    print('  totalScanned:', lsr.get('totalScanned'))
    print('  qualifyingOpportunities:', lsr.get('qualifyingOpportunities'))
    print('  scannerMode:', lsr.get('scannerMode'))
    print('  closedForReallocation:', lsr.get('closedForReallocation'))
    top = lsr.get('topOpportunities') or []
    print('  topOpportunities count:', len(top))
    for t in top[:3]:
        print('   ->', t)
    print('  --- open_positions detail ---')
    for k, v in op.items():
        print(f'   {k}: {json.dumps(v, default=str)[:300]}')

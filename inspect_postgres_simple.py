import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = 'postgresql://zwesta_admin:Zwesta%40Trading2026%21@localhost:5432/zwesta_trading'
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor(cursor_factory=RealDictCursor)
for bot_id in ['1780678113048', '178090663839']:
    print('\nBOT', bot_id)
    cur.execute('SELECT bot_id, user_id, name, status, enabled, daily_profit, total_profit, runtime_state, created_at, updated_at FROM user_bots WHERE bot_id = %s', (bot_id,))
    row = cur.fetchone()
    if not row:
        print('  NOT FOUND in user_bots')
    else:
        print('  user_bots row:', dict(row))
    cur.execute('SELECT COUNT(*) AS cnt, SUM(profit) AS closed_profit FROM trades WHERE bot_id = %s AND status = %s', (bot_id, 'closed'))
    tr = cur.fetchone()
    print('  closed trades count', tr['cnt'], 'closed_profit', tr['closed_profit'])
    cur.execute('SELECT COUNT(*) AS cnt FROM trades WHERE bot_id = %s AND status = %s', (bot_id, 'open'))
    op = cur.fetchone()
    print('  open trades count', op['cnt'])
conn.close()

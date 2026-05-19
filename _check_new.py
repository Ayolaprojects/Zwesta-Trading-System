import sqlite3
c = sqlite3.connect('C:/backend/zwesta_trading.db')
rows = c.execute(
    "SELECT trade_id, symbol, order_type, volume, price, profit, ticket, status, time_open "
    "FROM trades WHERE bot_id = ? ORDER BY created_at DESC",
    ('bot_1777949277150',)
).fetchall()
for r in rows:
    print(r)

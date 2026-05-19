"""Clear phantom open positions whose tickets are already in tradeHistory as closed."""
import json, sqlite3
from datetime import datetime
DB = r'C:\backend\zwesta_trading.db'
NOW = datetime.now().isoformat()
c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
cur = c.cursor()

for r in cur.execute("SELECT bot_id, runtime_state FROM user_bots WHERE broker_account_id LIKE 'Binance_%'").fetchall():
    bid = r['bot_id']
    s = json.loads(r['runtime_state'] or '{}')
    open_pos = s.get('open_positions') or {}
    history = s.get('tradeHistory') or []
    closed_tickets = {str(t.get('ticket')) for t in history if str(t.get('status') or '').lower() == 'closed'}
    removed = []
    for tk in list(open_pos.keys()):
        if str(tk) in closed_tickets:
            removed.append(tk)
            del open_pos[tk]
    if removed:
        s['open_positions'] = open_pos
        cur.execute("UPDATE user_bots SET runtime_state=?, updated_at=? WHERE bot_id=?",
                    (json.dumps(s), NOW, bid))
        print(f"[CLEAN] {bid}: removed phantom open_positions: {removed}")
    else:
        print(f"[CLEAN] {bid}: no phantoms ({len(open_pos)} open)")

c.commit(); c.close()

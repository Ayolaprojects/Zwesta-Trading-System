"""Reset stale watermark/drawdown state and managementState on Binance bots."""
import json, sqlite3
from datetime import datetime
DB = r'C:\backend\zwesta_trading.db'
USER = '8e74db37-fd1e-4c57-87c4-ad3b64012ecf'
NOW = datetime.now().isoformat()
c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
cur = c.cursor()

current_balance = 4109.27  # from earlier connect log
for r in cur.execute("SELECT bot_id, runtime_state FROM user_bots WHERE broker_account_id LIKE 'Binance_%' AND user_id=?", (USER,)).fetchall():
    bid = r['bot_id']
    s = json.loads(r['runtime_state'] or '{}')
    before = {
        'accountEquityHighWatermark': s.get('accountEquityHighWatermark'),
        'managementState': s.get('managementState'),
        'drawdownPauseUntil': s.get('drawdownPauseUntil'),
    }
    # Rebase watermark to current balance, clear pause, normal state
    s['accountEquityHighWatermark'] = current_balance
    s['accountEquity'] = current_balance
    s['accountBalance'] = current_balance
    s['drawdownPauseUntil'] = None
    s['managementState'] = 'normal'
    s['consecutiveLosses'] = 0
    s['effectiveSignalThreshold'] = 50  # ensure not None
    # Keep the manual threshold + autoSwitch off
    s['signalThreshold'] = 50
    s['signalThresholdMode'] = 'manual'
    s['autoSwitch'] = False
    cur.execute("UPDATE user_bots SET runtime_state=?, updated_at=? WHERE bot_id=?",
                (json.dumps(s), NOW, bid))
    print(f"[RESET] {bid}: before={before}")

c.commit(); c.close()
print('Done.')

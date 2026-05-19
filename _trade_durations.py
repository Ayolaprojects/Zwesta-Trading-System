import requests
from datetime import datetime

BASE = 'http://148.113.5.39:9000'
lr = requests.post(f'{BASE}/api/user/login', json={'email':'zwexman@gmail.com','password':'Zwesta1985'}, timeout=10)
SH = {'X-Session-Token': lr.json().get('session_token','')}

for bot_id in ['bot_1779185407301','bot_1779197221415','bot_1779201336253','AZE BOT']:
    r = requests.get(f'{BASE}/api/bot/config/{requests.utils.quote(bot_id)}', headers=SH, timeout=10)
    cfg = r.json().get('config', {})
    th = cfg.get('tradeHistory') or []
    print(f'=== {bot_id} (last 8 trades) ===')
    durations = []
    for t in th[-8:]:
        entry = str(t.get('entryTime') or t.get('time_open') or '')[:19]
        exit_ = str(t.get('exitTime') or t.get('time_close') or '')[:19]
        profit = t.get('profit', 0)
        symbol = t.get('symbol', '')
        status = t.get('status', '')
        close_reason = t.get('closeReason') or t.get('close_reason') or t.get('exitReason') or ''
        dur_str = '?'
        dur_mins = None
        if entry and exit_:
            try:
                e1 = datetime.fromisoformat(entry)
                e2 = datetime.fromisoformat(exit_)
                dur_mins = int((e2 - e1).total_seconds() / 60)
                dur_str = f'{dur_mins}m'
                durations.append(dur_mins)
            except:
                pass
        print(f'  {symbol:12} profit={profit:8.2f}  dur={dur_str:5}  status={status:8}  reason={close_reason}')

    if durations:
        avg = sum(durations) / len(durations)
        print(f'  >> Avg duration: {avg:.0f}m, min={min(durations)}m, max={max(durations)}m')

    pp = cfg.get('profitProtection') or {}
    print(f'  profitProtection.minimumHoldMinutes:   {pp.get("minimumHoldMinutes")}')
    print(f'  profitProtection.retraceClosePercent:  {pp.get("retraceClosePercent")}')
    print(f'  profitProtection.breakEvenLockEnabled: {pp.get("breakEvenLockEnabled")}')
    print(f'  profitProtection.switchOnReversal:     {pp.get("switchOnReversal")}')
    print(f'  drawdownPauseUntil: {cfg.get("drawdownPauseUntil")}')
    print(f'  drawdownPauseHours: {cfg.get("drawdownPauseHours")}')
    print(f'  tradingInterval/pollInterval: {cfg.get("tradingInterval")} / {cfg.get("pollInterval")}')
    print()

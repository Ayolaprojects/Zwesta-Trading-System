"""
Check bot_1781308107019 status on VPS and attempt to update its config.
"""
import urllib.request, json

VPS = 'http://148.113.5.39:9000'
TOKEN = '435f1a5e49f0d4e900637293356d392b3afd63cd'
BOT_ID = 'bot_1781308107019'
HEADERS = {'Content-Type': 'application/json', 'Authorization': f'Bearer {TOKEN}'}

def api(method, path, data=None, timeout=15):
    url = VPS + path
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {'error': str(e)}
    except Exception as e:
        return None, str(e)

print(f"=== VPS Bot Check: {VPS} ===")

# Check all bot statuses on VPS
status, data = api('GET', '/api/bot/status-public')
print(f"Public status HTTP {status}")
if status == 200:
    bots = data.get('bots', [])
    print(f"Total bots: {len(bots)}")
    for b in bots:
        bid = b.get('botId', '')
        if '1781308107019' in bid:
            print(f"  FOUND: {bid} | status={b.get('status')} | profit={b.get('profit')} | trades={b.get('totalTrades')}")
            print(f"         symbols={b.get('symbols')}")
    print("All bot IDs:", [b.get('botId') for b in bots])

# Try to get bot config
print()
status2, cfg = api('GET', f'/api/bot/config/{BOT_ID}')
print(f"Config GET HTTP {status2}: {json.dumps(cfg)[:400]}")

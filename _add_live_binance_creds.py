"""
Add Binance LIVE credentials (spot and/or futures) to the VPS.
Fill in your live API key and secret below, then run.
VPS whitelisted IP: 148.113.5.39

Required Binance API permissions:
  - Enable Reading
  - Enable Spot & Margin Trading   (for spot live)
  - Enable Futures                 (for futures live)
  - IP Restriction: 148.113.5.39
"""
import urllib.request, json, sys
sys.path.insert(0, r'C:\backend')
from credential_crypto import decrypt_secret
import sqlite3

BASE = 'http://148.113.5.39:9000'

# ============================================================
# FILL IN YOUR LIVE BINANCE API KEY HERE
# ============================================================
LIVE_API_KEY    = ''   # e.g. 'AbCdEfGhIjKl...'
LIVE_API_SECRET = ''   # e.g. 'xyzABC123...'
# ============================================================

if not LIVE_API_KEY or not LIVE_API_SECRET:
    print("ERROR: Fill in LIVE_API_KEY and LIVE_API_SECRET above before running.")
    sys.exit(1)

# Login
login = json.dumps({'email': 'zwexman@gmail.com', 'password': 'Zwesta1985'}).encode()
req = urllib.request.Request(BASE + '/api/user/login', data=login, headers={'Content-Type': 'application/json'})
token = json.loads(urllib.request.urlopen(req, timeout=10).read().decode())['session_token']
H = {'X-Session-Token': token, 'Content-Type': 'application/json'}

def post_cred(label, server, is_live):
    body = json.dumps({
        'broker_name': 'Binance',
        'api_key': LIVE_API_KEY,
        'api_secret': LIVE_API_SECRET,
        'server': server,
        'is_live': is_live,
        'label': label,
    }).encode()
    req = urllib.request.Request(BASE + '/api/broker/credentials', data=body, headers=H)
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
        cid = r.get('credential', {}).get('credential_id', '?')
        print(f"  {label}: OK → credential_id={cid}")
        return cid
    except urllib.error.HTTPError as e:
        print(f"  {label}: ERROR {e.code} — {e.read().decode()[:200]}")
    except Exception as e:
        print(f"  {label}: TIMEOUT/ERROR — {e}")
    return None

print("Adding live credentials...")
spot_live_id = post_cred('Binance Spot Live', server='spot', is_live=True)
futures_live_id = post_cred('Binance Futures Live', server='futures', is_live=True)

print()
if spot_live_id:
    print(f"Spot LIVE credential:    {spot_live_id}")
    print("  → Create bot: python _create_live_bot.py SPOT", spot_live_id)
if futures_live_id:
    print(f"Futures LIVE credential: {futures_live_id}")
    print("  → Create bot: python _create_live_bot.py FUTURES", futures_live_id)

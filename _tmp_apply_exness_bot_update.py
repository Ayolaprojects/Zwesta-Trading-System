import json
import sys
import time

import requests

BASE = 'http://148.113.5.39:9000'
EMAIL = 'zwexman@gmail.com'
PASSWORD = 'Zwesta1985'
BOT_ID = 'bot_1778879535397'
PAYLOAD = {
    'signalThreshold': 55,
    'managementProfile': 'balanced',
    'postCloseCooldownMinutes': 20,
    'postLossSameDirectionCooldownMinutes': 20,
    'tradeAmount': 125.0,
    'maxOpenPositions': 1,
    'maxPositionsPerSymbol': 1,
}

try:
    login = requests.post(
        f'{BASE}/api/user/login',
        json={'email': EMAIL, 'password': PASSWORD},
        timeout=30,
    )
    print('login_status', login.status_code)
    print(login.text[:300])
    login.raise_for_status()
    token = login.json()['session_token']
    headers = {'X-Session-Token': token, 'Content-Type': 'application/json'}

    resp = None
    for attempt in range(6):
        resp = requests.put(
            f'{BASE}/api/bot/config/{BOT_ID}',
            headers=headers,
            json=PAYLOAD,
            timeout=120,
        )
        print('update_attempt', attempt + 1, 'status', resp.status_code)
        print(resp.text[:2000])
        if resp.ok:
            break
        body = (resp.text or '').lower()
        if resp.status_code == 500 and 'database is locked' in body and attempt < 5:
            time.sleep(10)
            continue
        resp.raise_for_status()

    if resp is None:
        raise RuntimeError('Update request did not run')
    resp.raise_for_status()
except Exception as exc:
    print(type(exc).__name__, str(exc))
    sys.exit(1)

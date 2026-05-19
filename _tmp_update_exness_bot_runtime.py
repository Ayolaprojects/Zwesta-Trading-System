import json
import time
from typing import Any

import requests

BASE = 'http://148.113.5.39:9000'
EMAIL = 'zwexman@gmail.com'
PASSWORD = 'Zwesta1985'
BOT_ID = 'bot_1778879535397'

UPDATE_PAYLOAD = {
    'signalThreshold': 55,
    'managementProfile': 'balanced',
    'postCloseCooldownMinutes': 20,
    'postLossSameDirectionCooldownMinutes': 20,
    'tradeAmount': 125.0,
    'maxOpenPositions': 1,
    'maxPositionsPerSymbol': 1,
}


def login() -> dict[str, str]:
    resp = requests.post(
        f'{BASE}/api/user/login',
        json={'email': EMAIL, 'password': PASSWORD},
        timeout=30,
    )
    resp.raise_for_status()
    token = resp.json()['session_token']
    return {'X-Session-Token': token, 'Content-Type': 'application/json'}


def get_bot_status(headers: dict[str, str]) -> dict[str, Any] | None:
    resp = requests.get(f'{BASE}/api/bot/status', headers=headers, timeout=30)
    resp.raise_for_status()
    bots = resp.json().get('bots', [])
    for bot in bots:
        if bot.get('botId') == BOT_ID:
            return bot
    return None


def stop_bot(headers: dict[str, str]) -> None:
    try:
        resp = requests.post(f'{BASE}/api/bot/stop/{BOT_ID}', headers=headers, timeout=90)
        print('stop', resp.status_code, resp.text[:300])
    except requests.exceptions.ReadTimeout:
        print('stop request timed out; polling status')


def wait_for_status(headers: dict[str, str], expected_active: bool, timeout_seconds: int) -> dict[str, Any]:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        bot = get_bot_status(headers)
        if bot is None:
            raise RuntimeError(f'Bot {BOT_ID} not found in status payload')
        is_active = str(bot.get('status') or '').lower() == 'active'
        print('status', bot.get('status'), 'open', len(bot.get('openPositions') or []), 'pause', bot.get('pauseReason'))
        if is_active == expected_active:
            return bot
        time.sleep(5)
    raise TimeoutError(f'Bot did not reach expected_active={expected_active} within {timeout_seconds}s')


def update_bot(headers: dict[str, str]) -> None:
    resp = requests.put(
        f'{BASE}/api/bot/config/{BOT_ID}',
        headers=headers,
        json=UPDATE_PAYLOAD,
        timeout=90,
    )
    print('update', resp.status_code, resp.text[:600])
    resp.raise_for_status()


def start_bot(headers: dict[str, str]) -> None:
    resp = requests.post(
        f'{BASE}/api/bot/start',
        headers=headers,
        json={'botId': BOT_ID},
        timeout=90,
    )
    print('start', resp.status_code, resp.text[:400])
    resp.raise_for_status()


def get_bot_config(headers: dict[str, str]) -> dict[str, Any]:
    resp = requests.get(f'{BASE}/api/bot/config/{BOT_ID}', headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json().get('config', {})


def main() -> None:
    headers = login()
    before = get_bot_status(headers)
    print('before', json.dumps({
        'status': before.get('status') if before else None,
        'openPositions': len(before.get('openPositions') or []) if before else None,
        'signalThreshold': before.get('signalThreshold') if before else None,
        'managementProfile': before.get('managementProfile') if before else None,
    }, indent=2))

    stop_bot(headers)
    wait_for_status(headers, expected_active=False, timeout_seconds=180)
    update_bot(headers)
    start_bot(headers)
    wait_for_status(headers, expected_active=True, timeout_seconds=180)

    cfg = get_bot_config(headers)
    after = get_bot_status(headers)
    print('after', json.dumps({
        'status': after.get('status') if after else None,
        'signalThreshold': cfg.get('signalThreshold'),
        'managementProfile': cfg.get('managementProfile'),
        'postCloseCooldownMinutes': cfg.get('postCloseCooldownMinutes'),
        'postLossSameDirectionCooldownMinutes': cfg.get('postLossSameDirectionCooldownMinutes'),
        'tradeAmount': cfg.get('tradeAmount'),
        'effectiveTradeAmount': after.get('effectiveTradeAmount') if after else None,
        'pauseReason': after.get('pauseReason') if after else None,
    }, indent=2))


if __name__ == '__main__':
    main()

"""Retry profitProtection PATCH for the 4 Binance bots that got 409 (still stopping)."""
import requests, time

VPS     = 'http://148.113.5.39:9000'
USER_ID = '8e74db37-fd1e-4c57-87c4-ad3b64012ecf'

GOOD_PP = {
    'enabled': True, 'activationPercent': 3.0, 'activationMinProfit': 2.0,
    'portfolioActivationMinProfit': 3.0, 'breakEvenBufferProfit': 10.0,
    'breakEvenActivationShare': 0.30, 'minLockedProfit': 5.0,
    'retraceClosePercent': 10.0, 'peakProfitHardLockShare': 0.90,
    'closeLosingPositionsWithProfitablePeers': True, 'loserRotationMinLoss': 0.0,
    'marginTakeProfitPercent': 30.0, 'switchOnReversal': True,
    'adaptiveByVolatility': True, 'breakEvenLockEnabled': True,
    'zeroLossLockEnabled': True, 'minimumHoldMinutes': 1.0,
    'protectedSymbolCooldownMinutes': 5.0,
}

BINANCE_BOTS = [
    'bot_1779029733318_cf548079',
    'bot_1779029679564_b8070b61',
    'bot_1778971251604',
    'bot_1778970971191',
]

r = requests.post(f'{VPS}/api/user/login',
                  json={'email': 'zwexman@gmail.com', 'password': 'Zwesta1985'},
                  timeout=15)
TOKEN   = r.json()['session_token']
HEADERS = {'X-Session-Token': TOKEN}
print(f"Logged in.\n")

for bot_id in BINANCE_BOTS:
    print(f"--- {bot_id}")

    # Get config
    cfg_r = requests.get(f'{VPS}/api/bot/config/{bot_id}', headers=HEADERS, timeout=15)
    bot_cfg = cfg_r.json().get('config', {})
    cred_id = bot_cfg.get('credentialId')

    # Stop
    requests.post(f'{VPS}/api/bot/stop/{bot_id}', headers=HEADERS, timeout=15)
    print(f"  Stopped. Waiting 20s for thread to exit...")
    time.sleep(20)

    # PATCH
    patch_payload = {
        'credentialId': cred_id,
        'profitProtection': GOOD_PP,
        'strategy':          bot_cfg.get('strategy'),
        'symbols':           bot_cfg.get('symbols'),
        'managementProfile': bot_cfg.get('managementProfile'),
        'signalThreshold':   bot_cfg.get('signalThreshold'),
        'signalThresholdMode': bot_cfg.get('signalThresholdMode'),
        'maxOpenPositions':  bot_cfg.get('maxOpenPositions'),
        'tradeAmount':       bot_cfg.get('tradeAmount'),
        'dynamicSizing':     bot_cfg.get('dynamicSizing'),
        'intelligentScanner': bot_cfg.get('intelligentScanner'),
    }
    patch_r = requests.patch(f'{VPS}/api/bot/config/{bot_id}',
                              headers=HEADERS, json=patch_payload, timeout=60)
    if patch_r.status_code == 200:
        print(f"  [OK] PATCH succeeded - profitProtection updated on VPS")
    else:
        print(f"  [!!] PATCH failed: {patch_r.status_code} - {patch_r.text[:200]}")

    # Restart
    time.sleep(2)
    start_r = requests.post(f'{VPS}/api/bot/start', headers=HEADERS,
                             json={'botId': bot_id, 'user_id': USER_ID}, timeout=20)
    if start_r.status_code == 200:
        print(f"  [OK] Restarted")
    else:
        print(f"  [!!] Restart: {start_r.status_code} - {start_r.text[:80]}")

print("\nDone.")

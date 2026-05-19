"""
Pushes the $60+ profitProtection config to all VPS bots via the PATCH endpoint.

Strategy:
  1. For EACH bot:
     a. GET current config
     b. Stop bot
     c. PATCH with updated profitProtection
     d. Restart bot

For Binance bots the PATCH triggers a Binance connect() check.
The demo spot key works for testnet.binance.vision so it should succeed.
If a Binance bot PATCH times out, the bot is still restarted with the old config
and we note it for manual follow-up.
"""
import requests, json, time

VPS     = 'http://148.113.5.39:9000'
USER_ID = '8e74db37-fd1e-4c57-87c4-ad3b64012ecf'

GOOD_PP = {
    'enabled': True,
    'activationPercent': 3.0,
    'activationMinProfit': 2.0,
    'portfolioActivationMinProfit': 3.0,
    'breakEvenBufferProfit': 10.0,
    'breakEvenActivationShare': 0.30,
    'minLockedProfit': 5.0,
    'retraceClosePercent': 10.0,
    'peakProfitHardLockShare': 0.90,
    'closeLosingPositionsWithProfitablePeers': True,
    'loserRotationMinLoss': 0.0,
    'marginTakeProfitPercent': 30.0,
    'switchOnReversal': True,
    'adaptiveByVolatility': True,
    'breakEvenLockEnabled': True,
    'zeroLossLockEnabled': True,
    'minimumHoldMinutes': 1.0,
    'protectedSymbolCooldownMinutes': 5.0,
}

# Auth
r = requests.post(f'{VPS}/api/user/login',
                  json={'email': 'zwexman@gmail.com', 'password': 'Zwesta1985'},
                  timeout=15)
TOKEN   = r.json()['session_token']
HEADERS = {'X-Session-Token': TOKEN}
ADMIN   = {'Authorization': 'Bearer zwesta_live_api_key_2026_secure'}
print(f"Logged in. Token: {TOKEN[:16]}...\n")

# Get all active bots
bots_r = requests.get(f'{VPS}/api/user/{USER_ID}/bots', headers=HEADERS, timeout=15)
bots   = bots_r.json().get('bots', [])
bot_ids = [b['bot_id'] for b in bots]
print(f"Found {len(bot_ids)} bots: {bot_ids}\n")

results = {}

for bot_id in bot_ids:
    print(f"{'='*55}")
    print(f"Bot: {bot_id}")

    # 1. GET current config
    try:
        cfg_r = requests.get(f'{VPS}/api/bot/config/{bot_id}', headers=HEADERS, timeout=15)
        if cfg_r.status_code != 200:
            print(f"  [!!] GET config failed: {cfg_r.status_code}")
            results[bot_id] = 'GET_FAILED'
            continue
        bot_cfg = cfg_r.json().get('config', {})
        old_beb = bot_cfg.get('profitProtection', {}).get('breakEvenBufferProfit', '?')
        cred_id = bot_cfg.get('credentialId')
        print(f"  bEB was: {old_beb}")
    except Exception as e:
        print(f"  [!!] GET config error: {e}")
        results[bot_id] = 'GET_ERROR'
        continue

    # 2. Stop bot
    try:
        stop_r = requests.post(f'{VPS}/api/bot/stop/{bot_id}', headers=HEADERS, timeout=15)
        if stop_r.status_code == 200:
            print(f"  [OK] Stopped")
        else:
            print(f"  [!!] Stop failed: {stop_r.status_code} - {stop_r.text[:80]}")
    except Exception as e:
        print(f"  [!!] Stop error: {e}")

    time.sleep(3)

    # 3. PATCH with updated profitProtection
    patch_payload = {
        'credentialId': cred_id,
        'profitProtection': GOOD_PP,
        # Forward the essential config fields so the PATCH doesn't reset them
        'strategy':         bot_cfg.get('strategy'),
        'symbols':          bot_cfg.get('symbols'),
        'managementProfile':bot_cfg.get('managementProfile'),
        'signalThreshold':  bot_cfg.get('signalThreshold'),
        'signalThresholdMode': bot_cfg.get('signalThresholdMode'),
        'maxOpenPositions': bot_cfg.get('maxOpenPositions'),
        'tradeAmount':      bot_cfg.get('tradeAmount'),
        'dynamicSizing':    bot_cfg.get('dynamicSizing'),
        'intelligentScanner': bot_cfg.get('intelligentScanner'),
    }
    try:
        patch_r = requests.patch(
            f'{VPS}/api/bot/config/{bot_id}',
            headers=HEADERS,
            json=patch_payload,
            timeout=45,   # Binance connect can take a while
        )
        if patch_r.status_code == 200:
            print(f"  [OK] PATCH OK - profitProtection updated on VPS")
            results[bot_id] = 'PATCHED'
        else:
            print(f"  [!!] PATCH failed: {patch_r.status_code} - {patch_r.text[:120]}")
            results[bot_id] = 'PATCH_FAILED'
    except requests.exceptions.Timeout:
        print(f"  [~~] PATCH timed out (Binance connect) - will restart with old config")
        results[bot_id] = 'PATCH_TIMEOUT'
    except Exception as e:
        print(f"  [!!] PATCH error: {e}")
        results[bot_id] = 'PATCH_ERROR'

    time.sleep(2)

    # 4. Restart bot
    try:
        start_r = requests.post(f'{VPS}/api/bot/start',
                                headers=HEADERS,
                                json={'botId': bot_id, 'user_id': USER_ID},
                                timeout=20)
        if start_r.status_code == 200:
            print(f"  [OK] Restarted")
        else:
            print(f"  [!!] Restart failed: {start_r.status_code} - {start_r.text[:80]}")
    except Exception as e:
        print(f"  [!!] Restart error: {e}")

print(f"\n{'='*55}")
print("SUMMARY")
print(f"{'='*55}")
for bot_id, result in results.items():
    icon = '[OK]' if result == 'PATCHED' else '[!!]'
    print(f"  {icon} {bot_id}: {result}")

patched = [k for k, v in results.items() if v == 'PATCHED']
failed  = [k for k, v in results.items() if v != 'PATCHED']
print(f"\nPatched: {len(patched)}  |  Not patched: {len(failed)}")
if failed:
    print(f"\nNot patched (may need VPS backend restart): {failed}")
    print("  → To fix these permanently: RDP to 148.113.5.39, replace C:\\backend\\multi_broker_backend_updated.py,")
    print("    and restart the backend. The new code enforces DEFAULT values as floor on every bot load.")

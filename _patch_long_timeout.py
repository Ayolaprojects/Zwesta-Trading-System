"""
Try PATCH with a very long timeout to see if Binance validation eventually completes.
Try changing managementProfile from fast_growth to balanced to avoid the recovery-mode Binance restriction.
"""
import requests, time

VPS = 'http://148.113.5.39:9000'
response = requests.post(f'{VPS}/api/user/login',
    json={'email': 'zwexman@gmail.com', 'password': 'Zwesta1985'}, timeout=15)
data = response.json()
TOKEN = data['session_token']
USER_ID = data.get('user_id') or data.get('userId') or data.get('id')
HEADERS = {'X-Session-Token': TOKEN, 'Content-Type': 'application/json'}
print('user_id:', USER_ID)

# Try PATCH with balanced profile (which doesn't restrict Binance in recovery mode as aggressively)
# Using a very long timeout to allow Binance testnet validation to complete
PATCH = {
    'managementProfile': 'balanced',
    'managementMode': 'manual',
    'signalThresholdMode': 'manual',
    'allowedVolatility': ['Low', 'Medium', 'High'],
}

for bot_id in ['bot_1778970971191', 'bot_1778971251604']:
    print(f'\n--- {bot_id} ---')
    
    # Stop the bot first
    status_r = requests.get(f'{VPS}/api/bot/config/' + bot_id, headers=HEADERS, timeout=10)
    enabled = status_r.json().get('config', {}).get('enabled', True)
    print(f'enabled: {enabled}')
    
    if enabled:
        print('Stopping...')
        stop_r = requests.post(f'{VPS}/api/bot/stop/' + bot_id,
            headers=HEADERS, json={'user_id': USER_ID}, timeout=20)
        print(f'Stop: {stop_r.status_code}')
        if stop_r.status_code != 200:
            print('Could not stop, skipping.')
            continue
        time.sleep(5)
    
    print(f'Sending PATCH (timeout=120s)...')
    t0 = time.time()
    try:
        r = requests.patch(f'{VPS}/api/bot/config/' + bot_id,
            headers=HEADERS, json=PATCH, timeout=120)
        elapsed = time.time() - t0
        print(f'PATCH ({elapsed:.1f}s): {r.status_code} {r.text[:300]}')
    except Exception as e:
        elapsed = time.time() - t0
        print(f'PATCH ({elapsed:.1f}s) ERROR: {e}')

print('\nDone.')

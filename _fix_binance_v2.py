"""
Fix Binance bots: update config + restart for bots that are already stopped.
For bots still running: stop → update → restart.
"""
import requests, json, time

VPS = 'http://148.113.5.39:9000'
response = requests.post(f'{VPS}/api/user/login',
    json={'email': 'zwexman@gmail.com', 'password': 'Zwesta1985'}, timeout=15)
data = response.json()
TOKEN = data['session_token']
USER_ID = data.get('user_id') or data.get('userId') or data.get('id')
HEADERS = {'X-Session-Token': TOKEN, 'Content-Type': 'application/json'}
print('Authenticated. user_id:', USER_ID)

BINANCE_BOTS = ['bot_1778970971191', 'bot_1778971251604']

new_config = {
    'managementMode': 'manual',
    'signalThresholdMode': 'manual',
    'allowedVolatility': ['Low', 'Medium', 'High'],
}

for bot_id in BINANCE_BOTS:
    print('\n=== ' + bot_id + ' ===')
    
    # Check current status
    status_r = requests.get(f'{VPS}/api/bot/status/' + bot_id, headers=HEADERS, timeout=10)
    if status_r.status_code == 200:
        current_status = status_r.json().get('status', 'unknown')
        print('  Current status:', current_status)
    else:
        current_status = 'unknown'
        print('  Status check failed:', status_r.status_code)
    
    # Stop if running
    if current_status not in ('inactive', 'stopped'):
        print('Stopping bot...')
        stop_r = requests.post(f'{VPS}/api/bot/stop/' + bot_id,
            headers=HEADERS, json={'user_id': USER_ID}, timeout=20)
        print('  Stop:', stop_r.status_code, stop_r.text[:80])
        if stop_r.status_code != 200:
            print('  ERROR stopping, skipping.')
            continue
        time.sleep(10)
    else:
        print('  Bot is already stopped.')
        time.sleep(2)
    
    # Update config
    print('Updating config...')
    update_r = requests.put(f'{VPS}/api/bot/config/' + bot_id,
        headers=HEADERS, json=new_config, timeout=60)
    print('  Update:', update_r.status_code, update_r.text[:200])
    
    if update_r.status_code not in (200, 201):
        print('  WARNING: config update failed')
        # Still try to restart
    
    time.sleep(3)
    
    # Start bot
    print('Starting bot...')
    start_r = requests.post(f'{VPS}/api/bot/start',
        headers=HEADERS, json={'botId': bot_id, 'user_id': USER_ID}, timeout=30)
    print('  Start:', start_r.status_code, start_r.text[:200])

print('\n=== Done ===')

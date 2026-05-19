"""
Fix Binance bots: stop → update managementMode to manual → restart.
This bypasses the assisted effective-computation that restricts allowedVolatility to ['Very Low', 'Low'].
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

for bot_id in BINANCE_BOTS:
    print('\n=== ' + bot_id + ' ===')
    
    # Step 1: Stop the bot
    print('Stopping bot...')
    stop_r = requests.post(f'{VPS}/api/bot/stop/' + bot_id,
        headers=HEADERS, json={'user_id': USER_ID}, timeout=15)
    print('  Stop status:', stop_r.status_code, stop_r.text[:100])
    
    if stop_r.status_code != 200:
        print('  ERROR stopping bot, skipping.')
        continue
    
    # Wait for bot to stop
    time.sleep(8)
    
    # Step 2: Update configuration
    print('Updating config...')
    new_config = {
        'managementMode': 'manual',
        'signalThresholdMode': 'manual',
        'allowedVolatility': ['Low', 'Medium', 'High'],
    }
    update_r = requests.put(f'{VPS}/api/bot/config/' + bot_id,
        headers=HEADERS, json=new_config, timeout=30)
    print('  Update status:', update_r.status_code, update_r.text[:200])
    
    if update_r.status_code != 200:
        print('  WARNING: config update failed')
    
    # Step 3: Restart the bot
    print('Starting bot...')
    start_r = requests.post(f'{VPS}/api/bot/start',
        headers=HEADERS, json={'botId': bot_id, 'user_id': USER_ID}, timeout=20)
    print('  Start status:', start_r.status_code, start_r.text[:200])

print('\n=== Done ===')
print('Next cycle should show Binance bots trading without volatility block.')

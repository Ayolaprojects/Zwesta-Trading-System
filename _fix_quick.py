"""Quick fix: patch both Binance bots (stop second one, then patch both, then restart both)."""
import requests, time

VPS = 'http://148.113.5.39:9000'
response = requests.post(f'{VPS}/api/user/login',
    json={'email': 'zwexman@gmail.com', 'password': 'Zwesta1985'}, timeout=15)
data = response.json()
TOKEN = data['session_token']
USER_ID = data.get('user_id') or data.get('userId') or data.get('id')
HEADERS = {'X-Session-Token': TOKEN, 'Content-Type': 'application/json'}
print('user_id:', USER_ID)

PATCH = {
    'managementMode': 'manual',
    'signalThresholdMode': 'manual',
    'allowedVolatility': ['Low', 'Medium', 'High'],
}

# Bot 1 is already stopped - patch it
print('\n-- bot_1778970971191 (already stopped) --')
r = requests.patch(f'{VPS}/api/bot/config/bot_1778970971191', headers=HEADERS, json=PATCH, timeout=30)
print('PATCH:', r.status_code, r.text[:300])

# Bot 2 - stop it first
print('\n-- bot_1778971251604 (stopping) --')
stop_r = requests.post(f'{VPS}/api/bot/stop/bot_1778971251604', headers=HEADERS, json={'user_id': USER_ID}, timeout=20)
print('STOP:', stop_r.status_code, stop_r.text[:100])
time.sleep(8)
r2 = requests.patch(f'{VPS}/api/bot/config/bot_1778971251604', headers=HEADERS, json=PATCH, timeout=30)
print('PATCH:', r2.status_code, r2.text[:300])

# Restart both
print('\n-- Restarting both --')
for bot_id in ['bot_1778970971191', 'bot_1778971251604']:
    start_r = requests.post(f'{VPS}/api/bot/start', headers=HEADERS,
        json={'botId': bot_id, 'user_id': USER_ID}, timeout=30)
    print(bot_id, 'START:', start_r.status_code, start_r.text[:150])
    time.sleep(2)

print('\nDone.')

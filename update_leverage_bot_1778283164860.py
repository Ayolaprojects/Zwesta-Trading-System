import requests

VPS = 'http://148.113.5.39:9000'

# Login to the VPS
response = requests.post(f'{VPS}/api/user/login', json={
    'email': 'zwexman@gmail.com',
    'password': 'Zwesta1985'
}, timeout=15)

TOKEN = response.json()['session_token']
HEADERS = {'X-Session-Token': TOKEN}

# Bot ID to update
bot_id = 'bot_1778283164860'

# New leverage value
new_leverage = 20  # Increase leverage to 20x

# Update leverage for the bot
update_response = requests.put(f'{VPS}/api/bot/leverage/{bot_id}', json={'leverage': new_leverage}, headers=HEADERS, timeout=15)

if update_response.status_code == 200:
    print(f"Leverage for bot {bot_id} updated to {new_leverage}x successfully.")
else:
    print(f"Failed to update leverage for bot {bot_id}. Status code: {update_response.status_code}")
    print(update_response.text)
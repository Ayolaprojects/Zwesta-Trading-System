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
bot_id = 'bot_1778283367754'

# New configuration
new_config = {
    'riskPerTrade': 30.0,  # Match successful bot
    'maxDailyLoss': 160.0,  # Match successful bot
    'signalThreshold': 0.5,  # Lower threshold for more frequent trades
    'symbols': ['BTCUSDT', 'ETHBTC', 'ETHUSDT', 'SOLUSDT', 'SOLBNB', 'BNBUSDT', 'BNBETH'],  # Expand symbols
    'managementProfile': 'fast_growth',  # Aggressive trading
    'maxOpenPositions': 8  # Double trading frequency
}

# Update bot configuration
update_response = requests.put(f'{VPS}/api/bot/config/{bot_id}', json=new_config, headers=HEADERS, timeout=15)

if update_response.status_code == 200:
    print(f"Bot {bot_id} updated successfully.")
else:
    print(f"Failed to update bot {bot_id}. Status code: {update_response.status_code}")
    print(update_response.text)
import requests
import time

VPS = 'http://148.113.5.39:9000'

# Login to the VPS
response = requests.post(f'{VPS}/api/user/login', json={
    'email': 'zwexman@gmail.com',
    'password': 'Zwesta1985'
}, timeout=15)

TOKEN = response.json()['session_token']
HEADERS = {'X-Session-Token': TOKEN}

# Bot ID to stop and update
bot_id = 'bot_1778283367754'

# Stop the bot
stop_response = requests.post(f'{VPS}/api/bot/stop/{bot_id}', headers=HEADERS, timeout=15)

if stop_response.status_code == 200:
    print(f"Bot {bot_id} stopped successfully. Checking status...")

    # Check bot status until it becomes inactive
    for _ in range(10):  # Retry up to 10 times
        status_response = requests.get(f'{VPS}/api/bot/status/{bot_id}', headers=HEADERS, timeout=15)
        if status_response.status_code == 200:
            status = status_response.json().get('status', '')
            print(f"Current status: {status}")
            if status == 'inactive':
                break
        time.sleep(5)  # Wait before retrying
    else:
        print(f"Bot {bot_id} did not become inactive. Cannot proceed with update.")
        exit()

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
else:
    print(f"Failed to stop bot {bot_id}. Status code: {stop_response.status_code}")
    print(stop_response.text)
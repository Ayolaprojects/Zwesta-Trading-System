import requests
import json

VPS = 'http://148.113.5.39:9000'

# Login to the VPS
response = requests.post(f'{VPS}/api/user/login', json={
    'email': 'zwexman@gmail.com',
    'password': 'Zwesta1985'
}, timeout=15)

TOKEN = response.json()['session_token']
HEADERS = {'X-Session-Token': TOKEN}

# Bot IDs to fetch configurations for
bot_ids = ['bot_1778283164860', 'bot_1778283367754', 'bot_1778274751313']

# Fetch and print configurations
for bot_id in bot_ids:
    bot_response = requests.get(f'{VPS}/api/bot/config/{bot_id}', headers=HEADERS, timeout=10)
    config = bot_response.json().get('config', {})

    print(f"Bot ID: {bot_id}")
    print(f"  Broker: {config.get('brokerName', '?')}")
    print(f"  Trade Amount: {config.get('tradeAmount')}")
    print(f"  Risk Per Trade: {config.get('riskPerTrade')}%")
    print(f"  Max Daily Loss: {config.get('maxDailyLoss')}")
    print(f"  Symbols: {config.get('symbols')}")
    print(f"  Signal Threshold: {config.get('signalThreshold')}")
    print(f"  Management Profile: {config.get('managementProfile')}")
    print(f"  Stop Loss: {config.get('stopLoss')}")
    print(f"  Take Profit: {config.get('takeProfit')}")
    print(f"  Max Open Positions: {config.get('maxOpenPositions')}")
    print()
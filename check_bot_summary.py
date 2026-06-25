import requests
import json

# Check bot summary for this specific bot
resp = requests.get(
    'http://localhost:9000/api/bot/summary?mode=ALL',
    headers={'X-Session-Token': 'test-direct-token'},
    timeout=10
)
print(f"Status: {resp.status_code}")
data = resp.json()
for bot in data.get('bots', []):
    if '1782305458924' in str(bot.get('botId', '')):
        print(f"Bot found: {bot.get('botId')}")
        print(f"  createdAt: {bot.get('createdAt')}")
        print(f"  startTime: {bot.get('startTime')}")
        print(f"  runtimeFormatted: {bot.get('runtimeFormatted')}")
        print(f"  openPositionsCount: {bot.get('openPositionsCount')}")
        print(f"  profit: {bot.get('profit')}")
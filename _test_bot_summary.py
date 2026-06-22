import urllib.request, json, time

url = 'http://192.168.0.137:9000/api/bot/summary?mode=ALL'
headers = {
    'X-Session-Token': 'test-session-token-123',
    'Content-Type': 'application/json',
}

print(f"Starting request to {url}")
start = time.time()
try:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=120) as resp:
        elapsed = time.time() - start
        data = json.loads(resp.read().decode())
        print(f"Response in {elapsed:.1f}s")
        print('success:', data.get('success'))
        bots = data.get('bots', [])
        print('bot_count:', len(bots))
        for b in bots[:10]:
            print(f"  botId={b.get('botId')}  status={b.get('status')}  enabled={b.get('enabled')}  mode={b.get('mode')}  profit={b.get('profit')}")
except Exception as e:
    elapsed = time.time() - start
    print(f"Failed after {elapsed:.1f}s: {e}")

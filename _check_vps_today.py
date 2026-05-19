import requests, json
from collections import Counter

TOKEN = 'd2e93e00da2e04cdd815475b17a61cc6cbcdf02a75cc2a5ef9c3e9c472da3cc5'
H = {'X-Session-Token': TOKEN}

r = requests.get('http://148.113.5.39:9000/api/trades', headers=H, timeout=20)
data = r.json()
trades = data.get('trades', [])
print('Total trades:', len(trades))

dates = Counter(t.get('created_at','')[:10] for t in trades)
for d, cnt in sorted(dates.items(), reverse=True)[:7]:
    print(f'  {d}: {cnt} trades')

print()
today_trades = [t for t in trades if t.get('created_at','').startswith('2026-05-08')]
print('Today (May 8) trades:', len(today_trades))
for t in today_trades[:10]:
    print(' ', t.get('created_at','')[:19], t.get('symbol'), t.get('order_type'), 'profit='+str(t.get('profit')), 'status='+str(t.get('status')), 'bot='+str(t.get('bot_id')))

print()
# Last 5 trades overall
print('Last 5 trades overall:')
for t in trades[:5]:
    print(' ', t.get('created_at','')[:19], t.get('symbol'), t.get('order_type'), 'profit='+str(t.get('profit')), 'status='+str(t.get('status')))

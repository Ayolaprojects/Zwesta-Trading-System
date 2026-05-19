p = r'c:\backend\multi_broker_backend_updated.py'
t = open(p, 'r', encoding='utf-8').read()
old = "bot.get('effectiveSignalThreshold', bot.get('signalThreshold', 70))"
new = "bot.get('effectiveSignalThreshold', bot.get('signalThreshold', 5))"
print('count:', t.count(old))
t = t.replace(old, new)
open(p, 'w', encoding='utf-8').write(t)
print('done')

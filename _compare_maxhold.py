import re

OLD = open(r'C:\Users\zwexm\OneDrive\Documents\multi_broker_backend_updated.py', encoding='utf-8').read()
NEW = open(r'C:\backend\multi_broker_backend_updated.py', encoding='utf-8').read()

key = "'max_hold_minutes': 90"

print('=== OLD context around max_hold_minutes=90 ===')
idx = OLD.find(key)
while idx >= 0:
    print(OLD[idx-300:idx+200])
    print('---')
    idx = OLD.find(key, idx+1)

print()
print('=== NEW context around max_hold_minutes=90 ===')
idx = NEW.find(key)
while idx >= 0:
    print(NEW[idx-300:idx+200])
    print('---')
    idx = NEW.find(key, idx+1)

# Also check where max_hold_minutes is consumed
print()
print('=== How max_hold_minutes is applied (NEW) ===')
idx3 = NEW.find('max_hold_minutes > 0 and time_in_position')
print(NEW[idx3-500:idx3+500])

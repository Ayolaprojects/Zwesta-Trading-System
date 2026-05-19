with open('C:/backend/multi_broker_backend_updated.py', 'r', encoding='utf-8') as f:
    src = f.read()

checks = ['effectiveTradeAmount', 'tradeAmountAdaptation', 'dailyProfitPeaks']
start = src.find('PERSISTED_BOT_STATE_FIELDS = {')
end = src.find('}', start) + 1
block = src[start:end]
for field in checks:
    found = f"'{field}'" in block
    print(f"{field}: {'FOUND' if found else 'MISSING'} in PERSISTED_BOT_STATE_FIELDS")

fix1 = "performance_state['multiplier'] = round(multiplier, 3)" in src
print(f"lastSizingAdjustment fix in backend: {'APPLIED' if fix1 else 'MISSING'}")

with open(r'C:\zwesta-trader\Zwesta Flutter App\multi_broker_backend_updated.py', 'r', encoding='utf-8') as f:
    src2 = f.read()
start2 = src2.find('PERSISTED_BOT_STATE_FIELDS = {')
end2 = src2.find('}', start2) + 1
block2 = src2[start2:end2]
for field in checks:
    found = f"'{field}'" in block2
    print(f"{field}: {'FOUND' if found else 'MISSING'} in Flutter App PERSISTED_BOT_STATE_FIELDS")

fix2 = "performance_state['multiplier'] = round(multiplier, 3)" in src2
print(f"lastSizingAdjustment fix in Flutter App: {'APPLIED' if fix2 else 'MISSING'}")

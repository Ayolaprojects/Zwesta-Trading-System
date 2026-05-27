with open('C:/backend/multi_broker_backend_updated.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find any per-symbol open position limit check before a Binance order
keywords = ['open_for_symbol', 'symbol_positions', 'positions_for_symbol', 'per_symbol', 'same symbol', 'already open', 'symbol.*open.*limit', 'open.*same.*sym']
for i, line in enumerate(lines):
    ll = line.lower()
    if ('symbol' in ll and 'open' in ll and 'position' in ll and any(x in ll for x in ['limit', 'max', '>=',' skip', 'already'])):
        print(f'{i+1}: {line.rstrip()}')

print()
print("=== maxPositionsPerSymbol comparisons ===")
for i, line in enumerate(lines):
    if 'maxPositionsPerSymbol' in line:
        print(f'{i+1}: {line.rstrip()}')

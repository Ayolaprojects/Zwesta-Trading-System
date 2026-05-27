with open('C:/backend/multi_broker_backend_updated.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find where open position count is checked BEFORE placing a Binance futures order
for i, line in enumerate(lines):
    if 'maxPositionsPerSymbol' in line and any(x in line for x in ['>=', '>', 'skip', 'already', 'limit', 'reach']):
        start = max(0, i-3)
        end = min(len(lines), i+6)
        print(f'--- line {i+1} ---')
        for j in range(start, end):
            print(f'{j+1}: {lines[j].rstrip()}')
        print()

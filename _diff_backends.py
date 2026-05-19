"""Find meaningful differences between OneDrive (old) and backend (current) versions.
Focus on trading logic: lot sizing, profit targets, signals, thresholds."""
import difflib, re, sys

old_path = r'C:\Users\zwexm\OneDrive\Documents\multi_broker_backend_updated.py'
new_path = r'C:\backend\multi_broker_backend_updated.py'

with open(old_path, 'r', encoding='utf-8', errors='replace') as f:
    old = f.readlines()
with open(new_path, 'r', encoding='utf-8', errors='replace') as f:
    new = f.readlines()

print(f'OneDrive (old): {len(old)} lines')
print(f'Backend (current): {len(new)} lines')

# Generate unified diff and extract changed hunks
diff = list(difflib.unified_diff(old, new, fromfile='OneDrive', tofile='backend', n=2))

# Trading-relevant keywords
keywords = re.compile(
    r'tradeAmount|lot_size|lotSize|profit|signal|threshold|multiplier|'
    r'retrace|adaptive|sizing|drawdown|riskPer|scalper|recovery|scanner|'
    r'position_size|base_size|leverage|volatility|stopLoss|takeProfit|'
    r'tp_|sl_|min_profit|max_profit|HARD_PEAK|PEAK|lot|risk|guard|cap|'
    r'symbol_perf|perf_mult|performance|defend|conservative',
    re.IGNORECASE
)

# Collect hunks with trading relevance
hunk_lines = []
hunk_relevant = False
hunk_start = None
chunks = []

for line in diff:
    if line.startswith('@@'):
        if hunk_lines and hunk_relevant:
            chunks.append((hunk_start, ''.join(hunk_lines)))
        hunk_lines = [line]
        hunk_relevant = False
        m = re.search(r'\+(\d+)', line)
        hunk_start = int(m.group(1)) if m else 0
    else:
        hunk_lines.append(line)
        if (line.startswith('+') or line.startswith('-')) and keywords.search(line):
            hunk_relevant = True

if hunk_lines and hunk_relevant:
    chunks.append((hunk_start, ''.join(hunk_lines)))

print(f'\nTotal changed hunks with trading keywords: {len(chunks)}\n')
for lineno, hunk in chunks[:60]:
    print(f'--- near line {lineno} ---')
    for l in hunk.splitlines()[:25]:
        print(l)
    print()

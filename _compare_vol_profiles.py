import re

OLD = open(r'C:\Users\zwexm\OneDrive\Documents\multi_broker_backend_updated.py', encoding='utf-8').read()
NEW = open(r'C:\backend\multi_broker_backend_updated.py', encoding='utf-8').read()

# Extract PROFIT_PROTECTION_VOLATILITY_PROFILES from both versions
def extract_block(src, key):
    idx = src.find(key)
    if idx < 0:
        return '(not found)'
    # find next top-level closing
    brace = 0
    start = src.index('{', idx)
    for i, c in enumerate(src[start:], start):
        if c == '{':
            brace += 1
        elif c == '}':
            brace -= 1
            if brace == 0:
                return src[start:i+1]
    return src[start:start+2000]

old_pp = extract_block(OLD, 'PROFIT_PROTECTION_VOLATILITY_PROFILES')
new_pp = extract_block(NEW, 'PROFIT_PROTECTION_VOLATILITY_PROFILES')

print('=== OLD PROFIT_PROTECTION_VOLATILITY_PROFILES ===')
print(old_pp)
print()
print('=== NEW PROFIT_PROTECTION_VOLATILITY_PROFILES ===')
print(new_pp)
print()

if old_pp == new_pp:
    print('IDENTICAL - no difference')
else:
    old_lines = old_pp.split('\n')
    new_lines = new_pp.split('\n')
    for i, (ol, nl) in enumerate(zip(old_lines, new_lines)):
        if ol.strip() != nl.strip():
            print(f'DIFF line {i}: OLD={ol.strip()!r}  NEW={nl.strip()!r}')
    if len(old_lines) != len(new_lines):
        print(f'Length diff: OLD={len(old_lines)} NEW={len(new_lines)}')

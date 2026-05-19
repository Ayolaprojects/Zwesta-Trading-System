import re

OLD = open(r'C:\Users\zwexm\OneDrive\Documents\multi_broker_backend_updated.py', encoding='utf-8').read()
NEW = open(r'C:\backend\multi_broker_backend_updated.py', encoding='utf-8').read()

checks = [
    ('breakEvenLockEnabled default',       r"breakEvenLockEnabled['\"]:\s*(True|False)"),
    ('zeroLossLockEnabled default',        r"zeroLossLockEnabled['\"]:\s*(True|False)"),
    ('closeLosingPositions default',       r"closeLosingPositionsWithProfitablePeers['\"]:\s*(True|False)"),
    ('switchOnReversal default',           r"switchOnReversal['\"]:\s*(True|False)"),
    ('minimumHoldMinutes default',         r"minimumHoldMinutes['\"]:\s*([\d.]+)"),
    ('retraceClosePercent default',        r"retraceClosePercent['\"]:\s*([\d.]+)"),
    ('breakEvenBufferProfit default',      r"breakEvenBufferProfit['\"]:\s*([\d.]+)"),
    ('breakEvenActivationShare default',   r"breakEvenActivationShare['\"]:\s*([\d.]+)"),
    ('activationMinProfit default',        r"activationMinProfit['\"]:\s*([\d.]+)"),
    ('activationPercent default',          r"activationPercent['\"]:\s*([\d.]+)"),
    ('protectedSymbolCooldown default',    r"protectedSymbolCooldownMinutes['\"]:\s*([\d.]+)"),
    ('HARD_PAUSE_MINUTES const',           r"LOSS_STREAK_HARD_PAUSE_MINUTES\s*=\s*(\d+)"),
    ('tradingInterval default',            r"tradingInterval['\"][,\s]*bot\.get\('tradingInterval',\s*(\d+)"),
    ('pollInterval default',               r"pollInterval['\"][,\s]*bot\.get\('pollInterval',\s*(\d+)"),
    ('marginTakeProfitPercent default',    r"marginTakeProfitPercent['\"]:\s*([\d.]+)"),
    ('peakProfitHardLockShare default',    r"peakProfitHardLockShare['\"]:\s*([\d.]+)"),
]

for label, pattern in checks:
    old_m = sorted(set(re.findall(pattern, OLD)))
    new_m = sorted(set(re.findall(pattern, NEW)))
    changed = ' <<CHANGED>>' if old_m != new_m else ''
    print(f'{label:40} OLD={str(old_m):30} NEW={str(new_m):30}{changed}')

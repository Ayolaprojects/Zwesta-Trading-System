"""Compare old OneDrive vs current backend for trade hold/duration related settings."""
import re

OLD_PATH = r'C:\Users\zwexm\OneDrive\Documents\multi_broker_backend_updated.py'
NEW_PATH = r'C:\backend\multi_broker_backend_updated.py'

with open(OLD_PATH, 'r', encoding='utf-8') as f:
    old_lines = f.readlines()
with open(NEW_PATH, 'r', encoding='utf-8') as f:
    new_lines = f.readlines()

old_src = ''.join(old_lines)
new_src = ''.join(new_lines)

# Key patterns to compare
patterns = [
    ('minimumHoldMinutes', r'minimumHoldMinutes.*?=.*?\d+'),
    ('retraceClosePercent', r'retraceClosePercent.*?[\d.]+'),
    ('breakEvenBufferProfit', r'breakEvenBufferProfit.*?[\d.]+'),
    ('breakEvenActivationShare', r'breakEvenActivationShare.*?[\d.]+'),
    ('peakProfitHardLockShare', r'peakProfitHardLockShare.*?[\d.]+'),
    ('activationMinProfit', r'activationMinProfit.*?[\d.]+'),
    ('activationPercent', r'activationPercent.*?[\d.]+'),
    ('protectedSymbolCooldownMinutes', r'protectedSymbolCooldownMinutes.*?[\d.]+'),
    ('loss_streak_pause_after', r'LOSS_STREAK_PAUSE_AFTER\s*=\s*\d+'),
    ('loss_streak_pause_minutes', r'LOSS_STREAK_PAUSE_MINUTES\s*=\s*\d+'),
    ('loss_streak_hard_pause_after', r'LOSS_STREAK_HARD_PAUSE_AFTER\s*=\s*\d+'),
    ('loss_streak_hard_pause_minutes', r'LOSS_STREAK_HARD_PAUSE_MINUTES\s*=\s*\d+'),
    ('loss_streak_symbol_cooldown', r'LOSS_STREAK_SYMBOL_COOLDOWN_MINUTES\s*=\s*\d+'),
    ('Exness_pause_after', r"loss_streak_pause_after\s*=\s*min.*?\d+\)"),
    ('Exness_pause_minutes', r"loss_streak_pause_minutes\s*=\s*max.*?\d+\)"),
    ('Exness_hard_pause_after', r"loss_streak_hard_pause_after\s*=\s*min.*?\d+\)"),
    ('Exness_hard_pause_minutes', r"loss_streak_hard_pause_minutes\s*=\s*max.*?\d+\)"),
    ('Exness_symbol_cooldown', r"loss_streak_symbol_cooldown_minutes\s*=\s*max.*?\d+\)"),
    ('postLossSameDirectionCooldown', r'postLossSameDirectionCooldownMinutes.*?[\d.]+'),
    ('drawdownPauseHours_default', r'drawdownPauseHours.*?[\d.]+'),
    ('XAGUSD_cooldown', r'XAGUSD.*?[\d.]+.*?cooldown|post_loss.*?XAGUSD.*?[\d.]+'),
    ('pollInterval', r"'pollInterval'.*?[\d]+"),
    ('tradingInterval', r"'tradingInterval'.*?[\d]+"),
]

for label, pattern in patterns:
    old_matches = list(set(re.findall(pattern, old_src)))[:3]
    new_matches = list(set(re.findall(pattern, new_src)))[:3]
    old_str = ' | '.join(m.strip() for m in old_matches) or '(none)'
    new_str = ' | '.join(m.strip() for m in new_matches) or '(none)'
    changed = ' <<CHANGED>>' if old_str != new_str else ''
    print(f'{label:35} OLD: {old_str[:60]:60}  NEW: {new_str[:60]}{changed}')

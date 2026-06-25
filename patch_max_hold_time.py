"""
Patch for multi_broker_backend_updated.py - Adds MAX_HOLD_TIME_EXCEEDED check
This script adds a new position closing condition to prevent stale positions from leaking
"""

import re

# Read the original file
with open(r'C:\zwesta-trader\Zwesta Flutter App\multi_broker_backend_updated.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the position where we need to insert the max hold time check
# Look for the section after SL_HIT check and before the "Trailing profit floor enforcement" comment
old_pattern = r'''(trigger_reason = 'SL_HIT'\s*\n\s*# ── Trailing profit floor enforcement)'''

new_code = '''# Check if position has exceeded maximum hold time (prevent 14-day stale positions)
             _max_hold_min = _safe_float(runtime_state.get('maximumHoldMinutes'), 360.0)  # Default 6 hours
             _entry_iso_max = str(tracked.get('entryTime') or tracked.get('time') or '').strip()
             if _entry_iso_max and _max_hold_min > 0:
                 try:
                     from datetime import datetime
                     _entry_dt_max = datetime.fromisoformat(_entry_iso_max.replace('Z', ''))
                     _held_total_min = (datetime.now() - _entry_dt_max).total_seconds() / 60.0
                     if _held_total_min >= _max_hold_min:
                         trigger_reason = 'MAX_HOLD_TIME_EXCEEDED'
                         logger.warning(
                             f"[LEAK_FIX] Bot {bot_id}: {tracked_symbol} MAX_HOLD_TIME_EXCEEDED — "
                             f"held {_held_total_min:.0f}m >= {_max_hold_min}m limit, closing position"
                         )
                 except Exception:
                     pass
             
             \\1'''

# Apply the replacement
new_content = re.sub(old_pattern, new_code, content)

if new_content != content:
    with open(r'C:\zwesta-trader\Zwesta Flutter App\multi_broker_backend_updated.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("[PATCH] Successfully added MAX_HOLD_TIME_EXCEEDED check to backend")
else:
    print("[PATCH] Pattern not found - check file structure")
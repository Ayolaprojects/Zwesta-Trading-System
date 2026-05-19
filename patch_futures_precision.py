"""
Patch: fix Binance futures quantity precision (-1111 error)
Run this ON the VPS: python C:\patch_futures_precision.py
"""
import re, shutil, datetime

BACKEND = r'C:\backend\multi_broker_backend_updated.py'

OLD = (
    "            quantity_value = format(quantity, '.8f').rstrip('0').rstrip('.')\n"
    "            if self.market != 'futures':\n"
    "                quantity_value = self._format_spot_quantity(quantity, step_size, min_qty)"
)

NEW = (
    "            if self.market == 'futures':\n"
    "                from decimal import Decimal, ROUND_DOWN\n"
    "                _step = Decimal(str(step_size)) if step_size > 0 else Decimal('0.001')\n"
    "                _qty_d = Decimal(str(quantity)).quantize(_step, rounding=ROUND_DOWN)\n"
    "                quantity = float(_qty_d)\n"
    "                if quantity <= 0:\n"
    "                    return {'success': False, 'error': f'Calculated futures quantity {_qty_d} is below minimum step {step_size} for {instrument}'}\n"
    "                _decimals = max(0, -_step.as_tuple().exponent)\n"
    "                quantity_value = f\"{quantity:.{_decimals}f}\"\n"
    "            else:\n"
    "                quantity_value = self._format_spot_quantity(quantity, step_size, min_qty)"
)

with open(BACKEND, 'r', encoding='utf-8') as f:
    content = f.read()

if OLD not in content:
    print("ERROR: Target pattern not found — may already be patched or file differs.")
    print("Searching for 'format(quantity' to locate the line...")
    for i, line in enumerate(content.splitlines(), 1):
        if "format(quantity, '.8f')" in line:
            print(f"  Line {i}: {line.rstrip()}")
    raise SystemExit(1)

ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
backup = BACKEND.replace('.py', f'.BACKUP_{ts}.py')
shutil.copy2(BACKEND, backup)
print(f"Backup saved: {backup}")

patched = content.replace(OLD, NEW, 1)
with open(BACKEND, 'w', encoding='utf-8') as f:
    f.write(patched)

print("Patch applied successfully.")

# Verify syntax
import ast
try:
    ast.parse(patched)
    print("SYNTAX OK")
except SyntaxError as e:
    print(f"SYNTAX ERROR: {e} — restoring backup")
    shutil.copy2(backup, BACKEND)
    raise SystemExit(1)

print("\nNow restart the backend:")
print('  $p = Get-WmiObject Win32_Process | Where-Object {$_.CommandLine -like "*multi_broker_backend*"}')
print('  if ($p) { Stop-Process -Id $p.ProcessId -Force }')
print('  Start-Sleep -Seconds 3')
print('  Start-Process python "C:\\backend\\multi_broker_backend_updated.py" -WindowStyle Minimized')

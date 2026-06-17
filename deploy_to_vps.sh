#!/usr/bin/env bash
# VPS Deployment Package - Copy This Script Content to VPS
# Usage: Save this as deploy.sh, then run: bash deploy.sh

echo "========================================"
echo "Zwesta Profit Peak Protection Deployment"
echo "========================================"
echo ""

# Configuration
APP_PATH="${1:-.}"  # Default to current directory
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)

echo "[1/5] Backing up current backend..."
cp "$APP_PATH/multi_broker_backend_updated.py" "$APP_PATH/multi_broker_backend_updated.py.backup.$BACKUP_DATE"
echo "✅ Backup created: multi_broker_backend_updated.py.backup.$BACKUP_DATE"
echo ""

echo "[2/5] Copying new files..."
echo "- fix_profit_peak_erosion.py"
echo "- multi_broker_backend_updated.py (with 3 critical edits)"
# Files should be copied here manually via scp or file transfer
echo "✅ Files should be in $APP_PATH"
echo ""

echo "[3/5] Verifying syntax..."
python -m py_compile "$APP_PATH/multi_broker_backend_updated.py"
if [ $? -eq 0 ]; then
    echo "✅ Backend syntax: OK"
else
    echo "❌ Backend syntax: FAILED"
    exit 1
fi
echo ""

echo "[4/5] Verifying imports..."
python -c "from fix_profit_peak_erosion import *; print('✅ Peak protection module: OK')"
if [ $? -eq 0 ]; then
    echo "✅ All imports: OK"
else
    echo "❌ Import error - check fix_profit_peak_erosion.py exists"
    exit 1
fi
echo ""

echo "[5/5] File sizes..."
ls -lh "$APP_PATH/fix_profit_peak_erosion.py" "$APP_PATH/multi_broker_backend_updated.py"
echo ""

echo "========================================"
echo "✅ DEPLOYMENT VERIFICATION COMPLETE"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Restart backend: systemctl restart zwesta-backend"
echo "2. Watch logs: tail -f backend.log | grep -i peak"
echo "3. Monitor for 24-48 hours"
echo "4. Expect: PEAK DETECTED messages after 24-48h"
echo ""
echo "If issues occur, rollback:"
echo "  cp multi_broker_backend_updated.py.backup.$BACKUP_DATE multi_broker_backend_updated.py"
echo "  systemctl restart zwesta-backend"

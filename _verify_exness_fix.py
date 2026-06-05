"""VERIFY EXNESS FIX - Check what was actually applied"""
import json
import sqlite3

db = sqlite3.connect('C:/backend/zwesta_trading.db')
db.row_factory = sqlite3.Row
cur = db.cursor()

print("="*80)
print("EXNESS FIX VERIFICATION - CURRENT BOT STATE")
print("="*80)

rows = cur.execute("""
    SELECT bot_id, broker_account_id, runtime_state FROM user_bots 
    WHERE broker_account_id LIKE 'Exness_%'
""").fetchall()

for r in rows:
    rs = json.loads(r['runtime_state'] or '{}') if r['runtime_state'] else {}
    
    print(f"\n📌 {r['bot_id'][-15:]} ({r['broker_account_id']})")
    print(f"   Signal Threshold: {rs.get('signalThreshold', 'N/A')}")
    print(f"   Trade Amount: {rs.get('tradeAmount', 'N/A')}")
    print(f"   Max Lot Size: {rs.get('maxLotSize', 'N/A')}")
    print(f"   Stop Loss: {rs.get('stopLossPercentage', 'N/A')}%")
    print(f"   Take Profit: {rs.get('takeProfitPercentage', 'N/A')}%")
    print(f"   TP/SL Ratio: {rs.get('takeProfitPercentage', 0) / rs.get('stopLossPercentage', 1) if rs.get('stopLossPercentage') else 'N/A'}:1")
    print(f"   Pyramid: {rs.get('pyramidingEnabled', 'N/A')}")
    print(f"   Martingale: {rs.get('scalingMode', 'N/A')}")
    print(f"   Cooldown: {rs.get('postCloseCooldownMinutes', 'N/A')} min")
    print(f"   Max Consecutive Losses: {rs.get('maxConsecutiveLosingTrades', 'N/A')}")
    print(f"   Daily Loss Limit: {rs.get('dailyLossLimit', 'N/A')} ZAR")
    print(f"   Status: {rs.get('managementState', 'N/A')}")
    
    # Check symbol config
    sym_cfg = rs.get('symbol_config', {})
    if sym_cfg:
        print(f"   Enabled Symbols:")
        for sym, cfg in sym_cfg.items():
            if cfg.get('enabled'):
                print(f"      ✓ {sym}")
        print(f"   Disabled Symbols:")
        for sym, cfg in sym_cfg.items():
            if not cfg.get('enabled'):
                reason = cfg.get('reason', 'Not specified')
                print(f"      ✗ {sym}: {reason}")

print("\n" + "="*80)
print("✅ VERIFICATION COMPLETE")
print("="*80)
print("\nRecommendation:")
print("1. RESTART backend: python start_zwesta_backend.ps1")
print("2. Monitor live trades for 1-2 hours")
print("3. If losses continue, likely SIGNAL INVERSION issue")
print("   → Run: python _test_signal_reversal.py")

db.close()

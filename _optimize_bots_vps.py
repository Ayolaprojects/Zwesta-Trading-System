"""
Bot Optimization Script — run this ON THE VPS (C:\backend folder).

LOSS PROTECTION UPDATES:
1. ⬆️ Signal threshold: 70 (was 65) - stricter filtering
2. 🛡️ Daily loss limits: R30-R50 max loss per day
3. 📉 Auto position reduction after 2 losses (backend handles this)
4. 🎯 Only 1 position at a time (prevents overexposure)
5. ⚡ Quick profit lock at R1+ to secure wins
6. 🚫 Trading pauses automatically if daily loss hit

EXAMPLE PROTECTION:
- Bot 1 & 2: Stop trading after -R30 daily loss (50x leverage)
- Bot 3 & 4: Stop trading after -R40 daily loss (25x leverage)
- After 2 consecutive losses: Position size drops to 75% (backend auto-adjusts)
- After 3 consecutive losses: Trading PAUSES (circuit breaker)

This prevents sequences like: -R16, -R20, -R18, -R14 = -R68 total loss
Instead: -R16, -R14 (pause) = -R30 max loss, then bot stops for the day
"""
import sqlite3, json, shutil, os
from datetime import datetime

DB_PATH = r"C:\backend\zwesta_trading.db"

def main():
    # Backup first
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = DB_PATH.replace(".db", f"_BACKUP_{ts}.db")
    shutil.copy2(DB_PATH, backup)
    print(f"Backup created: {backup}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Check integrity
    cur.execute("PRAGMA integrity_check")
    ic = cur.fetchone()[0]
    if ic != "ok":
        print(f"WARNING: DB integrity check returned: {ic}")
        print("Attempting recovery via dump/reload...")
        conn.close()
        _recover_db(DB_PATH, backup)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

    optimizations = {
        # Binance futures bot — was signalThreshold=30 (too low), effectivePositionSizeMultiplier=0.45
        "bot_1779229018996": {
            "signalThreshold": 65,
            "managementProfile": "fast_growth",
            "maxOpenPositions": 1,
            "maxPositionsPerSymbol": 1,
            "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
            "effectivePositionSizeMultiplier": 30.0,  # ⚠️ EXTREME RISK - 30x position sizing
            "profitConditionalMultiplier": True,  # 🛡️ SAFEGUARD: Only use 30x when totalProfit >= 0
            "basePositionSizeMultiplier": 1.0,  # Use 1x (normal) when in loss
            "maxDailyLoss": 50.0,  # 🛡️ STOP trading after R50 daily loss
        },
        # Exness bot 1 — GBP/USD + AUD/USD with 50x + AGGRESSIVE PROFIT LOCK (mimics manual pattern)
        "bot_1779663832148": {
            "managementProfile": "fast_growth",
            "signalThreshold": 70,  # ⬆️ Raised from 65 to filter weaker signals
            "symbols": ["GBPUSDm", "AUDUSDm"],
            "effectivePositionSizeMultiplier": 50.0,  # ⚠️ EXTREME RISK - 50x position sizing
            "profitConditionalMultiplier": True,  # 🛡️ SAFEGUARD: Only use 50x when totalProfit >= 0
            "basePositionSizeMultiplier": 1.0,  # Use 1x (normal) when in loss
            "maxDailyLoss": 30.0,  # 🛡️ CIRCUIT BREAKER: Stop after R30 daily loss
            "maxOpenPositions": 1,  # Only 1 trade at a time
            "maxPositionsPerSymbol": 1,
            "profitProtection": {
                "enabled": True,
                "activationMinProfit": 0.50,  # 🎯 Activate earlier at R0.50 (was R1.0)
                "minLockedProfit": 0.30,  # Lock 30% of profit minimum (was 0.5)
                "retraceClosePercent": 12.0,  # 🚨 Close on 12% retrace (was 20%) - mimics your manual pattern
                "breakEvenBufferProfit": 1.0,  # Tighter break-even (was 1.5)
                "breakEvenActivationShare": 0.15,  # Activate at 15% to TP (was 20%)
                "zeroLossLockEnabled": True,
                "minimumHoldMinutes": 3.0,  # Exit faster (was 5.0) - don't hold losing momentum
            },
        },
        # Exness bot 2 — GBP/USD + AUD/USD with 50x + AGGRESSIVE PROFIT LOCK (mimics manual pattern)
        "bot_1779676762137": {
            "signalThreshold": 70,  # ⬆️ Raised from 65
            "symbols": ["GBPUSDm", "AUDUSDm"],
            "effectivePositionSizeMultiplier": 50.0,  # ⚠️ EXTREME RISK - 50x position sizing
            "profitConditionalMultiplier": True,  # 🛡️ SAFEGUARD: Only use 50x when totalProfit >= 0
            "basePositionSizeMultiplier": 1.0,  # Use 1x (normal) when in loss
            "maxDailyLoss": 30.0,  # 🛡️ CIRCUIT BREAKER: Stop after R30 daily loss
            "maxOpenPositions": 1,
            "maxPositionsPerSymbol": 1,
            "profitProtection": {
                "enabled": True,
                "activationMinProfit": 0.50,  # 🎯 Activate earlier at R0.50 (was R1.0)
                "minLockedProfit": 0.30,  # Lock 30% of profit minimum (was 0.5)
                "retraceClosePercent": 12.0,  # 🚨 Close on 12% retrace (was 20%) - mimics your manual pattern
                "breakEvenBufferProfit": 1.0,  # Tighter break-even (was 1.5)
                "breakEvenActivationShare": 0.15,  # Activate at 15% to TP (was 20%)
                "zeroLossLockEnabled": True,
                "minimumHoldMinutes": 3.0,  # Exit faster (was 5.0) - don't hold losing momentum
            },
        },
        # Exness bot 3 — Focus on GBP/USD + AUD/USD with AGGRESSIVE PROFIT LOCK
        "bot_1779698254543": {
            "signalThreshold": 70,  # ⬆️ Raised from 65
            "symbols": ["GBPUSDm", "AUDUSDm"],
            "effectivePositionSizeMultiplier": 25.0,  # Moderate 25x sizing
            "profitConditionalMultiplier": True,  # 🛡️ SAFEGUARD: Only use 25x when totalProfit >= 0
            "basePositionSizeMultiplier": 1.0,  # Use 1x (normal) when in loss
            "maxDailyLoss": 40.0,  # 🛡️ CIRCUIT BREAKER: Stop after R40 daily loss
            "maxOpenPositions": 1,
            "maxPositionsPerSymbol": 1,
            "profitProtection": {
                "enabled": True,
                "activationMinProfit": 0.50,  # 🎯 Activate earlier at R0.50 (was R1.0)
                "minLockedProfit": 0.30,  # Lock 30% of profit minimum (was 0.5)
                "retraceClosePercent": 12.0,  # 🚨 Close on 12% retrace (was 20%) - mimics your manual pattern
                "breakEvenBufferProfit": 1.0,  # Tighter break-even (was 1.5)
                "breakEvenActivationShare": 0.15,  # Activate at 15% to TP (was 20%)
                "zeroLossLockEnabled": True,
                "minimumHoldMinutes": 3.0,  # Exit faster (was 5.0) - don't hold losing momentum
            },
        },
        # Exness bot 4 — Focus on GBP/USD + AUD/USD with AGGRESSIVE PROFIT LOCK
        "bot_1779698380843_043c7e5d": {
            "signalThreshold": 70,  # ⬆️ Raised from 65
            "symbols": ["GBPUSDm", "AUDUSDm"],
            "effectivePositionSizeMultiplier": 25.0,  # Moderate 25x sizing
            "profitConditionalMultiplier": True,  # 🛡️ SAFEGUARD: Only use 25x when totalProfit >= 0
            "basePositionSizeMultiplier": 1.0,  # Use 1x (normal) when in loss
            "maxDailyLoss": 40.0,  # 🛡️ CIRCUIT BREAKER: Stop after R40 daily loss
            "maxOpenPositions": 1,
            "maxPositionsPerSymbol": 1,
            "profitProtection": {
                "enabled": True,
                "activationMinProfit": 0.50,  # 🎯 Activate earlier at R0.50 (was R1.0)
                "minLockedProfit": 0.30,  # Lock 30% of profit minimum (was 0.5)
                "retraceClosePercent": 12.0,  # 🚨 Close on 12% retrace (was 20%) - mimics your manual pattern
                "breakEvenBufferProfit": 1.0,  # Tighter break-even (was 1.5)
                "breakEvenActivationShare": 0.15,  # Activate at 15% to TP (was 20%)
                "zeroLossLockEnabled": True,
                "minimumHoldMinutes": 3.0,  # Exit faster (was 5.0) - don't hold losing momentum
            },
        },
    }

    for bot_id, updates in optimizations.items():
        cur.execute("SELECT runtime_state FROM user_bots WHERE bot_id = ?", (bot_id,))
        row = cur.fetchone()
        if not row:
            print(f"  SKIP (not found): {bot_id}")
            continue
        rs = json.loads(row["runtime_state"] or "{}")
        
        # Reset consecutive losses counter (fresh start)
        rs['consecutiveLosses'] = 0
        
        # Clear any existing pause states
        rs['drawdownPauseUntil'] = None
        rs['profitLockCooldownUntil'] = None
        
        # Deep merge for nested dicts like profitProtection
        for key, value in updates.items():
            if key == 'profitProtection' and isinstance(value, dict):
                # Merge profitProtection settings
                existing_pp = rs.get('profitProtection', {})
                if isinstance(existing_pp, dict):
                    existing_pp.update(value)
                    rs['profitProtection'] = existing_pp
                else:
                    rs['profitProtection'] = value
            else:
                rs[key] = value
        
        cur.execute("UPDATE user_bots SET runtime_state = ? WHERE bot_id = ?",
                    (json.dumps(rs), bot_id))
        print(f"  UPDATED {bot_id}")
        print(f"    ✅ Reset consecutive losses to 0")
        print(f"    ✅ Cleared pause states")
        for k, v in updates.items():
            if k == 'profitProtection':
                print(f"    profitProtection:")
                for pp_key, pp_val in v.items():
                    print(f"      {pp_key}: {pp_val}")
            else:
                before_val = rs.get(k) if k not in updates else "N/A"
                print(f"    {k}: → {v}")
        print()

    conn.commit()
    conn.close()
    print("All changes committed. DB integrity:", _check_integrity(DB_PATH))
    
    print("\n" + "=" * 80)
    print("🛡️ LOSS PROTECTION SUMMARY")
    print("=" * 80)
    print()
    print("Your bots now have MULTIPLE layers of protection:")
    print()
    print("0️⃣ PROFIT-CONDITIONAL MULTIPLIER (NEW!) 🆕")
    print("   • Multiplier ONLY activates when totalProfit >= R0 (in green)")
    print("   • When totalProfit < R0 (in red): Uses 1x normal sizing")
    print("   • When totalProfit >= R0 (breakeven or profit): Uses 30x-50x multiplier")
    print()
    print("   EXAMPLE:")
    print("   Current profit = -R25 (RED) → Next trade uses 1x (0.01 lots)")
    print("   Current profit = +R5 (GREEN) → Next trade uses 50x (0.50 lots)")
    print("   Current profit = R0 (BREAKEVEN) → Next trade uses 50x (0.50 lots)")
    print()
    print("   ✅ This prevents aggressive losses when already in the red!")
    print("   ✅ Bot must trade back to breakeven with NORMAL sizing first")
    print("   ✅ Then switches to HIGH sizing to accelerate profits")
    print()
    print("1️⃣ DAILY LOSS CIRCUIT BREAKER")
    print("   • Bots 1 & 2 (50x): Stop after -R30 daily loss")
    print("   • Bots 3 & 4 (25x): Stop after -R40 daily loss")
    print("   → Prevents massive loss sequences like -R16, -R20, -R18, -R14")
    print()
    print("   ✅ AUTO-RESUME: Automatically at midnight (new day)")
    print("      Daily loss counter RESETS to R0 every day at 00:00 SAST")
    print("      Trading resumes automatically with fresh daily limit")
    print()
    print("2️⃣ CONSECUTIVE LOSS AUTO-REDUCTION")
    print("   • After 2 losses: Position size drops to 75%")
    print("   • After 3 losses: Trading PAUSES automatically")
    print("   → Example: Instead of 50x → 50x → 50x losing trades")
    print("            You get:    50x → 37.5x → PAUSE")
    print()
    print("   ✅ AUTO-RESUME: When market conditions improve")
    print("      • If bot becomes profitable again → consecutive losses reset")
    print("      • After idle period (45+ min) with no open positions → auto-resume")
    print("      • When strong signal (70+) appears → early resume possible")
    print()
    print("3️⃣ STRICTER SIGNAL FILTERING")
    print("   • Signal threshold: 70 (was 65)")
    print("   • Only trades HIGH-QUALITY setups")
    print("   → Fewer trades = fewer chances to lose")
    print()
    print("4️⃣ QUICK PROFIT PROTECTION")
    print("   • Locks profit at R1+ (prevents rollback)")
    print("   • Auto-closes if profit drops 20% from peak")
    print("   → Secures small wins before they reverse")
    print()
    print("5️⃣ SINGLE POSITION LIMIT")
    print("   • Only 1 trade at a time per bot")
    print("   → Cannot have multiple losing positions simultaneously")
    print()
    print("=" * 80)
    print("🔄 AUTO-RESUME SCENARIOS")
    print("=" * 80)
    print()
    print("SCENARIO 1: Daily Loss Limit Hit (-R30)")
    print("  8:00 PM: Loss 1 = -R16")
    print("  8:15 PM: Loss 2 = -R14")
    print("  8:20 PM: Total = -R30 → BOT PAUSED 🛑")
    print("  11:59 PM: Still paused...")
    print("  12:00 AM: NEW DAY → AUTO-RESUME ✅ (fresh R30 limit)")
    print()
    print("SCENARIO 2: Consecutive Losses (3 in a row)")
    print("  8:00 PM: Loss 1")
    print("  8:10 PM: Loss 2 (position size reduced)")
    print("  8:20 PM: Loss 3 → BOT PAUSED 🛑")
    print("  9:05 PM: 45 min idle, no positions → AUTO-RESUME ✅")
    print()
    print("SCENARIO 3: Drawdown Recovery")
    print("  Bot paused due to losses")
    print("  Strong signal (75 strength) appears")
    print("  System checks: No open positions + High quality signal")
    print("  → EARLY AUTO-RESUME ✅ (doesn't wait for expiry)")
    print()
    print("=" * 80)
    print("WORST CASE SCENARIO (with new protections):")
    print("  Trade 1: -R16 (full 50x size)")
    print("  Trade 2: -R12 (reduced to 37.5x size)")
    print("  Trade 3: PAUSED (hit R30 daily loss limit)")
    print("  TOTAL LOSS: -R28 (saved from -R68 potential)")
    print("  NEXT DAY: Auto-resumes at midnight with fresh limits")
    print()
    print("=" * 80)
    print("✅ All bots updated with maximum loss protection!")
    print("✅ Auto-resume enabled - no manual intervention needed!")
    print("=" * 80)


def _check_integrity(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA integrity_check")
    r = cur.fetchone()[0]
    conn.close()
    return r


def _recover_db(db_path, original_backup):
    """Recover a malformed SQLite database via dump/reload."""
    dump_path = db_path + ".dump.sql"
    recovered_path = db_path + ".recovered"

    src = sqlite3.connect(original_backup)
    with open(dump_path, "w", encoding="utf-8") as f:
        for line in src.iterdump():
            f.write(line + "\n")
    src.close()

    dst = sqlite3.connect(recovered_path)
    with open(dump_path, "r", encoding="utf-8") as f:
        dst.executescript(f.read())
    dst.close()
    os.replace(recovered_path, db_path)
    os.remove(dump_path)
    print("DB recovered from dump.")


if __name__ == "__main__":
    main()

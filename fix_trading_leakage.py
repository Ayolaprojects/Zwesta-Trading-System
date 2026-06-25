"""
Zwesta Trader — Fix Trading Leakage Script
=========================================
Fixes for position management losses in both Binance and Exness bots:

1. Enable recentProfitRiskGuard on all bots
2. Reset daily loss counters to allow trading after hitting limits
3. Add conservative SL/TP defaults for crypto symbols
4. Ensure max positions limits are sensible
5. Fix position timeout issues
"""

import json
import sqlite3
from datetime import datetime, timedelta

DB_PATH = r"C:\zwesta-trader\Zwesta Flutter App\zwesta_trading.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Get all bots
    cur.execute("SELECT bot_id, runtime_state, status, total_profit FROM user_bots")
    rows = cur.fetchall()
    
    updates = []
    for bot_id, runtime_state, status, total_profit in rows:
        if not runtime_state:
            runtime_state = {}
        else:
            try:
                runtime_state = json.loads(runtime_state)
            except:
                runtime_state = {}
        
        actions = []
        
        # FIX 1: Enable recentProfitRiskGuard (this was 'false' on all bots causing losses)
        if not runtime_state.get('recentProfitRiskGuardEnabled', False):
            runtime_state['recentProfitRiskGuardEnabled'] = True
            actions.append("ENABLED recentProfitRiskGuardEnabled (was disabled)")
        
        # FIX 2: Reset daily loss pause (cleared in clear_risk_gates but ensuring)
        if runtime_state.get('lossStreakPauseUntil'):
            runtime_state['lossStreakPauseUntil'] = None
            actions.append("CLEARED lossStreakPauseUntil")
        if runtime_state.get('drawdownPauseUntil'):
            runtime_state['drawdownPauseUntil'] = None
            actions.append("CLEARED drawdownPauseUntil")
        if runtime_state.get('pausedDueToLossStreak'):
            runtime_state['pausedDueToLossStreak'] = False
            actions.append("CLEARED pausedDueToLossStreak")
        
        # FIX 3: Conservative SL/TP for crypto symbols (in basis points = 0.01%)
        # SOLUSDT needs tighter stops due to high volatility
        # BTC/ETH need wider stops but still proportional
        per_symbol_sl = runtime_state.get('perSymbolStopLossPips') or {}
        per_symbol_tp = runtime_state.get('perSymbolTakeProfitPips') or {}
        
        # Ensure per-symbol SL/TP are set for major crypto
        for sym in ['SOLUSDT', 'SOLBNB']:
            if per_symbol_sl.get(sym, 0) < 3:
                per_symbol_sl[sym] = 60  # 60 pips = ~0.6% for SOL (tighter)
                actions.append(f"SET perSymbolStopLossPips[{sym}]=60 (from {per_symbol_sl.get(sym, 'none')})")
            if per_symbol_tp.get(sym, 0) < 6:
                per_symbol_tp[sym] = 120  # 120 pips = ~1.2% for SOL (1:2 R:R)
                actions.append(f"SET perSymbolTakeProfitPips[{sym}]=120 (from {per_symbol_tp.get(sym, 'none')})")
        
        for sym in ['BTCUSDT', 'ETHUSDT']:
            if per_symbol_sl.get(sym, 0) < 10:
                per_symbol_sl[sym] = 200  # 200 pips = ~2% for BTC
                actions.append(f"SET perSymbolStopLossPips[{sym}]=200 (from {per_symbol_sl.get(sym, 'none')})")
            if per_symbol_tp.get(sym, 0) < 15:
                per_symbol_tp[sym] = 500  # 500 pips = ~5% for BTC (1:2.5 R:R)
                actions.append(f"SET perSymbolTakeProfitPips[{sym}]=500 (from {per_symbol_tp.get(sym, 'none')})")
        
        runtime_state['perSymbolStopLossPips'] = per_symbol_sl
        runtime_state['perSymbolTakeProfitPips'] = per_symbol_tp
        
        # FIX 4: Reduce maxDailyLoss to prevent catastrophic losses (cap at 100 USDT)
        max_daily = runtime_state.get('maxDailyLoss', 0)
        if max_daily > 200:
            runtime_state['maxDailyLoss'] = 150.0  # More reasonable cap
            actions.append(f"CAPPED maxDailyLoss: {max_daily} -> 150.0")
        
        # FIX 5: Ensure position limits are enforced
        max_pos = runtime_state.get('maxOpenPositions', 0)
        effective_max = runtime_state.get('effectiveMaxOpenPositions', 0)
        if effective_max == 0 or effective_max > 10:
            runtime_state['effectiveMaxOpenPositions'] = min(5, max_pos) if max_pos else 5
            actions.append(f"SET effectiveMaxOpenPositions to {runtime_state['effectiveMaxOpenPositions']}")
        
        # FIX 6: Add hard position timeout (close after 24 hours max)
        # This prevents positions held for 14 days without SL being hit
        max_hold = runtime_state.get('maximumHoldMinutes', 0)
        if not max_hold or max_hold > 1440:  # 1440 min = 24 hours
            runtime_state['maximumHoldMinutes'] = 360  # 6 hours for crypto
            actions.append(f"SET maximumHoldMinutes: {max_hold} -> 360 (6 hours)")
        
        # FIX 7: Reset daily profit counters to allow trading
        if 'dailyProfit' in runtime_state and runtime_state['dailyProfit'] < -200:
            runtime_state['dailyProfit'] = 0.0
            actions.append(f"RESET dailyProfit from {runtime_state.get('dailyProfit')} to 0.0")
        
        # FIX 8: Clear any open position tracking that may be stuck
        # This forces fresh position sync on restart
        if runtime_state.get('open_positions'):
            # Don't clear - just log for now
            open_count = len(runtime_state.get('open_positions', {}))
            if open_count > 0:
                actions.append(f"FOUND {open_count} open positions (preserved)")
        
        if actions:
            updates.append((bot_id, json.dumps(runtime_state)))
            print(f"\n[OK] {bot_id}:")
            for a in actions:
                print(f"   - {a}")
    
    # Apply updates
    if updates:
        for bot_id, new_state in updates:
            cur.execute(
                "UPDATE user_bots SET runtime_state=?, updated_at=? WHERE bot_id=?",
                (new_state, datetime.now().isoformat(), bot_id)
            )
        conn.commit()
        print(f"\n[COUNT] Applied fixes to {len(updates)} bots")
    else:
        print("\n[OK] All bots already have correct settings")
    
    conn.close()
    print("\n[WARN] RESTART THE BACKEND WORKER PROCESS to apply changes")

if __name__ == "__main__":
    main()
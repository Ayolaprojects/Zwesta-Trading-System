#!/usr/bin/env python3
"""
Comprehensive bot performance analysis from runtime_state JSON
"""
import sqlite3
import json
from collections import defaultdict
from datetime import datetime

def analyze_all_bots():
    """Analyze all bots from their runtime_state"""
    db = sqlite3.connect('zwesta_trading.db')
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    
    cursor.execute("SELECT bot_id, symbols, broker_account_id, runtime_state, total_profit, daily_profit, created_at FROM user_bots")
    bots = cursor.fetchall()
    
    print("\n" + "="*100)
    print("TRADING SYSTEM LOSS ANALYSIS - RUNTIME PERFORMANCE")
    print("="*100)
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    symbol_performance = defaultdict(lambda: {
        'total_pnl': 0,
        'wins': 0,
        'losses': 0,
        'win_rate': 0,
        'verdict': 'unknown',
        'multiplier': 1.0,
        'bots': []
    })
    
    print(f"[1] ANALYZING {len(bots)} ACTIVE BOTS\n")
    
    for bot in bots:
        bot_id = bot['bot_id']
        broker_id = bot['broker_account_id']
        symbols_str = bot['symbols'] or ''
        total_pnl = bot['total_profit'] or 0
        
        try:
            runtime_state = json.loads(bot['runtime_state'] or '{}')
        except:
            runtime_state = {}
        
        symbol_perf = runtime_state.get('symbolPerformance', {})
        
        print(f"Bot: {bot_id}")
        print(f"  Broker: {broker_id}")
        print(f"  Symbols: {symbols_str}")
        print(f"  Total P/L: {total_pnl:.2f} USDT")
        enabled = bot[4] if len(bot) > 5 else (bot.get('enabled') if isinstance(bot, dict) else True)
        print(f"  Status: {'Active' if enabled else 'Inactive'}")
        
        if symbol_perf:
            print(f"  Symbol Performance:")
            for symbol, perf_data in symbol_perf.items():
                wins = perf_data.get('wins', 0)
                losses = perf_data.get('losses', 0)
                pnl = perf_data.get('pnl', 0)
                verdict = perf_data.get('verdict', 'unknown')
                multiplier = perf_data.get('multiplier', 1.0)
                win_rate = perf_data.get('winRate', 0) * 100
                
                # Accumulate for symbol totals
                symbol_performance[symbol]['total_pnl'] += pnl
                symbol_performance[symbol]['wins'] += wins
                symbol_performance[symbol]['losses'] += losses
                symbol_performance[symbol]['verdict'] = verdict
                symbol_performance[symbol]['multiplier'] = multiplier
                symbol_performance[symbol]['bots'].append(bot_id)
                
                status_icon = "[OK]" if pnl >= 0 else "[XX]"
                print(f"    {symbol:>10} {status_icon} P/L:{pnl:>8.2f} Win%:{win_rate:>5.1f}% "
                      f"({wins}W {losses}L) [{verdict}]")
        else:
            print(f"  No symbol performance data")
        
        print()
    
    db.close()
    
    # ===== PART 2: SYMBOL ANALYSIS =====
    print("\n" + "-"*100)
    print("[2] SYMBOL-LEVEL PERFORMANCE ANALYSIS\n")
    
    sorted_symbols = sorted(symbol_performance.items(), key=lambda x: x[1]['total_pnl'])
    
    print(f"{'Symbol':<12} {'Total P/L':>10} {'Wins':>6} {'Losses':>6} {'Win%':>6} {'Status':>12} {'Verdict':>12}")
    print("-"*100)
    
    losing_symbols = []
    for symbol, perf in sorted_symbols:
        total_wins = perf['wins']
        total_losses = perf['losses']
        total_trades = total_wins + total_losses
        win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
        pnl = perf['total_pnl']
        
        status = "[OK] WINNING" if pnl > 0 else "[XX] LOSING"
        verdict = perf['verdict']
        
        print(f"{symbol:<12} {pnl:>10.2f} {total_wins:>6} {total_losses:>6} {win_rate:>5.1f}% {status:>12} {verdict:>12}")
        
        if pnl < 0 and total_trades >= 3:
            losing_symbols.append((symbol, pnl, win_rate))
    
    # ===== PART 3: ISSUES & RECOMMENDATIONS =====
    print("\n" + "-"*100)
    print("[3] CRITICAL ISSUES IDENTIFIED\n")
    
    if losing_symbols:
        print(f"[URGENT] CONSISTENTLY LOSING SYMBOLS ({len(losing_symbols)}):\n")
        for symbol, pnl, wr in losing_symbols:
            print(f"   {symbol:<12} P/L: {pnl:>8.2f} USDT  Win Rate: {wr:>5.1f}%")
    
    print("\n\n" + "-"*100)
    print("[4] RECOMMENDED FIXES (Immediate Actions)\n")
    
    recommendations = [
        ("URGENT", "Disable or pause losing symbols", 
         f"Symbols: {', '.join([s[0] for s in losing_symbols[:3]])}\n"
         "These symbols have negative P/L despite multiple trades"),
        
        ("HIGH", "Increase signal threshold to 60-70",
         "Current bots entering on weak signals (40-55 range)\n"
         "     Reduce false entries by enforcing higher quality signals"),
        
        ("HIGH", "Reduce risk per trade to 2-3%",
         "Current settings may be too aggressive\n"
         "     Conserve account capital to weather losing streaks"),
        
        ("MEDIUM", "Review and tighten position sizing",
         "Position size should scale with equity\n"
         "     Avoid oversizing early trades"),
        
        ("MEDIUM", "Implement stricter profit locks",
         "Lock profits at smaller intervals (10-20 USDT)\n"
         "     Protect against sudden reversals"),
        
        ("LOW", "Monitor volatility filters",
         "Ensure very high volatility symbols are excluded\n"
         "     Focus on low-medium volatility only"),
    ]
    
    for i, (priority, action, reason) in enumerate(recommendations, 1):
        print(f"{i}. {priority} - {action}")
        print(f"   {reason}\n")
    
    print("="*100 + "\n")

if __name__ == '__main__':
    analyze_all_bots()

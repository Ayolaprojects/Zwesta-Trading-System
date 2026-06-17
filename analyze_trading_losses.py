#!/usr/bin/env python3
"""
Comprehensive trading loss analysis:
1. Bot performance by symbol and broker
2. Current risk configuration audit
3. Signal threshold appropriateness
4. Position sizing analysis
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

# Try PostgreSQL first, fallback to SQLite
try:
    import psycopg2
    from psycopg2 import sql
    USING_POSTGRES = True
except ImportError:
    USING_POSTGRES = False

DB_PATH = r'C:\zwesta-trader\Zwesta Flutter App\zwesta_trading.db'
POSTGRES_URL = os.getenv('DATABASE_URL', 'postgresql://zwesta_admin@localhost:5432/zwesta_trading')

def get_db_connection():
    """Get database connection (Postgres or SQLite)"""
    if USING_POSTGRES:
        try:
            return psycopg2.connect(POSTGRES_URL)
        except Exception as e:
            print(f"[WARN] PostgreSQL connection failed: {e}, falling back to SQLite")
    
    return sqlite3.connect(DB_PATH)

def get_trades_data():
    """Get all closed trades with P/L from backend via API or active_bots"""
    try:
        import requests
        # Try to get trade history from backend API
        resp = requests.get('http://localhost:5001/api/trades/history', timeout=5)
        if resp.status_code == 200:
            return resp.json().get('trades', [])
    except:
        pass
    
    # Fallback: return empty list (trades stored in runtime memory, not DB)
    return []

def get_active_bots():
    """Get all active bots and their configurations"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                botId, userId, symbol, broker, isLive,
                riskPerTrade, maxDailyLoss, profitLock,
                managementProfile, signalThreshold,
                maxOpenPositions, createdAt
            FROM user_bots
            WHERE isActive = 1
            ORDER BY createdAt DESC
        """)
        
        rows = cursor.fetchall()
        # Convert to list of dicts for easier access
        result = []
        for row in rows:
            result.append({
                'id': row[0],
                'user_id': row[1],
                'symbol': row[2],
                'broker': row[3],
                'is_live': row[4],
                'risk_per_trade': row[5],
                'max_daily_loss': row[6],
                'profit_lock': row[7],
                'management_profile': row[8],
                'signal_threshold': row[9],
                'max_open_positions': row[10],
                'created_at': row[11],
            })
        return result
    except Exception as e:
        print(f"[ERROR] Failed to query user_bots: {e}")
        return []
    finally:
        conn.close()

def analyze_trades_by_symbol(trades):
    """Analyze trading performance grouped by symbol"""
    analysis = defaultdict(lambda: {
        'total_trades': 0,
        'winning_trades': 0,
        'losing_trades': 0,
        'win_rate': 0,
        'avg_win': 0,
        'avg_loss': 0,
        'total_pnl': 0,
        'largest_win': 0,
        'largest_loss': 0,
        'min_entry_price': float('inf'),
        'max_entry_price': 0,
    })
    
    if not trades:
        return analysis
    
    for trade in trades:
        if isinstance(trade, dict):
            symbol = trade.get('symbol', 'UNKNOWN')
            pnl = float(trade.get('pnl', 0) or 0)
            entry_price = float(trade.get('entry_price', 0) or 0)
        else:
            symbol = trade[1]  
            pnl = float(trade[8] or 0)
            entry_price = float(trade[5] or 0)
        
        stats = analysis[symbol]
        stats['total_trades'] += 1
        stats['total_pnl'] += pnl
        
        if pnl > 0:
            stats['winning_trades'] += 1
            stats['avg_win'] = (stats['avg_win'] * (stats['winning_trades'] - 1) + pnl) / stats['winning_trades']
            stats['largest_win'] = max(stats['largest_win'], pnl)
        else:
            stats['losing_trades'] += 1
            stats['avg_loss'] = (stats['avg_loss'] * (stats['losing_trades'] - 1) + pnl) / stats['losing_trades']
            stats['largest_loss'] = min(stats['largest_loss'], pnl)
        
        if entry_price > 0:
            stats['min_entry_price'] = min(stats['min_entry_price'], entry_price)
            stats['max_entry_price'] = max(stats['max_entry_price'], entry_price)
    
    # Calculate win rates
    for symbol, stats in analysis.items():
        if stats['total_trades'] > 0:
            stats['win_rate'] = (stats['winning_trades'] / stats['total_trades']) * 100
        if stats['min_entry_price'] == float('inf'):
            stats['min_entry_price'] = 0
    
    return analysis

def print_report():
    """Generate and print comprehensive analysis report"""
    print("\n" + "="*80)
    print("ZWESTA TRADING LOSS ANALYSIS")
    print("="*80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # ===== PART 1: TRADE PERFORMANCE ANALYSIS =====
    print("\n[1] TRADE PERFORMANCE BY SYMBOL")
    print("-" * 80)
    
    trades = get_trades_data()
    if not trades:
        print("⚠️  No closed trades found in database")
        return
    
    analysis = analyze_trades_by_symbol(trades)
    
    # Sort by total P/L (worst first)
    sorted_symbols = sorted(analysis.items(), key=lambda x: x[1]['total_pnl'])
    
    print(f"{'Symbol':<12} {'Trades':>6} {'Win%':>6} {'Avg W':>8} {'Avg L':>8} {'Total P/L':>10} {'Status':>12}")
    print("-" * 80)
    
    for symbol, stats in sorted_symbols:
        status = "✅ WINNING" if stats['total_pnl'] > 0 else "❌ LOSING"
        print(f"{symbol:<12} {stats['total_trades']:>6} {stats['win_rate']:>5.1f}% "
              f"{stats['avg_win']:>8.2f} {stats['avg_loss']:>8.2f} {stats['total_pnl']:>10.2f} {status:>12}")
    
    # ===== PART 2: RISK CONFIGURATION AUDIT =====
    print("\n\n[2] ACTIVE BOT CONFIGURATIONS")
    print("-" * 80)
    
    bots = get_active_bots()
    if not bots:
        print("⚠️  No active bots found")
        return
    
    print(f"{'Bot':>8} {'Symbol':<12} {'Broker':<10} {'Profile':<15} {'Signal':>6} {'Risk%':>6} {'Max Daily Loss':>14}")
    print("-" * 80)
    
    for bot in bots:
        bot_id = bot.get('id', 'N/A')
        symbol = bot.get('symbol', 'N/A')
        broker = bot.get('broker', 'N/A')
        profile = bot.get('management_profile', 'N/A')
        signal_thr = bot.get('signal_threshold', 'N/A')
        risk = bot.get('risk_per_trade', 'N/A')
        max_loss = bot.get('max_daily_loss', 'N/A')
        
        print(f"{str(bot_id)[:8]:>8} {str(symbol):<12} {str(broker):<10} {str(profile):<15} "
              f"{str(signal_thr):>6} {str(risk):>6} {str(max_loss):>14}")
    
    # ===== PART 3: PROBLEM IDENTIFICATION =====
    print("\n\n[3] IDENTIFIED PROBLEMS & RECOMMENDATIONS")
    print("-" * 80)
    
    problems = []
    
    # Check for consistently losing symbols
    losing_symbols = [s for s, stats in sorted_symbols if stats['win_rate'] < 40 and stats['total_trades'] >= 5]
    if losing_symbols:
        problems.append(f"❌ Consistently Losing Symbols (< 40% win rate, 5+ trades):\n   {', '.join(losing_symbols)}")
    
    # Check for weak signal thresholds
    weak_signal_bots = [b for b in bots if b.get('signal_threshold', 100) < 45]
    if weak_signal_bots:
        count = len(weak_signal_bots)
        problems.append(f"⚠️  {count} bots with weak signal thresholds (< 45)")
    
    # Check for high risk settings
    high_risk_bots = [b for b in bots if float(b.get('risk_per_trade', 0) or 0) > 15]
    if high_risk_bots:
        count = len(high_risk_bots)
        problems.append(f"⚠️  {count} bots with high risk per trade (> 15%)")
    
    # Check for high daily loss limits
    high_loss_bots = [b for b in bots if float(b.get('max_daily_loss', 0) or 0) > 100]
    if high_loss_bots:
        count = len(high_loss_bots)
        problems.append(f"⚠️  {count} bots with high daily loss limits (> $100)")
    
    if problems:
        for i, problem in enumerate(problems, 1):
            print(f"\n{i}. {problem}")
    else:
        print("✅ No obvious configuration problems detected")
    
    # ===== PART 4: RECOMMENDATIONS =====
    print("\n\n[4] RECOMMENDED FIXES (Priority Order)")
    print("-" * 80)
    
    recommendations = [
        ("🔴 HIGH", "Pause or disable bots trading losing symbols", 
         f"Symbols: {', '.join(losing_symbols) if losing_symbols else 'None'}"),
        ("🔴 HIGH", "Increase minimum signal threshold to 60+",
         "Current threshold too permissive, entering low-quality trades"),
        ("🟡 MEDIUM", "Reduce risk per trade to 3-5%",
         "Current settings too aggressive for account size"),
        ("🟡 MEDIUM", "Reduce daily loss limit proportionally",
         "Allow smaller daily losses to stop bleeding early"),
        ("🟢 LOW", "Enable profit locks on all bots",
         "Lock in gains before reversals"),
        ("🟢 LOW", "Review symbol volatility filters",
         "Avoid very high volatility on small accounts"),
    ]
    
    for priority, action, reason in recommendations:
        print(f"\n{priority} {action}")
        print(f"   Reason: {reason}")
    
    # ===== PART 5: QUICK STATS =====
    print("\n\n[5] OVERALL STATISTICS")
    print("-" * 80)
    
    total_trades = sum(s['total_trades'] for s in analysis.values())
    total_wins = sum(s['winning_trades'] for s in analysis.values())
    total_pnl = sum(s['total_pnl'] for s in analysis.values())
    overall_win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
    
    print(f"Total Trades:        {total_trades}")
    print(f"Total Winning:       {total_wins} ({overall_win_rate:.1f}%)")
    print(f"Total P/L:           {total_pnl:.2f} ZAR")
    print(f"Avg P/L per Trade:   {total_pnl/total_trades:.2f} ZAR" if total_trades > 0 else "N/A")
    print(f"Symbols Trading:     {len(analysis)}")
    print(f"Active Bots:         {len(bots)}")
    
    print("\n" + "="*80 + "\n")

if __name__ == '__main__':
    try:
        print_report()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

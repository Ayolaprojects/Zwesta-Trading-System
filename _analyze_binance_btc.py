#!/usr/bin/env python3
"""
Analyze actual Binance BTCUSDT performance from database
"""
import sqlite3
import json
from datetime import datetime, timedelta
from collections import defaultdict

DB_PATH = r'C:\backend\zwesta_trading.db'

def analyze_binance_btc():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    print("=" * 80)
    print("📊 BINANCE BTCUSDT PERFORMANCE ANALYSIS")
    print("=" * 80)
    print()
    
    # Get Binance bot ID
    cur.execute("""
        SELECT bot_id, name, runtime_state, broker_account_id
        FROM user_bots
        WHERE broker_account_id LIKE 'Binance_%'
        ORDER BY created_at DESC
        LIMIT 1
    """)
    bot = cur.fetchone()
    
    if not bot:
        print("❌ No Binance bot found!")
        return
    
    bot_id = bot['bot_id']
    print(f"🤖 Bot: {bot['name']} (ID: {bot_id})")
    print(f"   Broker Account: {bot['broker_account_id']}")
    
    rs = json.loads(bot['runtime_state']) if bot['runtime_state'] else {}
    print(f"   Status: {rs.get('pauseReason', 'ACTIVE')}")
    print(f"   Symbols: {rs.get('symbols', [])}")
    print()
    
    # Get all BTCUSDT trades
    cur.execute("""
        SELECT 
            trade_id,
            symbol,
            order_type,
            price,
            volume,
            profit,
            commission,
            created_at,
            closed_at,
            status
        FROM trades
        WHERE bot_id = ?
        AND symbol LIKE '%BTC%'
        AND status = 'closed'
        ORDER BY closed_at DESC
    """, (bot_id,))
    
    trades = cur.fetchall()
    
    if not trades:
        print("❌ No BTCUSDT trades found in database!")
        print()
        print("   This means the trades shown in your screenshot are either:")
        print("   1. From a different database/bot")
        print("   2. Not yet synced to the database")
        print("   3. Using a different symbol name")
        print()
        
        # Check all Binance trades
        cur.execute("""
            SELECT DISTINCT symbol
            FROM trades
            WHERE bot_id = ?
            ORDER BY symbol
        """, (bot_id,))
        all_symbols = [r['symbol'] for r in cur.fetchall()]
        print(f"   All symbols traded by this bot: {all_symbols}")
        return
    
    print(f"📈 FOUND {len(trades)} BTCUSDT TRADES")
    print("=" * 80)
    print()
    
    # Calculate statistics
    wins = [t for t in trades if t['profit'] and t['profit'] > 0]
    losses = [t for t in trades if t['profit'] and t['profit'] < 0]
    breakevens = [t for t in trades if t['profit'] == 0]
    
    total_pnl = sum(t['profit'] for t in trades if t['profit'])
    total_wins_pnl = sum(t['profit'] for t in wins)
    total_losses_pnl = abs(sum(t['profit'] for t in losses))
    
    win_rate = len(wins) / len(trades) * 100 if trades else 0
    pf = total_wins_pnl / total_losses_pnl if total_losses_pnl > 0 else 999
    
    avg_win = total_wins_pnl / len(wins) if wins else 0
    avg_loss = total_losses_pnl / len(losses) if losses else 0
    
    print(f"💰 OVERALL PERFORMANCE:")
    print(f"   Total Trades: {len(trades)}")
    print(f"   Wins: {len(wins)} ({win_rate:.1f}%)")
    print(f"   Losses: {len(losses)} ({len(losses)/len(trades)*100:.1f}%)")
    print(f"   Breakevens: {len(breakevens)}")
    print()
    print(f"   Net P&L: ${total_pnl:.2f}")
    print(f"   Gross Wins: ${total_wins_pnl:.2f}")
    print(f"   Gross Losses: ${total_losses_pnl:.2f}")
    print(f"   Profit Factor: {pf:.2f}")
    print()
    print(f"   Average Win: ${avg_win:.2f}")
    print(f"   Average Loss: ${avg_loss:.2f}")
    print(f"   Win/Loss Ratio: {avg_win/avg_loss:.2f}" if avg_loss > 0 else "   Win/Loss Ratio: ∞")
    print()
    
    # Last 8 days analysis
    eight_days_ago = datetime.now() - timedelta(days=8)
    recent_trades = [t for t in trades if t['closed_at'] and 
                     datetime.fromisoformat(t['closed_at'].replace('Z', '+00:00')).replace(tzinfo=None) > eight_days_ago]
    
    if recent_trades:
        recent_wins = [t for t in recent_trades if t['profit'] and t['profit'] > 0]
        recent_losses = [t for t in recent_trades if t['profit'] and t['profit'] < 0]
        recent_pnl = sum(t['profit'] for t in recent_trades if t['profit'])
        recent_wins_pnl = sum(t['profit'] for t in recent_wins)
        recent_losses_pnl = abs(sum(t['profit'] for t in recent_losses))
        recent_wr = len(recent_wins) / len(recent_trades) * 100 if recent_trades else 0
        recent_pf = recent_wins_pnl / recent_losses_pnl if recent_losses_pnl > 0 else 999
        
        print("=" * 80)
        print("📅 LAST 8 DAYS PERFORMANCE:")
        print("=" * 80)
        print()
        print(f"   Total Trades: {len(recent_trades)}")
        print(f"   Wins: {len(recent_wins)} ({recent_wr:.1f}%)")
        print(f"   Losses: {len(recent_losses)}")
        print()
        print(f"   Net P&L: ${recent_pnl:.2f}")
        print(f"   Gross Wins: ${recent_wins_pnl:.2f}")
        print(f"   Gross Losses: ${recent_losses_pnl:.2f}")
        print(f"   Profit Factor: {recent_pf:.2f}")
        print()
        
        if recent_pnl > 0:
            print(f"   ✅ PROFITABLE over last 8 days!")
        else:
            print(f"   ❌ Unprofitable over last 8 days")
        print()
    
    # Show last 20 trades
    print("=" * 80)
    print("📋 LAST 20 TRADES:")
    print("=" * 80)
    print()
    
    for i, t in enumerate(trades[:20], 1):
        pnl = t['profit'] if t['profit'] else 0
        order_type = t['order_type'].upper() if t['order_type'] else '?'
        qty = t['volume'] if t['volume'] else 0
        
        result = "✅ WIN" if pnl > 0 else "❌ LOSS" if pnl < 0 else "⚪ BE"
        
        closed_date = "Unknown"
        if t['closed_at']:
            try:
                dt = datetime.fromisoformat(t['closed_at'].replace('Z', '+00:00'))
                closed_date = dt.strftime('%Y-%m-%d %H:%M')
            except:
                closed_date = t['closed_at'][:16]
        
        print(f"{i:2}. {order_type:4} Vol: {qty:.2f} | ${pnl:+7.2f} | {closed_date} | {result}")
    
    print()
    
    # Verdict
    print("=" * 80)
    print("🎯 VERDICT:")
    print("=" * 80)
    print()
    
    if total_pnl > 0 and win_rate > 45 and pf > 1.0:
        print(f"   ✅ BTCUSDT is PROFITABLE!")
        print(f"   📊 Stats: {win_rate:.1f}% WR, PF={pf:.2f}, Net=${total_pnl:.2f}")
        print()
        print(f"   🚀 RECOMMENDATION:")
        print(f"      1. REMOVE from blacklist")
        print(f"      2. UNPAUSE Binance bot")
        print(f"      3. ADD 'BTCUSDT' to symbols")
        if pf > 1.3 and win_rate > 50:
            print(f"      4. Consider applying 10x multiplier (PF={pf:.2f} is excellent!)")
        print()
    else:
        print(f"   ⚠️ BTCUSDT performance is mixed")
        print(f"   📊 Stats: {win_rate:.1f}% WR, PF={pf:.2f}, Net=${total_pnl:.2f}")
        print()
        if total_pnl < 0:
            print(f"   ❌ Net negative, keep paused")
        elif win_rate < 45:
            print(f"   ❌ Win rate too low (<45%), risky")
        elif pf < 1.0:
            print(f"   ❌ Profit factor < 1.0, losing strategy")
        print()
    
    conn.close()

if __name__ == "__main__":
    analyze_binance_btc()

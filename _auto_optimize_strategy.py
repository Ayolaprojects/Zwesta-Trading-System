"""
Intelligent Strategy Optimizer - Automatically select best trading strategy
Analyzes historical performance and configures bots for optimal results
"""
import sqlite3
import json
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict

DB_PATH = r"C:\backend\zwesta_trading.db"
TRADES_CSV = r"C:\Users\zwexm\Downloads\01_01_2007-27_05_2026.csv"

def analyze_symbol_performance(df):
    """Analyze which symbols are actually profitable"""
    symbol_stats = {}
    
    for symbol in df['symbol'].unique():
        symbol_trades = df[df['symbol'] == symbol]
        
        total_pnl = symbol_trades['profit'].sum()
        win_rate = len(symbol_trades[symbol_trades['profit'] > 0]) / len(symbol_trades) * 100
        avg_win = symbol_trades[symbol_trades['profit'] > 0]['profit'].mean() if len(symbol_trades[symbol_trades['profit'] > 0]) > 0 else 0
        avg_loss = symbol_trades[symbol_trades['profit'] < 0]['profit'].mean() if len(symbol_trades[symbol_trades['profit'] < 0]) > 0 else 0
        rr_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        
        # Calculate profit factor
        total_wins = symbol_trades[symbol_trades['profit'] > 0]['profit'].sum()
        total_losses = abs(symbol_trades[symbol_trades['profit'] < 0]['profit'].sum())
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        symbol_stats[symbol] = {
            'trades': len(symbol_trades),
            'pnl': total_pnl,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'rr_ratio': rr_ratio,
            'profit_factor': profit_factor,
            'score': 0  # Will calculate below
        }
    
    # Calculate composite score: (win_rate * profit_factor * rr_ratio) / 100
    for symbol, stats in symbol_stats.items():
        stats['score'] = (stats['win_rate'] * stats['profit_factor'] * stats['rr_ratio']) / 100
    
    return symbol_stats

def categorize_symbols(symbol_stats):
    """Categorize symbols into tiers based on performance"""
    tier_a = []  # Profitable, high win rate, good RR
    tier_b = []  # Breakeven or small profit, decent metrics
    tier_c = []  # Losing but salvageable (good win rate OR good RR)
    tier_d = []  # Remove completely
    
    for symbol, stats in symbol_stats.items():
        if stats['trades'] < 10:
            continue  # Skip low sample size
        
        # Tier A: Profitable + (Win rate > 40% OR Profit factor > 1.0)
        if stats['pnl'] > 50 and (stats['win_rate'] > 40 or stats['profit_factor'] > 1.0):
            tier_a.append(symbol)
        
        # Tier B: Breakeven to small loss + reasonable metrics
        elif stats['pnl'] > -100 and stats['win_rate'] > 35 and stats['profit_factor'] > 0.7:
            tier_b.append(symbol)
        
        # Tier C: Losing but has potential (high win rate OR good RR)
        elif stats['win_rate'] > 50 or (stats['rr_ratio'] > 1.5 and stats['win_rate'] > 35):
            tier_c.append(symbol)
        
        # Tier D: Remove
        else:
            tier_d.append(symbol)
    
    return tier_a, tier_b, tier_c, tier_d

def generate_optimal_strategy(tier_a, tier_b, tier_c, tier_d, symbol_stats):
    """Generate optimal bot configuration based on symbol tiers"""
    
    strategy = {
        'name': 'Data-Driven Optimized Strategy',
        'generated_at': datetime.now().isoformat(),
        'signal_threshold': 70,  # Higher threshold = more selective
        'max_open_positions': 2,
        'max_positions_per_symbol': 1,
        'management_profile': 'balanced',
        
        # Symbol allocation
        'focus_symbols': tier_a,  # Trade most
        'secondary_symbols': tier_b,  # Trade less
        'experimental_symbols': tier_c[:2] if tier_c else [],  # Test carefully
        'blacklisted_symbols': tier_d,  # Don't trade
        
        # Risk settings based on tier
        'tier_a_multiplier': 1.2,  # Increase size on winners
        'tier_b_multiplier': 0.8,  # Reduce size on breakeven
        'tier_c_multiplier': 0.4,  # Minimal size on experimental
        
        # Stop loss optimization (reduce SL hits from 28% to 20%)
        'stop_loss_buffer': 1.3,  # 30% wider stops
        
        # Take profit optimization (increase TP hits from 5% to 15%)
        'use_trailing_stop': True,
        'partial_tp_enabled': True,
        'tp_levels': [
            {'target': 1.5, 'close_percent': 30},  # Close 30% at 1.5R
            {'target': 2.5, 'close_percent': 40},  # Close 40% at 2.5R
            {'target': 4.0, 'close_percent': 30},  # Let 30% run to 4R
        ],
        
        # Recommendations
        'recommendations': []
    }
    
    # Add specific recommendations
    if tier_a:
        strategy['recommendations'].append(f"✅ FOCUS: Trade {', '.join(tier_a)} - your only profitable symbols")
    else:
        strategy['recommendations'].append("⚠️ WARNING: No profitable symbols found - consider DEMO mode")
    
    if tier_d:
        strategy['recommendations'].append(f"❌ REMOVE: Stop trading {', '.join(tier_d)} - consistent losers")
    
    # Calculate expected improvement
    total_trades_in_losers = sum(symbol_stats[s]['trades'] for s in tier_d)
    total_loss_from_losers = sum(symbol_stats[s]['pnl'] for s in tier_d)
    
    if total_trades_in_losers > 0:
        strategy['expected_improvement'] = {
            'trades_eliminated': total_trades_in_losers,
            'losses_avoided': abs(total_loss_from_losers),
            'percentage_saved': abs(total_loss_from_losers) / 1908.63 * 100  # From total loss
        }
    
    return strategy

def apply_strategy_to_bots(strategy):
    """Apply optimized strategy to all active bots"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    cur.execute("SELECT bot_id, runtime_state FROM user_bots WHERE enabled = 1")
    bots = cur.fetchall()
    
    updates = []
    
    for bot in bots:
        bot_id = bot['bot_id']
        rs = json.loads(bot['runtime_state'] or '{}')
        broker = rs.get('brokerName', '').lower()
        
        # Get current symbols
        current_symbols = rs.get('symbols', [])
        
        # Filter symbols based on strategy - GROUPED BY TIER (A first, then B, then C)
        tier_a_symbols = []  # Focus - most profitable
        tier_b_symbols = []  # Secondary - breakeven
        tier_c_symbols = []  # Experimental - minimal exposure
        
        for symbol in current_symbols:
            symbol_base = symbol.replace('m', '').replace('USDT', '')
            
            # Check if symbol should be removed (Tier D blacklist)
            blacklisted = any(symbol_base in bl for bl in strategy['blacklisted_symbols'])
            if blacklisted:
                continue
            
            # Categorize by tier (group profitable symbols at the top)
            in_focus = any(symbol_base in fc for fc in strategy['focus_symbols'])
            in_secondary = any(symbol_base in sc for sc in strategy['secondary_symbols'])
            in_experimental = any(symbol_base in ex for ex in strategy['experimental_symbols'])
            
            if in_focus:
                tier_a_symbols.append(symbol)
            elif in_secondary:
                tier_b_symbols.append(symbol)
            elif in_experimental:
                tier_c_symbols.append(symbol)
        
        # Add focus symbols if not already included (for forex symbols)
        if broker == 'exness':
            for focus in strategy['focus_symbols']:
                symbol_with_suffix = focus + 'm' if not focus.endswith('m') else focus
                if symbol_with_suffix not in tier_a_symbols:
                    tier_a_symbols.append(symbol_with_suffix)
        
        # Combine symbols with profitable ones at the top
        new_symbols = tier_a_symbols + tier_b_symbols + tier_c_symbols
        
        # Update configuration
        updates_made = {
            'symbols': new_symbols,
            'signalThreshold': strategy['signal_threshold'],
            'maxOpenPositions': strategy['max_open_positions'],
            'maxPositionsPerSymbol': strategy['max_positions_per_symbol'],
            'managementProfile': strategy['management_profile'],
            'strategyVersion': 'optimized_v1',
            'lastOptimized': datetime.now().isoformat(),
        }
        
        rs.update(updates_made)
        
        cur.execute("UPDATE user_bots SET runtime_state = ? WHERE bot_id = ?",
                   (json.dumps(rs), bot_id))
        
        updates.append({
            'bot_id': bot_id,
            'old_symbols': current_symbols,
            'new_symbols': new_symbols,
            'changes': updates_made
        })
    
    conn.commit()
    conn.close()
    
    return updates

def main():
    print("=" * 80)
    print("🤖 INTELLIGENT STRATEGY OPTIMIZER")
    print("=" * 80)
    print()
    
    # Load trade data
    print("📊 Loading trade history...")
    df = pd.read_csv(TRADES_CSV)
    print(f"   Loaded {len(df)} trades")
    print()
    
    # Analyze symbols
    print("🔍 Analyzing symbol performance...")
    symbol_stats = analyze_symbol_performance(df)
    
    # Categorize symbols
    tier_a, tier_b, tier_c, tier_d = categorize_symbols(symbol_stats)
    
    print()
    print("📈 SYMBOL PERFORMANCE ANALYSIS:")
    print()
    
    print("🥇 TIER A - PROFITABLE (Trade These):")
    if tier_a:
        for symbol in tier_a:
            stats = symbol_stats[symbol]
            print(f"   ✅ {symbol}: {stats['pnl']:+.2f} ZAR | "
                  f"{stats['win_rate']:.0f}% WR | PF={stats['profit_factor']:.2f} | "
                  f"RR={stats['rr_ratio']:.2f}")
    else:
        print("   ⚠️  None found - system needs major overhaul")
    print()
    
    print("🥈 TIER B - BREAKEVEN (Trade Cautiously):")
    if tier_b:
        for symbol in tier_b:
            stats = symbol_stats[symbol]
            print(f"   ⚪ {symbol}: {stats['pnl']:+.2f} ZAR | "
                  f"{stats['win_rate']:.0f}% WR | PF={stats['profit_factor']:.2f}")
    else:
        print("   None")
    print()
    
    print("🥉 TIER C - EXPERIMENTAL (Minimal Exposure):")
    if tier_c:
        for symbol in tier_c[:3]:
            stats = symbol_stats[symbol]
            print(f"   🔬 {symbol}: {stats['pnl']:+.2f} ZAR | "
                  f"{stats['win_rate']:.0f}% WR | RR={stats['rr_ratio']:.2f}")
    else:
        print("   None")
    print()
    
    print("❌ TIER D - REMOVE (Stop Trading):")
    if tier_d:
        total_loss = sum(symbol_stats[s]['pnl'] for s in tier_d)
        total_trades = sum(symbol_stats[s]['trades'] for s in tier_d)
        print(f"   Combined: {len(tier_d)} symbols, {total_trades} trades, {total_loss:.2f} ZAR loss")
        for symbol in sorted(tier_d, key=lambda x: symbol_stats[x]['pnl'])[:5]:
            stats = symbol_stats[symbol]
            print(f"   ❌ {symbol}: {stats['pnl']:+.2f} ZAR | "
                  f"{stats['win_rate']:.0f}% WR | PF={stats['profit_factor']:.2f}")
    print()
    
    # Generate optimal strategy
    print("🎯 Generating optimal strategy...")
    strategy = generate_optimal_strategy(tier_a, tier_b, tier_c, tier_d, symbol_stats)
    
    print()
    print("=" * 80)
    print("📋 RECOMMENDED STRATEGY")
    print("=" * 80)
    print()
    print(f"Strategy: {strategy['name']}")
    print(f"Signal Threshold: {strategy['signal_threshold']} (more selective)")
    print(f"Max Positions: {strategy['max_open_positions']}")
    print(f"Management: {strategy['management_profile']}")
    print()
    
    print("🎯 Symbol Allocation:")
    if strategy['focus_symbols']:
        print(f"   Focus (1.2x size): {', '.join(strategy['focus_symbols'])}")
    if strategy['secondary_symbols']:
        print(f"   Secondary (0.8x): {', '.join(strategy['secondary_symbols'])}")
    if strategy['experimental_symbols']:
        print(f"   Experimental (0.4x): {', '.join(strategy['experimental_symbols'])}")
    if strategy['blacklisted_symbols']:
        print(f"   ❌ Blacklist: {', '.join(strategy['blacklisted_symbols'])}")
    print()
    
    print("💡 Key Improvements:")
    for rec in strategy['recommendations']:
        print(f"   {rec}")
    print()
    
    if 'expected_improvement' in strategy:
        imp = strategy['expected_improvement']
        print(f"💰 Expected Improvement:")
        print(f"   Eliminate {imp['trades_eliminated']} losing trades")
        print(f"   Avoid {imp['losses_avoided']:.2f} ZAR in losses")
        print(f"   Save {imp['percentage_saved']:.1f}% of historical losses")
        print()
    
    # Ask for confirmation
    print("=" * 80)
    response = input("Apply this strategy to all active bots? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        print()
        print("⚙️  Applying strategy to bots...")
        updates = apply_strategy_to_bots(strategy)
        
        print()
        print("✅ STRATEGY APPLIED TO BOTS:")
        for update in updates:
            print(f"   Bot {update['bot_id']}:")
            print(f"      Old symbols: {update['old_symbols']}")
            print(f"      New symbols: {update['new_symbols']}")
        
        print()
        print("🔄 Restart the backend to activate changes:")
        print("   taskkill /F /IM python.exe")
        print("   cd C:\\backend")
        print("   python multi_broker_backend_updated.py")
        
        # Save strategy to file
        strategy_file = r"C:\backend\optimal_strategy.json"
        with open(strategy_file, 'w') as f:
            json.dump(strategy, f, indent=2)
        print()
        print(f"💾 Strategy saved to: {strategy_file}")
        
    else:
        print()
        print("❌ Strategy not applied. Review recommendations and run again when ready.")
    
    print()
    print("=" * 80)

if __name__ == "__main__":
    main()

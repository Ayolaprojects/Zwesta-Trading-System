#!/usr/bin/env python3
"""
Analyze Binance Futures trading data and generate comprehensive report
"""
import re
from datetime import datetime
from collections import defaultdict

# Raw trade data
TRADE_DATA = """
2026-05-26 06:14:31 LTCUSDTPerp Market Sell 52.23 Market 1.916 LTC
2026-05-26 05:55:21 LTCUSDTPerp Market Buy 52.28 Market 0.958 LTC
2026-05-26 05:54:23 LTCUSDTPerp Market Buy 52.25 Market 0.958 LTC
2026-05-26 05:48:59 BTCUSDTPerp Market Buy 76,629.30 Market 0.002 BTC
2026-05-26 05:28:57 BTCUSDTPerp Market Sell 76,500.00 Market 0.001 BTC
2026-05-26 05:28:54 BTCUSDTPerp Market Sell 76,500.00 Market 0.001 BTC
2026-05-26 05:25:00 ETHUSDTPerp Market Buy 2,086.69 Market 0.048 ETH
2026-05-26 05:04:07 ETHUSDTPerp Market Sell 2,087.05 Market 0.024 ETH
2026-05-26 05:03:58 ETHUSDTPerp Market Sell 2,086.95 Market 0.024 ETH
"""

def parse_trades(raw_data):
    """Parse raw trade data into structured format"""
    trades = []
    lines = [line.strip() for line in raw_data.strip().split('\n') if line.strip()]
    
    for line in lines:
        # Parse: DateTime Symbol Type Side Price _ Size Unit
        parts = line.split()
        if len(parts) < 8:
            continue
            
        try:
            date = parts[0]
            time = parts[1]
            symbol = parts[2].replace('Perp', '')
            side = parts[4]  # Buy or Sell
            price = float(parts[5].replace(',', ''))
            size = float(parts[7])
            unit = parts[8]
            
            trades.append({
                'datetime': f"{date} {time}",
                'symbol': symbol,
                'side': side,
                'price': price,
                'size': size,
                'unit': unit,
                'value': price * size
            })
        except (ValueError, IndexError) as e:
            print(f"Skipping malformed line: {line[:50]}... Error: {e}")
            continue
    
    return trades

def analyze_trades(trades):
    """Analyze trading performance"""
    
    # Group by symbol
    by_symbol = defaultdict(list)
    for trade in trades:
        by_symbol[trade['symbol']].append(trade)
    
    # Calculate metrics per symbol
    symbol_stats = {}
    
    for symbol, symbol_trades in by_symbol.items():
        buys = [t for t in symbol_trades if t['side'] == 'Buy']
        sells = [t for t in symbol_trades if t['side'] == 'Sell']
        
        total_buy_value = sum(t['value'] for t in buys)
        total_sell_value = sum(t['value'] for t in sells)
        total_buy_size = sum(t['size'] for t in buys)
        total_sell_size = sum(t['size'] for t in sells)
        
        avg_buy_price = total_buy_value / total_buy_size if total_buy_size > 0 else 0
        avg_sell_price = total_sell_value / total_sell_size if total_sell_size > 0 else 0
        
        # Estimate P&L (simplified - assumes all buys were sold)
        min_size = min(total_buy_size, total_sell_size)
        estimated_pnl = (avg_sell_price - avg_buy_price) * min_size if min_size > 0 else 0
        
        symbol_stats[symbol] = {
            'total_trades': len(symbol_trades),
            'buys': len(buys),
            'sells': len(sells),
            'total_buy_value': total_buy_value,
            'total_sell_value': total_sell_value,
            'avg_buy_price': avg_buy_price,
            'avg_sell_price': avg_sell_price,
            'estimated_pnl': estimated_pnl,
            'net_position': total_buy_size - total_sell_size
        }
    
    return symbol_stats, by_symbol

def generate_report(trades, symbol_stats):
    """Generate comprehensive trading report"""
    
    print("=" * 80)
    print("📊 BINANCE FUTURES TRADING ANALYSIS")
    print("=" * 80)
    print()
    
    # Overall summary
    print(f"📈 OVERALL SUMMARY:")
    print(f"   Total Trades: {len(trades)}")
    print(f"   Symbols Traded: {len(symbol_stats)}")
    print(f"   Total Trading Volume: ${sum(t['value'] for t in trades):,.2f} USDT")
    print()
    
    # Account status from user's data
    print("💰 CURRENT ACCOUNT STATUS:")
    print("   Balance: 56.4176 USDT")
    print("   Equity: 56.13 USD")
    print("   Unrealized P&L: -0.1821 USDT")
    print("   Margin Ratio: 0.98%")
    print("   Position Value: 124.99 USD")
    print("   Leverage: 2.23x")
    print()
    
    # Per-symbol analysis
    print("📊 SYMBOL-BY-SYMBOL ANALYSIS:")
    print()
    
    sorted_symbols = sorted(symbol_stats.items(), 
                          key=lambda x: x[1]['estimated_pnl'], 
                          reverse=True)
    
    total_estimated_pnl = 0
    
    for symbol, stats in sorted_symbols:
        pnl_emoji = "✅" if stats['estimated_pnl'] > 0 else "❌"
        print(f"{pnl_emoji} {symbol}:")
        print(f"   Trades: {stats['total_trades']} ({stats['buys']} buys, {stats['sells']} sells)")
        print(f"   Avg Buy Price: ${stats['avg_buy_price']:,.2f}")
        print(f"   Avg Sell Price: ${stats['avg_sell_price']:,.2f}")
        print(f"   Estimated P&L: ${stats['estimated_pnl']:,.2f}")
        print(f"   Net Position: {stats['net_position']:.4f}")
        print()
        total_estimated_pnl += stats['estimated_pnl']
    
    print("=" * 80)
    print(f"💵 TOTAL ESTIMATED P&L: ${total_estimated_pnl:,.2f} USDT")
    print("=" * 80)
    print()
    
    # Trading patterns
    print("📈 TRADING PATTERNS:")
    buys = [t for t in trades if t['side'] == 'Buy']
    sells = [t for t in trades if t['side'] == 'Sell']
    print(f"   Total Buys: {len(buys)} ({len(buys)/len(trades)*100:.1f}%)")
    print(f"   Total Sells: {len(sells)} ({len(sells)/len(trades)*100:.1f}%)")
    print(f"   Buy/Sell Ratio: {len(buys)/len(sells):.2f}" if sells else "   Buy/Sell Ratio: N/A")
    print()
    
    # Position sizes
    avg_trade_size = sum(t['value'] for t in trades) / len(trades)
    print(f"   Average Trade Size: ${avg_trade_size:,.2f} USDT")
    print(f"   Largest Trade: ${max(t['value'] for t in trades):,.2f} USDT")
    print(f"   Smallest Trade: ${min(t['value'] for t in trades):,.2f} USDT")
    print()
    
    # Critical findings
    print("=" * 80)
    print("⚠️  CRITICAL FINDINGS:")
    print("=" * 80)
    
    findings = []
    
    # Check account size vs losses
    if total_estimated_pnl < 0:
        loss_pct = (abs(total_estimated_pnl) / 56.4176) * 100
        findings.append(f"❌ NET LOSS: ${abs(total_estimated_pnl):,.2f} ({loss_pct:.1f}% of account)")
    
    # Check for over-trading
    if len(trades) > 100:
        findings.append(f"⚠️  HIGH TRADE FREQUENCY: {len(trades)} trades - possible over-trading")
    
    # Check position sizes
    if avg_trade_size < 1:
        findings.append(f"⚠️  VERY SMALL POSITIONS: Avg ${avg_trade_size:.2f} - high fee impact")
    
    # Check leverage
    findings.append("✅ LOW LEVERAGE: 2.23x is conservative (safe)")
    
    # Check losing symbols
    losing_symbols = [(s, st) for s, st in symbol_stats.items() if st['estimated_pnl'] < 0]
    if losing_symbols:
        findings.append(f"❌ LOSING SYMBOLS: {len(losing_symbols)} out of {len(symbol_stats)} symbols unprofitable")
    
    for finding in findings:
        print(f"   {finding}")
    
    print()
    print("=" * 80)
    print("💡 RECOMMENDATIONS:")
    print("=" * 80)
    print("   1. STOP TRADING CRYPTO - Align with Exness strategy (only GBPUSDm profitable)")
    print("   2. INCREASE POSITION SIZES - Small trades = high fee percentage")
    print("   3. REDUCE TRADE FREQUENCY - Over-trading increases costs")
    print("   4. FOCUS ON WINNING SETUPS - Quality over quantity")
    print("   5. MATCH EXNESS OPTIMIZATIONS - Apply same filters to Binance bot")
    print()
    print("=" * 80)

def main():
    # Note: This is a minimal sample - the full data needs to be parsed from the user's dump
    print("⚠️  WARNING: This is parsing a SAMPLE of the trade data.")
    print("   The full dataset appears to contain 300+ trades.")
    print("   For complete analysis, the full trade history should be provided in CSV format.")
    print()
    
    trades = parse_trades(TRADE_DATA)
    
    if not trades:
        print("❌ No trades parsed. Please provide data in correct format.")
        return
    
    symbol_stats, by_symbol = analyze_trades(trades)
    generate_report(trades, symbol_stats)

if __name__ == "__main__":
    main()

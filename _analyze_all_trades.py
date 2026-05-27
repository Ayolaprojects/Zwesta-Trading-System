"""Analyze all live trades from Exness account"""
import pandas as pd
from datetime import datetime

# Load trade data
df = pd.read_csv(r'C:\Users\zwexm\Downloads\01_01_2007-27_05_2026.csv')

print("=" * 80)
print("ZWESTA TRADING SYSTEM - COMPLETE LIVE TRADE ANALYSIS")
print("=" * 80)

# Basic stats
print(f"\n📊 OVERALL STATISTICS:")
print(f"  Total trades: {len(df)}")
print(f"  Date range: {df['opening_time_utc'].min()} to {df['closing_time_utc'].max()}")

# Profit analysis
total_pnl = df['profit'].sum()
winners = df[df['profit'] > 0]
losers = df[df['profit'] < 0]
breakeven = df[df['profit'] == 0]

win_rate = len(winners) / len(df) * 100 if len(df) > 0 else 0

print(f"\n💰 PROFIT & LOSS:")
print(f"  Total P&L: {total_pnl:.2f} ZAR")
print(f"  Winners: {len(winners)} trades ({len(winners)/len(df)*100:.1f}%)")
print(f"  Losers: {len(losers)} trades ({len(losers)/len(df)*100:.1f}%)")
print(f"  Breakeven: {len(breakeven)} trades")
print(f"  Win rate: {win_rate:.1f}%")

if len(winners) > 0:
    print(f"\n  Avg win: {winners['profit'].mean():.2f} ZAR")
    print(f"  Largest win: {winners['profit'].max():.2f} ZAR")
    print(f"  Total wins: {winners['profit'].sum():.2f} ZAR")

if len(losers) > 0:
    print(f"\n  Avg loss: {losers['profit'].mean():.2f} ZAR")
    print(f"  Largest loss: {losers['profit'].min():.2f} ZAR")
    print(f"  Total losses: {losers['profit'].sum():.2f} ZAR")

# Risk metrics
if len(winners) > 0 and len(losers) > 0:
    avg_win = winners['profit'].mean()
    avg_loss = abs(losers['profit'].mean())
    profit_factor = winners['profit'].sum() / abs(losers['profit'].sum()) if losers['profit'].sum() != 0 else float('inf')
    expectancy = (win_rate/100 * avg_win) - ((100-win_rate)/100 * avg_loss)
    
    print(f"\n📈 RISK METRICS:")
    print(f"  Profit factor: {profit_factor:.2f}")
    print(f"  Risk/Reward ratio: {avg_win/avg_loss:.2f}")
    print(f"  Expectancy: {expectancy:.2f} ZAR per trade")

# Symbol analysis
print(f"\n🎯 TOP TRADED SYMBOLS:")
symbol_counts = df['symbol'].value_counts().head(10)
for symbol, count in symbol_counts.items():
    symbol_pnl = df[df['symbol'] == symbol]['profit'].sum()
    symbol_win_rate = len(df[(df['symbol'] == symbol) & (df['profit'] > 0)]) / count * 100
    print(f"  {symbol}: {count} trades, {symbol_pnl:+.2f} ZAR, {symbol_win_rate:.0f}% win rate")

# Daily performance
df['date'] = pd.to_datetime(df['closing_time_utc']).dt.date
daily_pnl = df.groupby('date')['profit'].sum().sort_index()

print(f"\n📅 DAILY PERFORMANCE (Last 10 days):")
for date, pnl in daily_pnl.tail(10).items():
    trades = len(df[df['date'] == date])
    print(f"  {date}: {pnl:+8.2f} ZAR ({trades} trades)")

# Close reasons
print(f"\n🚪 CLOSE REASONS:")
close_reasons = df['close_reason'].value_counts()
for reason, count in close_reasons.items():
    pct = count / len(df) * 100
    print(f"  {reason}: {count} ({pct:.1f}%)")

# Position sizes
print(f"\n📊 POSITION SIZE DISTRIBUTION:")
print(f"  Min: {df['lots'].min():.2f} lots")
print(f"  Max: {df['lots'].max():.2f} lots")
print(f"  Avg: {df['lots'].mean():.2f} lots")
print(f"  Median: {df['lots'].median():.2f} lots")

# Recent performance (last 24 hours)
recent = df[pd.to_datetime(df['closing_time_utc']) > pd.Timestamp.now() - pd.Timedelta(hours=24)]
if len(recent) > 0:
    print(f"\n⏰ LAST 24 HOURS:")
    print(f"  Trades: {len(recent)}")
    print(f"  P&L: {recent['profit'].sum():+.2f} ZAR")
    print(f"  Win rate: {len(recent[recent['profit'] > 0])/len(recent)*100:.1f}%")

print("\n" + "=" * 80)

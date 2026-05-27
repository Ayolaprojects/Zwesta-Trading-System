import requests
import json

headers = {'X-Session-Token': '81c471de50030ec8db3fa96b652315ce07b001f25d1b2c543ff27344ba2ff2e6'}
response = requests.get('http://localhost:9000/api/bot/status', headers=headers)
bots = response.json()

# Find Binance Futures bot
binance_bot = None
for bot in bots:
    if 'Binance' in bot.get('broker_type', ''):
        binance_bot = bot
        break

if not binance_bot:
    print('No Binance bot found')
    exit(1)

# Extract key information
print('='*80)
print('BINANCE FUTURES BOT ANALYSIS')
print('='*80)
print()

# Account & Position Info
print('ACCOUNT INFORMATION:')
print(f'  Account Balance/Equity: ')
print(f'  Current Leverage: {binance_bot.get("leverage", "N/A")}x')
print(f'  Trade Amount: ')
print(f'  Risk Profile: {binance_bot.get("risk_profile", "N/A")}')
print(f'  Max Open Positions: {binance_bot.get("max_open_positions", "N/A")}')
print()

# Performance Metrics
print('PERFORMANCE METRICS:')
daily_profit = binance_bot.get('daily_profit', 0)
total_profit = binance_bot.get('total_profit', 0)
win_rate = binance_bot.get('win_rate', 0)
print(f'  Daily Profit: ')
print(f'  Total Profit: ')
print(f'  Win Rate: {win_rate:.1f}%')
print()

# Trade Adaptation
print('TRADE ADAPTATION:')
trade_adaptation = binance_bot.get('tradeAmountAdaptation', {})
multiplier = trade_adaptation.get('currentMultiplier', 1.0)
print(f'  Current Multiplier: {multiplier:.2f}x')
print(f'  Management State: {binance_bot.get("management_state", "N/A")}')
print()

# Calculate Realistic Profit Potential
balance = binance_bot.get('account_balance', 0)
if balance > 0:
    print('='*80)
    print('PROFIT POTENTIAL ANALYSIS')
    print('='*80)
    print()
    
    daily_rate = (daily_profit / balance) * 100 if balance > 0 else 0
    monthly_projection = daily_rate * 30
    
    print(f'  Daily Profit Rate: {daily_rate:.2f}%')
    print(f'  Monthly Projection: {monthly_projection:.2f}%')
    
    if daily_rate > 0:
        # Time to 10x (900% profit needed)
        days_to_10x = 900 / daily_rate
        print(f'  Days to 10x at current rate: {days_to_10x:.0f} days ({days_to_10x/30:.1f} months)')
        
        # With aggressive scaling (assume 50% higher rate)
        aggressive_rate = daily_rate * 1.5
        days_aggressive = 900 / aggressive_rate
        print(f'  Days to 10x with 50% scaling: {days_aggressive:.0f} days ({days_aggressive/30:.1f} months)')
    print()

# Risk Assessment
print('='*80)
print('RISK ASSESSMENT')
print('='*80)
print()

print('  Drawdown Protection:')
max_drawdown = binance_bot.get('max_drawdown_percent', 'N/A')
print(f'    Max Drawdown: {max_drawdown}%' if max_drawdown != 'N/A' else '    Max Drawdown: Not configured')

print()
print('  Daily Loss Limits:')
max_daily_loss = binance_bot.get('max_daily_loss', 'N/A')
print(f'    Max Daily Loss: ' if max_daily_loss != 'N/A' else '    Max Daily Loss: Not configured')

print()
print('  Leverage Risk:')
leverage = binance_bot.get('leverage', 0)
if leverage >= 20:
    risk_level = 'VERY HIGH'
elif leverage >= 10:
    risk_level = 'HIGH'
elif leverage >= 5:
    risk_level = 'MODERATE'
else:
    risk_level = 'LOW'
print(f'    Leverage: {leverage}x ({risk_level} RISK)')

print()
print('  Position Sizing:')
trade_amount = binance_bot.get('trade_amount', 0)
position_size_pct = (trade_amount / balance * 100) if balance > 0 else 0
print(f'    Trade Amount:  ({position_size_pct:.1f}% of balance)')
max_positions = binance_bot.get('max_open_positions', 1)
max_exposure = trade_amount * max_positions
max_exposure_pct = (max_exposure / balance * 100) if balance > 0 else 0
print(f'    Max Exposure:  ({max_exposure_pct:.1f}% of balance)')

print()
print('='*80)
print('10X ACHIEVABILITY ASSESSMENT')
print('='*80)
print()

if daily_rate <= 0:
    print('VERDICT: NOT ACHIEVABLE')
    print('Reason: Bot is not currently profitable on a daily basis')
elif daily_rate < 0.5:
    print('VERDICT: UNLIKELY (Multi-year timeframe)')
    print(f'Reason: At {daily_rate:.2f}% daily, would take {days_to_10x/365:.1f} years')
elif daily_rate < 1.0:
    print('VERDICT: POSSIBLE (1-3 year timeframe)')
    print(f'Reason: At {daily_rate:.2f}% daily, would take {days_to_10x/365:.1f} years')
    print('Conditions needed: Consistent performance, no major drawdowns')
elif daily_rate < 2.0:
    print('VERDICT: ACHIEVABLE (6-18 months)')
    print(f'Reason: At {daily_rate:.2f}% daily, would take {days_to_10x/30:.1f} months')
    print('Conditions needed: Maintain win rate, scale position sizes, compound profits')
else:
    print('VERDICT: HIGHLY ACHIEVABLE (3-12 months)')
    print(f'Reason: At {daily_rate:.2f}% daily, would take {days_to_10x/30:.1f} months')
    print('WARNING: High return rates may not be sustainable long-term')

print()
print('Key Risk Factors:')
print(f'  - Leverage risk is {risk_level}')
print(f'  - Position exposure up to {max_exposure_pct:.1f}% of balance')
print(f'  - Win rate of {win_rate:.1f}% needs to be maintained')
print(f'  - Market conditions must remain favorable')
print()


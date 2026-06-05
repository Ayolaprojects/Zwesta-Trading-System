import json

data = json.load(open('bot_status.json'))
binance_bots = [b for b in data.get('bots',[]) if b.get('broker_type')=='Binance']

print("BINANCE BOT RISK PROTECTION CHECK\n")
print("=" * 60)

for b in binance_bots:
    print(f"\nBot: {b['botId']}")
    print(f"  Account Balance: ${b.get('accountBalance', 'N/A'):.2f}")
    print(f"  Daily Loss Limit: ${b.get('maxDailyLoss', 'NOT SET')}")
    print(f"  Max Open Positions: {b.get('maxOpenPositions', 'NOT SET')}")
    print(f"  Leverage: {b.get('binanceFuturesBaseLeverage', 'N/A')}x")
    print(f"  Current Drawdown: {b.get('maxDrawdown', 0):.2f}%")
    print(f"  Daily P&L: ${b.get('dailyProfit', 0):.2f}")
    print(f"  Total P&L: ${b.get('totalProfit', 0):.2f}")
    print(f"  Profit Lock: ${b.get('profitLock', 'NOT SET')}")
    print(f"  Status: {b.get('status')}")
    print(f"  Enabled: {b.get('enabled')}")
    print(f"  Management State: {b.get('managementState', 'N/A')}")
    
    # Check if protections are active
    max_daily = b.get('maxDailyLoss')
    if not max_daily or max_daily == 0:
        print(f"  ❌ NO DAILY LOSS LIMIT SET!")
    
    leverage = b.get('binanceFuturesBaseLeverage')
    if leverage and leverage > 2:
        print(f"  ⚠️  HIGH LEVERAGE: {leverage}x (should be 2x)")
    
    if b.get('managementState') == 'recovery':
        print(f"  ⚠️  Bot in RECOVERY mode (hitting losses)")

print("\n" + "=" * 60)

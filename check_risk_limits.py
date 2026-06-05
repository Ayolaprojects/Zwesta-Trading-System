import json

data = json.load(open('bot_status.json'))
exness_bots = [b for b in data.get('bots',[]) if b.get('broker_type')=='Exness']

print("EXNESS BOT RISK PROTECTION CHECK\n")
print("=" * 60)

for b in exness_bots:
    print(f"\nBot: {b['botId']}")
    print(f"  Account Balance: ${b.get('accountBalance', 'N/A'):.2f}")
    print(f"  Daily Loss Limit: ${b.get('maxDailyLoss', 'NOT SET')}")
    print(f"  Drawdown Pause %: {b.get('drawdownPausePercent', 'NOT SET')}%")
    print(f"  Drawdown Pause Hours: {b.get('drawdownPauseHours', 'NOT SET')}")
    print(f"  Current Drawdown: {b.get('maxDrawdown', 0):.2f}%")
    print(f"  Daily P&L: ${b.get('dailyProfit', 0):.2f}")
    print(f"  Total P&L: ${b.get('totalProfit', 0):.2f}")
    print(f"  Status: {b.get('status')}")
    print(f"  Enabled: {b.get('enabled')}")
    
    # Check if protections are active
    max_daily = b.get('maxDailyLoss')
    if not max_daily or max_daily == 0:
        print(f"  ❌ NO DAILY LOSS LIMIT SET!")
    
    drawdown_pause = b.get('drawdownPausePercent')
    if not drawdown_pause or drawdown_pause == 0:
        print(f"  ❌ NO DRAWDOWN PAUSE SET!")
    
    if b.get('managementState') == 'recovery':
        print(f"  ⚠️  Bot in RECOVERY mode (hitting losses)")

print("\n" + "=" * 60)

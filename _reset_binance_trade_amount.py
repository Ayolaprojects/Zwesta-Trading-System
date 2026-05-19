"""
Reset bot trade amount adaptation so the bot uses the actual free Binance balance
instead of the inflated $95,951 figure that causes -2010 rejection errors.
"""
import sqlite3, json

db = r'C:\backend\zwesta_trading.db'
bot_id = 'bot_1778970971191'

conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row
c = conn.cursor()

row = c.execute('SELECT runtime_state FROM user_bots WHERE bot_id=?', (bot_id,)).fetchone()
state = json.loads(row['runtime_state'])

# Show before
print('BEFORE:')
print(f"  effectiveTradeAmount: {state.get('effectiveTradeAmount')}")
print(f"  riskPercent: {state.get('riskPercent')}")
print(f"  riskPerTrade: {state.get('riskPerTrade')}")
adapt = state.get('tradeAmountAdaptation', {})
print(f"  tradeAmountAdaptation.state: {adapt.get('state')}")
print(f"  tradeAmountAdaptation.multiplier: {adapt.get('multiplier')}")
print(f"  tradeAmountAdaptation.adjustedTradeAmount: {adapt.get('adjustedTradeAmount')}")
print(f"  effectivePositionSizeMultiplier: {state.get('effectivePositionSizeMultiplier')}")
print(f"  effectiveScannerCapitalMultiplier: {state.get('effectiveScannerCapitalMultiplier')}")

# Reset the hot-state multipliers back to baseline
# The demo account has ~$4,514 free USDT; use a conservative trade amount
if adapt:
    adapt['state'] = 'normal'
    adapt['multiplier'] = 1.0
    adapt['adjustedTradeAmount'] = adapt.get('baseTradeAmount', 3000.0)
    adapt['scannerCapitalMultiplier'] = 1.0
    adapt['retraceRatio'] = 0.0
    adapt['reason'] = 'reset to baseline — free balance capped'
    state['tradeAmountAdaptation'] = adapt

state['effectivePositionSizeMultiplier'] = 1.0
state['effectiveScannerCapitalMultiplier'] = 1.0

# Cap effectiveTradeAmount to something the demo account can fill
# Free USDT is ~$4,514; use 80% of that conservatively = ~$3,600
state['effectiveTradeAmount'] = 3500.0

# Also bring riskPerTrade in line — max 5% of free balance per trade
state['riskPerTrade'] = 230.0    # ~5% of $4,514
state['maxDailyLoss'] = 920.0    # ~4× riskPerTrade

c.execute('UPDATE user_bots SET runtime_state=? WHERE bot_id=?', (json.dumps(state), bot_id))
conn.commit()

print('\nAFTER:')
print(f"  effectiveTradeAmount: {state.get('effectiveTradeAmount')}")
print(f"  riskPerTrade: {state.get('riskPerTrade')}")
print(f"  maxDailyLoss: {state.get('maxDailyLoss')}")
print(f"  tradeAmountAdaptation.state: {state['tradeAmountAdaptation'].get('state')}")
print(f"  tradeAmountAdaptation.multiplier: {state['tradeAmountAdaptation'].get('multiplier')}")

conn.close()
print('\nDone.')

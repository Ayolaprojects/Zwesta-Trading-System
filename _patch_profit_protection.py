import sqlite3, json

DB_PATH = r'C:\backend\zwesta_trading.db'
BOT_ID = 'bot_1779112497256'

NEW_PP = {
    "enabled": True,
    "activationMinProfit": 2.0,
    "activationPercent": 3.0,
    "adaptiveByVolatility": True,
    "breakEvenActivationShare": 0.3,
    "breakEvenBufferProfit": 10.0,
    "breakEvenLockEnabled": False,        # don't freeze trading at break-even
    "closeLosingPositionsWithProfitablePeers": True,
    "loserRotationMinLoss": 0.0,
    "marginTakeProfitPercent": 30.0,
    "minLockedProfit": 10.0,              # never let saved profit fall below 10
    "minimumHoldMinutes": 1.0,
    "peakProfitHardLockShare": 0.0,       # no hard stop — bot keeps trading after close
    "portfolioActivationMinProfit": 3.0,
    "protectedSymbolCooldownMinutes": 5.0,
    "retraceClosePercent": 20.0,          # close open positions if profit drops 20% from peak
    "switchOnReversal": True,
    "zeroLossLockEnabled": False          # don't freeze trading at zero profit
}

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("SELECT strategy_id, parameters FROM bot_strategies WHERE bot_id = ?", (BOT_ID,))
row = cur.fetchone()
if not row:
    print("ERROR: bot not found in bot_strategies")
    conn.close()
    exit(1)

sid, params_raw = row
params = json.loads(params_raw) if params_raw else {}
old_pp = params.get('profitProtection', {})
print("OLD profitProtection:")
print(json.dumps(old_pp, indent=2))

params['profitProtection'] = NEW_PP
cur.execute("UPDATE bot_strategies SET parameters = ?, updated_at = datetime('now') WHERE strategy_id = ?",
            (json.dumps(params), sid))
conn.commit()
conn.close()

print("\nNEW profitProtection applied.")
print("Bot will now trade all day. Hard locks disabled. Cooldowns preserved.")

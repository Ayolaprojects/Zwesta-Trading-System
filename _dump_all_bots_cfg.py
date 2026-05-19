import sqlite3, json

db = sqlite3.connect('C:/backend/zwesta_trading.db')
rows = db.execute('SELECT bot_id, runtime_state, is_live FROM user_bots').fetchall()
for bot_id, rs, is_live in rows:
    if rs:
        cfg = json.loads(rs)
        broker = str(cfg.get('brokerType') or cfg.get('credentialType') or '')
        market = cfg.get('binanceMarket','')
        print(f'BOT_ID={bot_id} broker={broker} market={market} live={is_live}')
        keys = [
            'tradeAmount','effectiveTradeAmount','effectivePositionSizeMultiplier',
            'effectiveScannerCapitalMultiplier','signalThreshold','effectiveSignalThreshold',
            'managementState','managementProfile','binanceMarket','binanceFuturesBaseLeverage',
            'effectiveBinanceFuturesLeverage','binanceFuturesMarginType','accountBalance',
            'riskPerTrade','maxDailyLoss','maxOpenPositions','dailyProfit','totalProfit',
            'totalTrades','drawdownPauseUntil','selectedPreset','scannerCapitalLiveMaxBoost',
            'symbols','lastSizingAdjustment','tradeAmountAdaptation'
        ]
        print(json.dumps({k: cfg.get(k) for k in keys}, indent=2))
        print()
db.close()

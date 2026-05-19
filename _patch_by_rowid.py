"""
Patch user_bots by rowid, bypassing bulk table corruption.
"""
import sqlite3, json

src = r'C:\backend\zwesta_trading.db'
conn = sqlite3.connect(src)
conn.execute('PRAGMA journal_mode=WAL')

targets = {
    'bot_1778970971191': {
        'rowid': 2,
        'effectiveTradeAmount': 3500.0,
        'riskPerTrade': 230.0,
        'maxDailyLoss': 920.0,
        'effectivePositionSizeMultiplier': 1.0,
        'effectiveScannerCapitalMultiplier': 1.0,
    },
}

for bot_id, patches in targets.items():
    rowid = patches.pop('rowid')
    try:
        row = conn.execute('SELECT runtime_state FROM user_bots WHERE rowid=?', (rowid,)).fetchone()
        if not row:
            print(f'{bot_id}: not found at rowid {rowid}')
            continue
        state = json.loads(row[0] or '{}')

        # Apply patches
        for k, v in patches.items():
            state[k] = v

        # Reset tradeAmountAdaptation
        if isinstance(state.get('tradeAmountAdaptation'), dict):
            adapt = state['tradeAmountAdaptation']
            adapt['state'] = 'normal'
            adapt['multiplier'] = 1.0
            adapt['adjustedTradeAmount'] = 3500.0
            adapt['scannerCapitalMultiplier'] = 1.0
            adapt['retraceRatio'] = 0.0
            state['tradeAmountAdaptation'] = adapt

        conn.execute('UPDATE user_bots SET runtime_state=? WHERE rowid=?', (json.dumps(state), rowid))
        conn.commit()
        print(f'{bot_id}: PATCHED at rowid {rowid}')
        print(f'  effectiveTradeAmount = {state.get("effectiveTradeAmount")}')
        print(f'  riskPerTrade = {state.get("riskPerTrade")}')
        print(f'  effectivePositionSizeMultiplier = {state.get("effectivePositionSizeMultiplier")}')
        print(f'  effectiveScannerCapitalMultiplier = {state.get("effectiveScannerCapitalMultiplier")}')
    except Exception as e:
        print(f'{bot_id}: ERROR {e}')

conn.close()

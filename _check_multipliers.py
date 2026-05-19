import sqlite3, json

db = sqlite3.connect('C:/backend/zwesta_trading.db')
rows = db.execute("SELECT bot_id, runtime_state FROM user_bots WHERE runtime_state IS NOT NULL").fetchall()
for bot_id, cfg_raw in rows:
    try:
        cfg = json.loads(cfg_raw)
        psm  = cfg.get('effectivePositionSizeMultiplier', 'N/A')
        scm  = cfg.get('effectiveScannerCapitalMultiplier', 'N/A')
        eta  = cfg.get('effectiveTradeAmount', 'N/A')
        ta   = cfg.get('tradeAmount', 'N/A')
        mode = cfg.get('mode', '')
        broker = cfg.get('brokerType', '')
        sizing   = cfg.get('lastSizingAdjustment') or {}
        sz_st    = sizing.get('state', '')
        sz_mult  = sizing.get('multiplier', 'N/A')
        sz_reason = (sizing.get('reason') or '')[:60]
        taa = cfg.get('tradeAmountAdaptation') or {}
        taa_mult = taa.get('multiplier', 'N/A')
        taa_reason = (taa.get('reason') or '')[:60]
        print(f"{bot_id[:22]} | {broker:10} | {mode:5} | PSM={psm} SCM={scm} ETA={eta} TA={ta}")
        print(f"  lastSizingAdjustment : mult={sz_mult} state={sz_st} | {sz_reason}")
        print(f"  tradeAmountAdaptation: mult={taa_mult} | {taa_reason}")
        print()
    except Exception as e:
        print(f"Error {bot_id}: {e}")
db.close()

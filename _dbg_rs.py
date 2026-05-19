import sqlite3, json
c=sqlite3.connect(r'C:\backend\zwesta_trading.db')
c.row_factory=sqlite3.Row
for bid in ('bot_1778004514350','bot_1777949277150'):
    r=c.execute('SELECT bot_id, total_profit, daily_profit, runtime_state FROM user_bots WHERE bot_id=?',(bid,)).fetchone()
    rs=json.loads(r['runtime_state'] or '{}')
    print('===',bid)
    print('  total_profit_col:', r['total_profit'])
    print('  daily_profit_col:', r['daily_profit'])
    print('  rs.totalProfit:', rs.get('totalProfit'))
    print('  rs.peakProfit:', rs.get('peakProfit'))
    print('  rs.maxDrawdown:', rs.get('maxDrawdown'))
    print('  rs.dailyProfits:', rs.get('dailyProfits'))
    print('  rs.tradeHistory_len:', len(rs.get('tradeHistory') or []))
    print('  rs.profitHistory_len:', len(rs.get('profitHistory') or []))
    print('  rs.open_positions keys:', list((rs.get('open_positions') or {}).keys()))
    op = rs.get('open_positions') or {}
    for k,v in op.items():
        print('    pos', k, 'profit=',v.get('profit'),'volume=',v.get('volume'),'symbol=',v.get('symbol'),'type=',v.get('type'))
    print('  rs.accountEquityHighWatermark:', rs.get('accountEquityHighWatermark'))
    print('  rs.drawdownPauseUntil:', rs.get('drawdownPauseUntil'))
    print('  rs.signalThreshold:', rs.get('signalThreshold'))
print('--- trades table counts ---')
for bid in ('bot_1778004514350','bot_1777949277150'):
    cnt=c.execute('SELECT COUNT(*), SUM(profit) FROM trades WHERE bot_id=?',(bid,)).fetchone()
    print(bid, 'trades_rows=',cnt[0],'sum_profit=',cnt[1])

import os, json
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

import sys

if len(sys.argv) > 1:
    BOT_IDS = sys.argv[1:]
else:
    BOT_IDS = ['bot_1786359308343', 'bot_1785510766379']

def main():
    try:
        import psycopg2
    except Exception as e:
        print('PSYCOPG2_IMPORT_ERROR', e)
        return
    url = os.getenv('DATABASE_URL')
    if not url:
        print('NO_DATABASE_URL')
        return
    try:
        conn = psycopg2.connect(url)
        cur = conn.cursor()
        cur.execute("SELECT bot_id, name, enabled, is_live, runtime_state FROM user_bots WHERE bot_id = ANY(%s)", (BOT_IDS,))
        rows = cur.fetchall()
        out = []
        for r in rows:
            bot_id = r[0]
            name = r[1] or ''
            flag = 'LIVE' if r[3] else 'DEMO'
            en = 'ENABLED' if r[2] else 'DISABLED'
            rs = r[4]
            try:
                js = json.loads(rs) if rs else {}
            except Exception:
                js = {'_raw': str(rs)}
            snippet = {k: js.get(k) for k in ['brokerName','mode','open_positions','totalProfit','balanceTrend','consecutiveLosses','lossStreakPauseUntil','manualTradingHoursEnabled','signalThreshold','intelligentScanner','cumulativeProfit','consecutiveLosses','profitProtection']}
            out.append({'bot_id':bot_id,'name':name,'live':flag,'enabled':en,'snippet':snippet})
        print(json.dumps(out, indent=2))
    except Exception as e:
        print('QUERY_ERROR', e)
    finally:
        try:
            conn.close()
        except Exception:
            pass

if __name__ == '__main__':
    main()

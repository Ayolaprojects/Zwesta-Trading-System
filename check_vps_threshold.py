import sqlite3
import json

conn = sqlite3.connect('C:\\backend\\zwesta_trading.db')
c = conn.cursor()
c.execute("SELECT name, runtime_state FROM user_bots WHERE name LIKE '%demo%'")
row = c.fetchone()
conn.close()

if row:
    rs = json.loads(row[1])
    print('Signal Threshold:', rs.get('signalThreshold', 'N/A'))
    print('Effective Signal Threshold:', rs.get('effectiveSignalThreshold', 'N/A'))
else:
    print('No demo bot found')
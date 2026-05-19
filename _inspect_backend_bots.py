import sqlite3, json
conn = sqlite3.connect(r'C:\backend\zwesta_trading.db')
cursor = conn.cursor()
cursor.execute('SELECT bot_id, name, enabled, status, runtime_state FROM user_bots')
for bot_id, name, enabled, status, rs in cursor.fetchall():
    state = json.loads(rs) if rs else {}
    print(f"{bot_id} {name} (enabled={enabled}, status={status}):")
    print(f"  signalThreshold={state.get('signalThreshold')}")
    print(f"  effectiveSignalThreshold={state.get('effectiveSignalThreshold')}")
    print(f"  adaptiveSignalThresholdOffset={state.get('adaptiveSignalThresholdOffset')}")
    print(f"  brokerName={state.get('brokerName')}")
    print(f"  strategy={state.get('strategy')}")
    print(f"  managementMode={state.get('managementMode')}")
    print(f"  managementProfile={state.get('managementProfile')}")
    print(f"  signalThresholdMode={state.get('signalThresholdMode')}")
    print(f"  symbols={state.get('symbols')}")
conn.close()

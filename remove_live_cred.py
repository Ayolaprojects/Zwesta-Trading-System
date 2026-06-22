import psycopg2
conn = psycopg2.connect('postgresql://zwesta_admin:Zwesta%40Trading2026!@localhost:5432/zwesta_trading')
cur = conn.cursor()
# Remove the live credential that's causing the MT5 terminal to switch
cur.execute("DELETE FROM broker_credentials WHERE credential_id='fd34606e-2077-421d-afaa-c7af0b4abd98'")
conn.commit()
print('Removed live credential')
conn.close()
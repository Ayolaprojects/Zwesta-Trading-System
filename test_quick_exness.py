import requests, json
import psycopg2

# Get the user_id for the credential
conn = psycopg2.connect('postgresql://zwesta_admin:Zwesta%40Trading2026!@localhost:5432/zwesta_trading')
cur = conn.cursor()
cur.execute("SELECT user_id FROM broker_credentials WHERE credential_id='66838627-f045-489d-85d6-a81e829d4228'")
row = cur.fetchone()
user_id = row[0] if row else ''
conn.close()
print('User ID:', user_id)

# Test quick-create-exness with the correct user_id
r = requests.post('http://localhost:9000/api/bot/quick-create-exness',
    headers={'Content-Type': 'application/json'},
    json={'credentialId': '66838627-f045-489d-85d6-a81e829d4228', 'preset': 'edge_pairs'},
    timeout=30)
print('Quick-create Exness:', r.status_code)
print(r.text)
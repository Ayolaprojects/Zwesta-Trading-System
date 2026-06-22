import requests, json
import psycopg2
import uuid

# Register a new user
r = requests.post('http://localhost:9000/api/user/register',
    headers={'Content-Type': 'application/json'},
    json={'username': 'testuser5', 'email': 'testuser5@test.com', 'password': 'test123456', 'name': 'Test User 5'}, timeout=10)
print('Register:', r.status_code)
data = r.json()
token = data.get('session_token', '')
user_id = data.get('user_id', '')
print('Token:', token[:30] + '...')
print('User ID:', user_id)

# Update credential ownership
conn = psycopg2.connect('postgresql://zwesta_admin:Zwesta%40Trading2026!@localhost:5432/zwesta_trading')
cur = conn.cursor()
cur.execute("UPDATE broker_credentials SET user_id=%s WHERE credential_id='66838627-f045-489d-85d6-a81e829d4228'", (user_id,))
conn.commit()
print('Updated credential ownership')
conn.close()

# Test quick-create-exness
r = requests.post('http://localhost:9000/api/bot/quick-create-exness',
    headers={'Content-Type': 'application/json', 'X-Session-Token': token},
    json={'credentialId': '66838627-f045-489d-85d6-a81e829d4228', 'preset': 'edge_pairs'},
    timeout=30)
print('Quick-create Exness:', r.status_code)
print(r.text)
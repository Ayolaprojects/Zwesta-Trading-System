import psycopg2
import uuid

new_user_id = str(uuid.uuid4())
print(f"New user ID: {new_user_id}")

conn = psycopg2.connect('postgresql://zwesta_admin:Zwesta%40Trading2026!@localhost:5432/zwesta_trading')
cur = conn.cursor()
cur.execute("UPDATE broker_credentials SET user_id=%s WHERE credential_id='66838627-f045-489d-85d6-a81e829d4228'", (new_user_id,))
conn.commit()
print('Updated credential ownership')
conn.close()
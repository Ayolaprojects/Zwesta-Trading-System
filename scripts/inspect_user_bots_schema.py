import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(r'c:\zwesta-trader\Zwesta Flutter App\vps_app_package\.env', override=True)
from runtime_infrastructure import get_database_url

import psycopg2

url = get_database_url()
if not url:
    print('No DATABASE_URL configured')
    sys.exit(1)

conn = psycopg2.connect(url)
cur = conn.cursor()
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='user_bots'")
for row in cur.fetchall():
    print(row)
cur.close()
conn.close()

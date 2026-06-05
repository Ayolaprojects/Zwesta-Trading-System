import psycopg2

try:
    conn = psycopg2.connect(
        "postgresql://zwesta_admin:Zwesta@Trading2026!@localhost:5432/zwesta_trading"
    )
    cur = conn.cursor()
    
    # Get users
    cur.execute("SELECT id, email, name FROM users LIMIT 10;")
    users = cur.fetchall()
    
    print("Available users:")
    for user_id, email, name in users:
        print(f"  {email} - {name}")
    
    # Get bots
    print("\nAvailable bots:")
    cur.execute("SELECT id, name, broker, status FROM bots LIMIT 10;")
    bots = cur.fetchall()
    for bot_id, name, broker, status in bots:
        print(f"  {name} ({broker}) - {status}")
    
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

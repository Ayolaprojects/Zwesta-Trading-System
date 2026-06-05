#!/usr/bin/env python3
"""
Check actual database users.
"""
import psycopg2.extras

try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="zwesta_trading",
        user="zwesta_admin",
        password="Zwesta@Trading2026!",
    )
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    # Get users
    cur.execute("SELECT id, email, name FROM users LIMIT 10;")
    users = cur.fetchall()
    
    print("Available users in database:")
    for user in users:
        print(f"  ID: {user['id']}, Email: {user['email']}, Name: {user['name']}")
    
    # Get bots
    print("\nAvailable bots:")
    cur.execute("SELECT id, name, broker, status FROM bots LIMIT 10;")
    bots = cur.fetchall()
    for bot in bots:
        print(f"  {bot['name']} ({bot['broker']}) - {bot['status']}")
    
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

"""
Quick check of actual PostgreSQL table names and bot configurations
"""

import os
import sys
sys.path.insert(0, r'C:\backend')

from runtime_infrastructure import get_sqlalchemy_engine
from sqlalchemy import text, inspect

def main():
    print("\n" + "═" * 80)
    print("  POSTGRESQL TABLE INSPECTION")
    print("═" * 80)
    
    try:
        engine = get_sqlalchemy_engine()
        conn = engine.connect()
        inspector = inspect(engine)
        
        # List all tables
        tables = inspector.get_table_names()
        print(f"\n📊 Total Tables: {len(tables)}")
        print("\nTables:")
        for table in sorted(tables):
            print(f"  - {table}")
        
        # Check for bot-related tables
        print("\n" + "═" * 80)
        print("  BOT CONFIGURATION TABLES")
        print("═" * 80)
        
        bot_tables = [t for t in tables if 'bot' in t.lower()]
        print(f"\nBot-related tables: {len(bot_tables)}")
        for table in bot_tables:
            print(f"\n📋 Table: {table}")
            
            # Get row count
            try:
                query = text(f"SELECT COUNT(*) FROM {table}")
                result = conn.execute(query)
                count = result.fetchone()[0]
                print(f"   Rows: {count}")
                
                # Show first few rows if it's a config table
                if count > 0:
                    query = text(f"SELECT * FROM {table} LIMIT 5")
                    result = conn.execute(query)
                    rows = result.fetchall()
                    cols = result.keys()
                    
                    print(f"   Columns: {', '.join(cols)}")
                    print()
                    for row in rows:
                        print(f"   Row: {dict(zip(cols, row))}")
                        
            except Exception as e:
                print(f"   ⚠️  Error querying table: {e}")
        
        # Check sessions table
        if 'sessions' in tables:
            print("\n" + "═" * 80)
            print("  RECENT BOT ACTIVITY (sessions table)")
            print("═" * 80)
            
            query = text("""
                SELECT bot_id, COUNT(*) as count, MAX(timestamp) as last_run
                FROM sessions
                GROUP BY bot_id
                ORDER BY bot_id
            """)
            result = conn.execute(query)
            sessions = result.fetchall()
            
            print(f"\nBot Activity Summary:")
            for s in sessions:
                print(f"  Bot {s[0]}: {s[1]} sessions | Last: {s[2]}")
        
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

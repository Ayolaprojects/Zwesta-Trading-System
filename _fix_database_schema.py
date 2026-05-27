"""
Fix Database Schema - Add missing closed_at column
"""
import sqlite3
import sys

DB_PATH = r"C:\backend\zwesta_trading.db"

def fix_database():
    print(f"Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check current schema
    cursor.execute("PRAGMA table_info(trades)")
    columns = cursor.fetchall()
    
    print("\n✓ Current trades table columns:")
    column_names = [col[1] for col in columns]
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
    
    # Check if closed_at exists
    if 'closed_at' in column_names:
        print("\n✓ Column 'closed_at' already exists!")
    else:
        print("\n⚠️  Column 'closed_at' is MISSING - adding it now...")
        try:
            cursor.execute("ALTER TABLE trades ADD COLUMN closed_at TEXT")
            conn.commit()
            print("✓ Successfully added 'closed_at' column!")
            
            # Update existing closed trades with created_at as closed_at
            cursor.execute("""
                UPDATE trades 
                SET closed_at = created_at 
                WHERE status = 'closed' AND closed_at IS NULL
            """)
            conn.commit()
            print(f"✓ Updated {cursor.rowcount} existing closed trades")
            
        except Exception as e:
            print(f"✗ Error adding column: {e}")
            conn.rollback()
            sys.exit(1)
    
    # Verify fix
    cursor.execute("PRAGMA table_info(trades)")
    columns_after = cursor.fetchall()
    column_names_after = [col[1] for col in columns_after]
    
    print("\n✓ Final schema verification:")
    for col in columns_after:
        if col[1] == 'closed_at':
            print(f"  ✓ {col[1]} ({col[2]}) - PRESENT")
            break
    else:
        print("  ✗ closed_at - STILL MISSING!")
        sys.exit(1)
    
    # Test query that was failing
    print("\n✓ Testing profit calculation query...")
    cursor.execute("""
        SELECT COUNT(*) as total_trades,
               SUM(CASE WHEN closed_at IS NOT NULL THEN 1 ELSE 0 END) as closed_trades
        FROM trades
    """)
    result = cursor.fetchone()
    print(f"  Total trades: {result[0]}")
    print(f"  Trades with closed_at: {result[1]}")
    
    conn.close()
    print("\n✅ DATABASE FIXED! Ready to copy to VPS.")
    print(f"\nCopy command:")
    print(f'  Copy-Item "{DB_PATH}" -Destination "\\\\38.247.146.198\\C$\\backend\\zwesta_trading.db" -Force')
    print("\nOR manually via RDP:")
    print(f'  1. Copy: {DB_PATH}')
    print(f'  2. Paste to VPS: C:\\backend\\zwesta_trading.db')
    print(f'  3. Restart backend')

if __name__ == "__main__":
    try:
        fix_database()
    except Exception as e:
        print(f"\n✗ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

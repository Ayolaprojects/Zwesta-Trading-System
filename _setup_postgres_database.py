#!/usr/bin/env python3
"""
PostgreSQL Database Setup for Zwesta Trading System
Creates database, user, and permissions
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys

# Default PostgreSQL superuser connection
SUPERUSER_CONFIG = {
    'host': 'localhost',
    'database': 'postgres',  # Connect to default database
    'user': 'postgres',
    'port': 5432
}

# New database configuration
DB_NAME = 'zwesta_trading'
DB_USER = 'zwesta_admin'
DB_PASSWORD = 'Zwesta@Trading2026!'  # Strong password

def setup_database():
    """Create database, user, and grant permissions"""
    print("╔════════════════════════════════════════════════════════════╗")
    print("║   PostgreSQL Database Setup - Zwesta Trading System       ║")
    print("╚════════════════════════════════════════════════════════════╝\n")
    
    try:
        # Get superuser password
        print("🔑 Enter PostgreSQL superuser (postgres) password:")
        print("   (If you just installed, it might be empty - press Enter)")
        superuser_password = input("   Password: ").strip()
        
        if superuser_password:
            SUPERUSER_CONFIG['password'] = superuser_password
        
        # Connect as superuser
        print(f"\n🐘 Connecting to PostgreSQL as superuser...")
        conn = psycopg2.connect(**SUPERUSER_CONFIG)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        print("   ✅ Connected successfully")
        
        # Check if database exists
        print(f"\n🔍 Checking if database '{DB_NAME}' exists...")
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
        db_exists = cursor.fetchone() is not None
        
        if db_exists:
            print(f"   ⚠️  Database '{DB_NAME}' already exists")
            response = input("   Drop and recreate? (yes/no): ").strip().lower()
            if response == 'yes':
                print(f"   🗑️  Dropping database '{DB_NAME}'...")
                cursor.execute(f"DROP DATABASE {DB_NAME}")
                print("   ✅ Database dropped")
                db_exists = False
        
        if not db_exists:
            print(f"\n📦 Creating database '{DB_NAME}'...")
            cursor.execute(f"CREATE DATABASE {DB_NAME}")
            print("   ✅ Database created")
        
        # Check if user exists
        print(f"\n👤 Checking if user '{DB_USER}' exists...")
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (DB_USER,))
        user_exists = cursor.fetchone() is not None
        
        if user_exists:
            print(f"   ⚠️  User '{DB_USER}' already exists")
            print(f"   🔄 Updating password...")
            cursor.execute(f"ALTER USER {DB_USER} WITH PASSWORD %s", (DB_PASSWORD,))
            print("   ✅ Password updated")
        else:
            print(f"\n🔐 Creating user '{DB_USER}'...")
            cursor.execute(f"CREATE USER {DB_USER} WITH PASSWORD %s", (DB_PASSWORD,))
            print("   ✅ User created")
        
        # Grant privileges
        print(f"\n🔓 Granting privileges on database '{DB_NAME}' to '{DB_USER}'...")
        cursor.execute(f"GRANT ALL PRIVILEGES ON DATABASE {DB_NAME} TO {DB_USER}")
        print("   ✅ Privileges granted")
        
        # Connect to new database to grant schema privileges
        cursor.close()
        conn.close()
        
        print(f"\n🔗 Connecting to '{DB_NAME}' database...")
        db_config = SUPERUSER_CONFIG.copy()
        db_config['database'] = DB_NAME
        conn = psycopg2.connect(**db_config)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print(f"\n🔓 Granting schema privileges...")
        cursor.execute(f"GRANT ALL ON SCHEMA public TO {DB_USER}")
        cursor.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO {DB_USER}")
        cursor.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO {DB_USER}")
        print("   ✅ Schema privileges granted")
        
        cursor.close()
        conn.close()
        
        # Test connection as new user
        print(f"\n🧪 Testing connection as '{DB_USER}'...")
        test_config = {
            'host': 'localhost',
            'database': DB_NAME,
            'user': DB_USER,
            'password': DB_PASSWORD,
            'port': 5432
        }
        test_conn = psycopg2.connect(**test_config)
        test_cursor = test_conn.cursor()
        test_cursor.execute("SELECT version()")
        version = test_cursor.fetchone()[0]
        print(f"   ✅ Connection successful!")
        print(f"   PostgreSQL version: {version.split(',')[0]}")
        test_cursor.close()
        test_conn.close()
        
        print("\n╔════════════════════════════════════════════════════════════╗")
        print("║                    ✅ SETUP COMPLETE                       ║")
        print("╚════════════════════════════════════════════════════════════╝")
        print("\n📋 Database Configuration:")
        print(f"   Host: localhost")
        print(f"   Port: 5432")
        print(f"   Database: {DB_NAME}")
        print(f"   User: {DB_USER}")
        print(f"   Password: {DB_PASSWORD}")
        print("\n🔐 IMPORTANT: Save this password securely!")
        print("\n📝 Connection String:")
        print(f"   postgresql://{DB_USER}:{DB_PASSWORD}@localhost:5432/{DB_NAME}")
        print("\n🚀 Next Steps:")
        print("   1. Run: python _migrate_to_postgresql.py")
        print("   2. Update backend DATABASE_URL environment variable")
        print("   3. Restart backend service")
        
        return True
        
    except psycopg2.Error as e:
        print(f"\n❌ PostgreSQL Error: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Ensure PostgreSQL service is running")
        print("   2. Check if you have superuser access")
        print("   3. Verify PostgreSQL port 5432 is not blocked")
        return False
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user")
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

if __name__ == '__main__':
    success = setup_database()
    sys.exit(0 if success else 1)

"""
Test PostgreSQL Connection from Backend
"""
import os
import sys

# Add backend to path
sys.path.insert(0, r'C:\backend')

from runtime_infrastructure import (
    using_postgres, 
    get_database_backend,
    get_database_url,
    get_runtime_infrastructure_summary
)

print("╔══════════════════════════════════════════════════════════════╗")
print("║   PostgreSQL Connection Test                                 ║")
print("╚══════════════════════════════════════════════════════════════╝\n")

# Check configuration
print("📋 Configuration:")
print(f"   Backend: {get_database_backend()}")
print(f"   Using Postgres: {using_postgres()}")
print(f"   Database URL: {get_database_url()[:50]}...")

# Get full summary
print("\n🔍 Full Infrastructure Summary:")
summary = get_runtime_infrastructure_summary()
for key, value in summary.items():
    print(f"   {key}: {value}")

# Test SQLAlchemy connection
if using_postgres():
    print("\n🐘 Testing PostgreSQL Connection...")
    try:
        from runtime_infrastructure import get_sqlalchemy_engine
        engine = get_sqlalchemy_engine()
        
        if engine:
            print("   ✅ SQLAlchemy engine created")
            
            # Test actual connection
            with engine.connect() as conn:
                # Simple version check
                from sqlalchemy import text
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                print(f"   ✅ PostgreSQL connection successful!")
                print(f"   📦 PostgreSQL version: {version.split(',')[0]}")
                
                # Test queries
                result = conn.execute(text("SELECT COUNT(*) as count FROM users"))
                user_count = result.fetchone()[0]
                print(f"   📊 Users in database: {user_count}")
                
                result = conn.execute(text("SELECT COUNT(*) as count FROM user_bots"))
                bot_count = result.fetchone()[0]
                print(f"   📊 Bots in database: {bot_count}")
                
                result = conn.execute(text("SELECT COUNT(*) as count FROM broker_credentials"))
                cred_count = result.fetchone()[0]
                print(f"   📊 Credentials in database: {cred_count}")
        else:
            print("   ❌ Failed to create SQLAlchemy engine")
            
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
else:
    print("\n⚠️  PostgreSQL mode not enabled!")
    print("   Check DATABASE_BACKEND or DATABASE_URL in .env")

print("\n" + "="*70)
print("✅ Test Complete")
print("="*70)

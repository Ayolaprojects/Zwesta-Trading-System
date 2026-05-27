"""
SQLite to PostgreSQL Migration Script
Migrates zwesta_trading.db to PostgreSQL for enterprise scale (1,000-5,000 users)
"""

import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import os
import json
from datetime import datetime

# Configuration
SQLITE_DB_PATH = r'C:\backend\zwesta_trading.db'
POSTGRES_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'database': os.getenv('POSTGRES_DB', 'zwesta_trading'),
    'user': os.getenv('POSTGRES_USER', 'zwesta_admin'),
    'password': os.getenv('POSTGRES_PASSWORD', 'Zwesta@Trading2026!'),
    'port': int(os.getenv('POSTGRES_PORT', '5432'))
}

def create_postgres_schema(pg_conn):
    """Create PostgreSQL tables with optimizations for scale"""
    cursor = pg_conn.cursor()
    
    print("📋 Creating PostgreSQL schema...")
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id UUID PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255),
            name VARCHAR(255),
            referral_code VARCHAR(20) UNIQUE,
            referrer_id UUID,
            total_commission DECIMAL(15, 2) DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_referral_code ON users(referral_code);')
    
    # Broker credentials
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS broker_credentials (
            credential_id TEXT PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            broker_name VARCHAR(50) NOT NULL,
            account_number VARCHAR(100),
            password TEXT,
            server VARCHAR(100),
            mt5_terminal_path TEXT,
            is_live BOOLEAN DEFAULT FALSE,
            binance_api_key TEXT,
            binance_api_secret TEXT,
            binance_subaccount_email VARCHAR(255),
            binance_subaccount_id TEXT,
            commission_collection_method VARCHAR(50),
            created_at TIMESTAMP DEFAULT NOW()
        );
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_broker_creds_user_id ON broker_credentials(user_id);')
    
    # User bots (partitioned by broker for performance)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_bots (
            bot_id VARCHAR(100) PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            broker_type VARCHAR(50) NOT NULL,
            broker_account_id TEXT,
            strategy VARCHAR(100),
            status VARCHAR(50) DEFAULT 'STOPPED',
            enabled BOOLEAN DEFAULT TRUE,
            is_live BOOLEAN DEFAULT FALSE,
            total_profit DECIMAL(15, 2) DEFAULT 0,
            daily_profit DECIMAL(15, 2) DEFAULT 0,
            total_trades INTEGER DEFAULT 0,
            winning_trades INTEGER DEFAULT 0,
            runtime_state JSONB,
            commission_collected BOOLEAN DEFAULT FALSE,
            commission_collected_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_bots_user_id ON user_bots(user_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_bots_broker_type ON user_bots(broker_type);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_bots_status ON user_bots(status);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_bots_enabled ON user_bots(enabled);')
    
    # Trades table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            trade_id TEXT PRIMARY KEY,
            bot_id VARCHAR(100) REFERENCES user_bots(bot_id) ON DELETE CASCADE,
            user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
            symbol VARCHAR(50),
            action VARCHAR(20),
            volume DECIMAL(15, 8),
            open_price DECIMAL(20, 8),
            close_price DECIMAL(20, 8),
            profit DECIMAL(15, 2),
            opened_at TIMESTAMP,
            closed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW()
        );
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_bot_id ON trades(bot_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_user_id ON trades(user_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_created_at ON trades(created_at);')
    
    # Commission config
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS commission_config (
            config_id TEXT PRIMARY KEY,
            developer_direct_rate DECIMAL(5, 4) DEFAULT 0.25,
            developer_referral_rate DECIMAL(5, 4) DEFAULT 0.25,
            recruiter_rate DECIMAL(5, 4) DEFAULT 0.05,
            tier2_rate DECIMAL(5, 4) DEFAULT 0.02,
            developer_id UUID,
            multi_tier_enabled BOOLEAN DEFAULT TRUE,
            updated_at TIMESTAMP DEFAULT NOW(),
            updated_by TEXT
        );
    ''')
    
    # Commission transactions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS commission_transactions (
            transaction_id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(user_id),
            amount DECIMAL(15, 2) NOT NULL,
            currency VARCHAR(10) DEFAULT 'USDT',
            method VARCHAR(50),
            binance_txn_id TEXT,
            binance_withdraw_id TEXT,
            payment_proof TEXT,
            status VARCHAR(50) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT NOW(),
            completed_at TIMESTAMP
        );
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_commission_user_id ON commission_transactions(user_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_commission_status ON commission_transactions(status);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_commission_created_at ON commission_transactions(created_at);')
    
    # Withdrawal requests
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS withdrawal_requests (
            withdrawal_id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(user_id),
            amount_requested DECIMAL(15, 2) NOT NULL,
            commission_due DECIMAL(15, 2) NOT NULL,
            net_amount DECIMAL(15, 2) NOT NULL,
            currency VARCHAR(10) DEFAULT 'USDT',
            withdrawal_address TEXT,
            status VARCHAR(50) DEFAULT 'pending_commission_payment',
            payment_proof TEXT,
            approved_by TEXT,
            approved_at TIMESTAMP,
            admin_notes TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_withdrawal_user_id ON withdrawal_requests(user_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_withdrawal_status ON withdrawal_requests(status);')
    
    # Referrals
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS referrals (
            referral_id UUID PRIMARY KEY,
            referrer_id UUID REFERENCES users(user_id),
            referred_user_id UUID REFERENCES users(user_id),
            created_at TIMESTAMP DEFAULT NOW()
        );
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id);')
    
    pg_conn.commit()
    print("✅ PostgreSQL schema created successfully")

def migrate_table(sqlite_conn, pg_conn, table_name, column_mapping=None):
    """Migrate a single table from SQLite to PostgreSQL"""
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    print(f"\n📦 Migrating table: {table_name}")
    
    # Get all data from SQLite
    sqlite_cursor.execute(f'SELECT * FROM {table_name}')
    rows = sqlite_cursor.fetchall()
    
    if not rows:
        print(f"   ⚠️  No data in {table_name}")
        return
    
    # Get column names
    columns = [desc[0] for desc in sqlite_cursor.description]
    
    # Apply column mapping if provided
    if column_mapping:
        columns = [column_mapping.get(col, col) for col in columns]
    
    # Build INSERT query
    columns_str = ', '.join(columns)
    placeholders = ', '.join(['%s'] * len(columns))
    
    # Convert rows to list of tuples
    data = []
    for row in rows:
        row_data = list(row)
        
        # Convert JSON strings to JSONB for runtime_state
        if 'runtime_state' in columns:
            idx = columns.index('runtime_state')
            if row_data[idx]:
                try:
                    # Already valid JSON
                    if isinstance(row_data[idx], str):
                        json.loads(row_data[idx])  # Validate
                except:
                    row_data[idx] = '{}'  # Default to empty JSON
        
        data.append(tuple(row_data))
    
    # Bulk insert using execute_values (proper syntax)
    try:
        query_template = f'INSERT INTO {table_name} ({columns_str}) VALUES %s ON CONFLICT DO NOTHING'
        execute_values(pg_cursor, query_template, data, template=None, page_size=100)
        pg_conn.commit()
        print(f"   ✅ Migrated {len(data)} rows")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        pg_conn.rollback()

def migrate_all_data():
    """Main migration function"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║   SQLite → PostgreSQL Migration                          ║
║   Enterprise Scale Database Setup                        ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Check if SQLite database exists
    if not os.path.exists(SQLITE_DB_PATH):
        print(f"❌ SQLite database not found: {SQLITE_DB_PATH}")
        return False
    
    try:
        # Connect to SQLite
        print(f"\n📂 Connecting to SQLite: {SQLITE_DB_PATH}")
        sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
        sqlite_conn.row_factory = sqlite3.Row
        print("   ✅ SQLite connected")
        
        # Connect to PostgreSQL
        print(f"\n🐘 Connecting to PostgreSQL: {POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}")
        pg_conn = psycopg2.connect(**POSTGRES_CONFIG)
        print("   ✅ PostgreSQL connected")
        
        # Create schema
        create_postgres_schema(pg_conn)
        
        # Migrate tables in order (respecting foreign keys)
        tables = [
            'users',
            'referrals',
            'broker_credentials',
            'user_bots',
            'trades',
            'commission_config',
            'commission_transactions',
            'withdrawal_requests'
        ]
        
        print("\n" + "="*60)
        print("Starting data migration...")
        print("="*60)
        
        for table in tables:
            try:
                migrate_table(sqlite_conn, pg_conn, table)
            except Exception as e:
                print(f"   ⚠️  Skipping {table}: {e}")
        
        # Close connections
        sqlite_conn.close()
        pg_conn.close()
        
        print("\n" + "="*60)
        print("✅ Migration completed successfully!")
        print("="*60)
        
        print("""
Next steps:
1. Update backend to use PostgreSQL connection
2. Test all API endpoints
3. Monitor performance
4. Backup SQLite database (keep as fallback)
        """)
        
        return True
    
    except psycopg2.OperationalError as e:
        print(f"\n❌ PostgreSQL connection failed: {e}")
        print("""
Common fixes:
1. Ensure PostgreSQL is running: systemctl status postgresql
2. Check credentials in environment variables
3. Verify firewall allows port 5432
4. Test connection: psql -h localhost -U zwesta_admin -d zwesta_trading
        """)
        return False
    
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_migration():
    """Verify migration was successful"""
    print("\n🔍 Verifying migration...")
    
    try:
        pg_conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = pg_conn.cursor()
        
        tables = ['users', 'user_bots', 'trades', 'broker_credentials']
        
        for table in tables:
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            count = cursor.fetchone()[0]
            print(f"   {table}: {count} rows")
        
        pg_conn.close()
        print("✅ Verification complete")
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")

if __name__ == '__main__':
    print("\n⚠️  WARNING: This will migrate your database to PostgreSQL")
    print("Make sure you have:")
    print("1. PostgreSQL installed and running")
    print("2. Created database: zwesta_trading")
    print("3. Created user: zwesta_admin")
    print("4. Set environment variables (POSTGRES_HOST, POSTGRES_PASSWORD, etc.)")
    
    confirm = input("\nContinue with migration? (yes/no): ")
    
    if confirm.lower() == 'yes':
        success = migrate_all_data()
        
        if success:
            verify_migration()
            
            print("""
╔═══════════════════════════════════════════════════════════╗
║   🎉 Migration Complete!                                 ║
║                                                           ║
║   Your database is now ready for 1,000-5,000 users       ║
║                                                           ║
║   Next: Update backend connection string                 ║
╚═══════════════════════════════════════════════════════════╝
            """)
    else:
        print("\n❌ Migration cancelled")

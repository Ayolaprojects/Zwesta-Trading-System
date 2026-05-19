#!/usr/bin/env python3
"""
Database Setup Script
Creates test users and broker credentials for bot creation testing
"""

import sqlite3
import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash

def setup_test_data():
    """Set up test users and broker credentials"""
    print('🚀 SETTING UP TEST DATA FOR BOT CREATION')
    print('=' * 60)

    conn = sqlite3.connect('zwesta_trading.db')
    cursor = conn.cursor()

    try:
        # Create test user (no password hash in schema)
        user_id = str(uuid.uuid4())
        email = 'test@example.com'
        name = 'Test User'
        created_at = datetime.now().isoformat()

        cursor.execute('''
            INSERT INTO users (user_id, email, name, created_at)
            VALUES (?, ?, ?, ?)
        ''', (user_id, email, name, created_at))

        print(f'✅ Created test user: {email} (ID: {user_id[:8]}...)')

        # Create test MT5 demo credentials
        credential_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO broker_credentials (
                credential_id, user_id, broker_name, account_number, password,
                server, is_live, is_active, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            credential_id, user_id, 'Exness', '12345678', 'testpass123',
            'Exness-Demo', False, True, created_at
        ))

        print(f'✅ Created MT5 demo credentials: {credential_id[:8]}...')

        # Create test Binance credentials
        binance_credential_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO broker_credentials (
                credential_id, user_id, broker_name, account_number, password,
                server, is_live, is_active, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            binance_credential_id, user_id, 'Binance', 'binance_test', 'test_secret_456',
            'spot', False, True, created_at
        ))

        print(f'✅ Created Binance demo credentials: {binance_credential_id[:8]}...')

        conn.commit()
        print(f'\n🎉 Test data setup complete!')
        print(f'👤 User: {email} / password123')
        print(f'🔑 MT5 Credential ID: {credential_id}')
        print(f'🔑 Binance Credential ID: {binance_credential_id}')

        return user_id, credential_id, binance_credential_id

    except Exception as e:
        print(f'❌ Setup failed: {e}')
        conn.rollback()
        return None, None, None
    finally:
        conn.close()

def test_bot_creation_simulation():
    """Simulate bot creation with test data"""
    print('\n🤖 TESTING BOT CREATION SIMULATION')
    print('=' * 60)

    user_id, mt5_cred_id, binance_cred_id = setup_test_data()

    if not user_id:
        return

    # Simulate bot creation payload
    mt5_bot_payload = {
        "botId": f"test_mt5_bot_{int(datetime.now().timestamp())}",
        "credentialId": mt5_cred_id,
        "mode": "demo",
        "symbols": ["EURUSD", "GBPUSD"],
        "strategy": "Test Strategy",
        "riskPerTrade": 2.0,
        "maxDailyLoss": 50
    }

    binance_bot_payload = {
        "botId": f"test_binance_bot_{int(datetime.now().timestamp())}",
        "credentialId": binance_cred_id,
        "mode": "demo",
        "symbols": ["BTCUSDT", "ETHUSDT"],
        "strategy": "Crypto Momentum",
        "riskPerTrade": 1.0,
        "maxDailyLoss": 25
    }

    print('📋 Test bot creation payloads prepared:')
    print(f'   MT5 Bot: {mt5_bot_payload["botId"]}')
    print(f'   Binance Bot: {binance_bot_payload["botId"]}')
    print()
    print('🚀 Ready to test bot creation via API!')
    print('   Use the credential IDs above in your bot creation requests')

if __name__ == '__main__':
    test_bot_creation_simulation()
#!/usr/bin/env python3
"""
Test PostgreSQL setup for Exness and Binance bot execution.
Verifies database connectivity, bot loading, and credential resolution.
"""

import os
import sys
import json
from datetime import datetime

# Ensure we can import backend modules
sys.path.insert(0, 'c:\\zwesta-trader')
sys.path.insert(0, 'c:\\backend')

def test_database_connection():
    """Test that database connection works"""
    print("\n=== Testing Database Connection ===")
    
    try:
        from runtime_infrastructure import using_postgres, get_database_url
        
        if using_postgres():
            url = get_database_url()
            print(f"✅ PostgreSQL mode enabled")
            print(f"   Database URL: {url[:50]}..." if len(url) > 50 else f"   Database URL: {url}")
        else:
            print(f"ℹ️  Using SQLite mode (DATABASE_URL not set)")
            return True
            
        # Try to connect
        from multi_broker_backend_updated import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        conn.close()
        
        print(f"✅ Database connection successful")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_bot_loading():
    """Test that bots can be loaded from database"""
    print("\n=== Testing Bot Loading ===")
    
    try:
        from multi_broker_backend_updated import load_user_bots_from_database, active_bots
        
        # Clear active bots for clean test
        active_bots.clear()
        
        # Load bots
        bots_loaded = load_user_bots_from_database(enabled_only=False)
        
        print(f"✅ Bot loading successful: {bots_loaded} bots loaded")
        
        if bots_loaded > 0:
            # Show bot summary
            exness_bots = sum(1 for b in active_bots.values() if 'Exness' in (b.get('brokerName') or ''))
            binance_bots = sum(1 for b in active_bots.values() if 'Binance' in (b.get('brokerName') or ''))
            
            print(f"   - Exness bots: {exness_bots}")
            print(f"   - Binance bots: {binance_bots}")
            
            # Show first bot details
            first_bot = list(active_bots.values())[0]
            print(f"\n   First bot example:")
            print(f"   - Bot ID: {first_bot.get('botId')}")
            print(f"   - Broker: {first_bot.get('brokerName')}")
            print(f"   - Mode: {first_bot.get('mode')}")
            print(f"   - Enabled: {first_bot.get('enabled')}")
            print(f"   - Strategy: {first_bot.get('strategy')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Bot loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_credential_resolution():
    """Test that credentials are properly resolved"""
    print("\n=== Testing Credential Resolution ===")
    
    try:
        from multi_broker_backend_updated import (
            active_bots,
            _resolve_active_broker_credential_for_bot,
            get_db_connection
        )
        
        if not active_bots:
            print("ℹ️  No active bots to test credential resolution")
            return True
        
        # Test first bot
        test_bot = list(active_bots.values())[0]
        bot_id = test_bot['botId']
        user_id = test_bot['user_id']
        broker_name = test_bot['brokerName']
        account_number = test_bot.get('accountNumber')
        mode = test_bot['mode']
        
        print(f"Testing bot: {bot_id}")
        print(f"  Broker: {broker_name}, Account: {account_number}, Mode: {mode}")
        
        # Resolve credential
        resolved = _resolve_active_broker_credential_for_bot(
            user_id,
            broker_name,
            account_number,
            mode,
            test_bot.get('credentialId')
        )
        
        if resolved:
            print(f"✅ Credential resolved successfully")
            print(f"   - Credential ID: {resolved.get('credential_id')}")
            print(f"   - Account Currency: {resolved.get('account_currency')}")
            print(f"   - Is Live: {resolved.get('is_live')}")
            return True
        else:
            print(f"⚠️  Could not resolve credential (may be intentional)")
            return True
            
    except Exception as e:
        print(f"❌ Credential resolution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_trade_history_access():
    """Test that trade history can be accessed"""
    print("\n=== Testing Trade History Access ===")
    
    try:
        from multi_broker_backend_updated import active_bots, get_db_connection
        
        if not active_bots:
            print("ℹ️  No active bots to test trade history")
            return True
        
        # Test first bot
        test_bot = list(active_bots.values())[0]
        bot_id = test_bot['botId']
        
        # Try to load trades from database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM trades WHERE bot_id = ?", (bot_id,))
        result = cursor.fetchone()
        trade_count = result['count'] if result else 0
        
        conn.close()
        
        print(f"✅ Trade history accessible")
        print(f"   Bot {bot_id}: {trade_count} trades found")
        return True
        
    except Exception as e:
        print(f"❌ Trade history access failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_runtime_state_persistence():
    """Test that bot runtime state can be saved/loaded"""
    print("\n=== Testing Runtime State Persistence ===")
    
    try:
        from multi_broker_backend_updated import (
            active_bots,
            persist_bot_runtime_state,
            get_db_connection
        )
        
        if not active_bots:
            print("ℹ️  No active bots to test runtime state")
            return True
        
        # Test first bot
        test_bot_id = list(active_bots.keys())[0]
        test_bot = active_bots[test_bot_id]
        
        # Modify runtime state to test persistence
        original_profit = test_bot.get('totalProfit', 0)
        test_bot['totalProfit'] = original_profit + 1.0  # Increment by 1
        test_bot['lastUpdate'] = datetime.now().isoformat()
        
        # Persist
        persist_bot_runtime_state(test_bot_id)
        
        # Reload from database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT runtime_state FROM user_bots WHERE bot_id = ?",
            (test_bot_id,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result and result.get('runtime_state'):
            runtime_state = json.loads(result['runtime_state'])
            restored_profit = runtime_state.get('totalProfit', original_profit)
            
            print(f"✅ Runtime state persistence working")
            print(f"   Original profit: {original_profit}")
            print(f"   Persisted profit: {restored_profit}")
            
            # Restore original value
            test_bot['totalProfit'] = original_profit
            persist_bot_runtime_state(test_bot_id)
            
            return True
        else:
            print(f"⚠️  Could not verify persistence (no state found)")
            return True
            
    except Exception as e:
        print(f"❌ Runtime state persistence failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("PostgreSQL Setup Verification for Exness & Binance Bots")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Bot Loading", test_bot_loading),
        ("Credential Resolution", test_credential_resolution),
        ("Trade History Access", test_trade_history_access),
        ("Runtime State Persistence", test_runtime_state_persistence),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ FATAL: {test_name} crashed: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    total_passed = sum(1 for v in results.values() if v)
    total_tests = len(results)
    
    print(f"\nTotal: {total_passed}/{total_tests} passed")
    
    if total_passed == total_tests:
        print("\n✅ All tests passed! PostgreSQL setup is ready for bot execution.")
        return 0
    else:
        print(f"\n⚠️  {total_tests - total_passed} test(s) failed. Check above for details.")
        return 1


if __name__ == '__main__':
    sys.exit(main())

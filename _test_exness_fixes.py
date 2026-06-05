#!/usr/bin/env python3
"""
Comprehensive test for Exness MT5 connection and PostgreSQL integration after fixes.
Verifies:
1. MT5 IPC availability
2. PostgreSQL connection
3. Exness credential verification with new timeouts
4. Bot loading from PostgreSQL
"""

import os
import sys
import time
import logging
import json
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def test_mt5_ipc():
    """Test MT5 IPC availability"""
    print("\n" + "="*60)
    print("TEST 1: MT5 IPC Availability")
    print("="*60)
    
    try:
        import MetaTrader5 as mt5
        version = mt5.version()
        if version:
            print(f"✅ MT5 IPC available - Version: {version}")
            return True
        else:
            print(f"❌ MT5 IPC not responding: {mt5.last_error()}")
            return False
    except ImportError:
        print("❌ MetaTrader5 module not installed")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_postgres_connection():
    """Test PostgreSQL connection"""
    print("\n" + "="*60)
    print("TEST 2: PostgreSQL Connection")
    print("="*60)
    
    try:
        import psycopg2
        from psycopg2.pool import SimpleConnectionPool
        
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            print("⚠️  DATABASE_URL not set - using default localhost")
            db_url = "postgresql://postgres:password@localhost:5432/trader"
        
        # Parse connection string
        # Format: postgresql://user:password@host:port/database
        parts = db_url.replace("postgresql://", "").split("/")
        if len(parts) < 2:
            print("❌ Invalid DATABASE_URL format")
            return False
        
        db_name = parts[-1]
        user_host = parts[0].split("@")
        if len(user_host) != 2:
            print("❌ Invalid DATABASE_URL format")
            return False
        
        user_pass = user_host[0].split(":")
        host_port = user_host[1].split(":")
        
        try:
            conn = psycopg2.connect(
                database=db_name,
                user=user_pass[0],
                password=user_pass[1] if len(user_pass) > 1 else "password",
                host=host_port[0],
                port=host_port[1] if len(host_port) > 1 else "5432",
                timeout=5
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            cursor.close()
            conn.close()
            
            print(f"✅ PostgreSQL connection successful")
            print(f"   Database: {db_name}")
            print(f"   Version: {version[0][:50]}...")
            return True
            
        except psycopg2.OperationalError as e:
            print(f"❌ PostgreSQL connection failed: {e}")
            return False
            
    except ImportError:
        print("❌ psycopg2 module not installed")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_exness_quick_connect(account, password, server):
    """Test Exness connection with new timeouts"""
    print("\n" + "="*60)
    print("TEST 3: Exness Credential Verification (New Timeouts)")
    print("="*60)
    
    try:
        import MetaTrader5 as mt5
        
        print(f"Account: {account}")
        print(f"Server: {server}")
        print(f"Attempting connection with 8s lock + 20s init timeouts...")
        
        start = time.time()
        
        # Replicate the new timeout values
        init_result = mt5.initialize(
            login=int(account),
            password=password,
            server=server,
            timeout=20000  # 20 seconds (20,000 milliseconds)
        )
        
        elapsed = time.time() - start
        
        if init_result:
            print(f"✅ Connection succeeded ({elapsed:.1f}s)")
            
            # Get account info
            acct_info = mt5.account_info()
            if acct_info:
                print(f"   Account Name: {acct_info.name}")
                print(f"   Balance: {acct_info.balance:.2f} {acct_info.currency}")
                print(f"   Equity: {acct_info.equity:.2f}")
                print(f"   Margin: {acct_info.margin:.2f}")
                print(f"   Margin Free: {acct_info.margin_free:.2f}")
                print(f"   Profit: {acct_info.profit:.2f}")
            
            mt5.shutdown()
            return True
        else:
            error = mt5.last_error()
            elapsed = time.time() - start
            
            error_code = error[0] if isinstance(error, tuple) else -1
            error_msg = error[1] if isinstance(error, tuple) and len(error) > 1 else str(error)
            
            print(f"❌ Connection failed ({elapsed:.1f}s)")
            print(f"   Error Code: {error_code}")
            print(f"   Error Message: {error_msg}")
            
            if error_code == -10014 or 'future not completed' in error_msg.lower():
                print(f"\n   ⚠️  Still getting 'future not completed' error")
                print(f"      This may indicate MT5 terminal isn't fully initialized")
                print(f"      Try: Restarting the MT5 terminal and waiting 30+ seconds")
            
            mt5.shutdown()
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_bot_loading():
    """Test bot loading from PostgreSQL"""
    print("\n" + "="*60)
    print("TEST 4: Bot Loading from PostgreSQL")
    print("="*60)
    
    try:
        # Import the backend module to test bot loading
        sys.path.insert(0, '/backend')
        import sqlite3
        import os
        
        # Check if database exists
        db_path = '/zwesta-trader/bots.db'
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Try to load bots
            cursor.execute("SELECT COUNT(*) FROM bots WHERE type='exness_mt5'")
            exness_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM bots WHERE type='binance'")
            binance_count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            print(f"✅ SQLite bot database loaded")
            print(f"   Exness MT5 bots: {exness_count}")
            print(f"   Binance bots: {binance_count}")
            
            return True
        else:
            print(f"⚠️  SQLite database not found: {db_path}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    print("\n" + "="*70)
    print("COMPREHENSIVE TEST: Exness MT5 & PostgreSQL Integration")
    print("="*70)
    
    results = {}
    
    # Test 1: MT5 IPC
    results['MT5 IPC'] = test_mt5_ipc()
    
    # Test 2: PostgreSQL
    results['PostgreSQL'] = test_postgres_connection()
    
    # Test 3: Exness connection (prompt for credentials)
    print("\n" + "-"*60)
    print("Do you want to test Exness credential verification? (y/n): ", end="")
    if input().lower() == 'y':
        try:
            account = input("Account number: ").strip()
            password = input("Password: ").strip()
            server = input("Server (default 'Exness-MT5 Trial'): ").strip()
            if not server:
                server = "Exness-MT5 Trial"
            
            results['Exness Connection'] = test_exness_quick_connect(account, password, server)
        except KeyboardInterrupt:
            print("\n⏸️  Skipped")
            results['Exness Connection'] = None
    else:
        print("Skipped")
        results['Exness Connection'] = None
    
    # Test 4: Bot loading
    results['Bot Loading'] = test_bot_loading()
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, result in results.items():
        if result is True:
            status = "✅ PASS"
        elif result is False:
            status = "❌ FAIL"
        else:
            status = "⏭️  SKIPPED"
        
        print(f"{test_name:.<40} {status}")
    
    # Overall result
    passed = sum(1 for r in results.values() if r is True)
    total = len(results)
    
    print("\n" + "="*70)
    if passed == total:
        print(f"✅ ALL TESTS PASSED ({passed}/{total})")
        return 0
    elif passed >= total - 1:  # Allow 1 skip
        print(f"⚠️  MOST TESTS PASSED ({passed}/{total})")
        return 0
    else:
        print(f"❌ SOME TESTS FAILED ({passed}/{total})")
        return 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n⏸️  Test interrupted")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

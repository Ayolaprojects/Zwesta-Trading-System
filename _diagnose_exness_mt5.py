#!/usr/bin/env python3
"""
Diagnose Exness MT5 connection issues during credential testing.
Helps identify why "future not completed" errors occur.
"""

import os
import sys
import time
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

def check_mt5_terminal_running():
    """Check if any MT5 terminal is running"""
    print("\n=== Checking MT5 Terminal Status ===")
    
    try:
        import psutil
        
        mt5_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                if 'terminal' in proc.name().lower() or 'metatrader' in proc.name().lower():
                    mt5_processes.append({
                        'pid': proc.pid,
                        'name': proc.name(),
                        'exe': proc.exe()
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        if mt5_processes:
            print(f"✅ Found {len(mt5_processes)} MT5 terminal process(es):")
            for proc in mt5_processes:
                print(f"   - PID {proc['pid']}: {proc['name']}")
                print(f"     Path: {proc['exe']}")
        else:
            print("❌ No MT5 terminal processes found!")
            print("   Action: Start the Exness MetaTrader 5 terminal manually")
            return False
        
        return True
        
    except ImportError:
        print("⚠️  psutil not installed - cannot check process list")
        print("   Install with: pip install psutil")
        return None
    except Exception as e:
        print(f"❌ Error checking MT5 processes: {e}")
        return None


def check_mt5_ipc_availability():
    """Check if MT5 IPC channel is available"""
    print("\n=== Checking MT5 IPC Channel ===")
    
    try:
        import MetaTrader5 as mt5
        
        # Try to get version (lightweight operation)
        version = mt5.version()
        if version:
            print(f"✅ MT5 IPC available")
            print(f"   Version: {version}")
            return True
        else:
            print(f"❌ MT5 IPC not responding")
            print(f"   Error: {mt5.last_error()}")
            return False
            
    except ImportError:
        print("❌ MetaTrader5 module not installed")
        print("   Install with: pip install MetaTrader5")
        return None
    except Exception as e:
        print(f"❌ Error checking MT5 IPC: {e}")
        return None


def check_exness_account_access(account, password, server, path=None):
    """Try to connect to Exness account"""
    print(f"\n=== Testing Exness Account Access ===")
    print(f"Account: {account}")
    print(f"Server: {server}")
    print(f"Path: {path or '(default)'}")
    
    try:
        import MetaTrader5 as mt5
        
        # Try with increased timeouts
        print("\n⏳ Attempting MT5 connection with 10s timeout...")
        start = time.time()
        
        if path:
            init_result = mt5.initialize(path, login=int(account), password=password, server=server, timeout=10000)
        else:
            init_result = mt5.initialize(login=int(account), password=password, server=server, timeout=10000)
        
        elapsed = time.time() - start
        
        if init_result:
            print(f"✅ MT5 connection succeeded ({elapsed:.1f}s)")
            
            # Get account info
            acct_info = mt5.account_info()
            if acct_info:
                print(f"   Balance: {acct_info.balance} {acct_info.currency}")
                print(f"   Equity: {acct_info.equity}")
                print(f"   Margin: {acct_info.margin}")
                print(f"   Margin Free: {acct_info.margin_free}")
            
            mt5.shutdown()
            return True
        else:
            error = mt5.last_error()
            error_code = error[0] if isinstance(error, tuple) else -1
            error_msg = error[1] if isinstance(error, tuple) and len(error) > 1 else str(error)
            
            print(f"❌ MT5 connection failed ({elapsed:.1f}s)")
            print(f"   Error Code: {error_code}")
            print(f"   Error Message: {error_msg}")
            
            if error_code == -10014 or 'future not completed' in error_msg.lower():
                print(f"\n   🔍 ISSUE: 'Future not completed' (error -10014)")
                print(f"      This means MT5 IPC is busy or not fully initialized")
                print(f"      Suggestions:")
                print(f"      1. Wait 30+ seconds for MT5 to fully load")
                print(f"      2. Close other MT5 instances or processes")
                print(f"      3. Restart the MT5 terminal")
                print(f"      4. Check system resources (CPU, memory)")
            
            mt5.shutdown()
            return False
            
    except Exception as e:
        print(f"❌ Exception during connection test: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    print("=" * 60)
    print("Exness MT5 Connection Diagnostic")
    print("=" * 60)
    
    # Check MT5 terminal
    term_running = check_mt5_terminal_running()
    if term_running is False:
        print("\n❌ FATAL: No MT5 terminal running")
        print("   Start Exness MetaTrader 5 and try again")
        return 1
    
    # Check IPC
    ipc_ok = check_mt5_ipc_availability()
    if ipc_ok is False:
        print("\n❌ FATAL: MT5 IPC not responding")
        print("   Wait for MT5 to fully load or restart the terminal")
        return 1
    
    if ipc_ok is None:
        print("\n⚠️  Cannot verify MT5 availability")
        return 1
    
    # Try to get credentials from user
    print("\n=== Testing Exness Account Connection ===")
    print("Enter your Exness credentials to test the connection")
    print("(or press Ctrl+C to skip)")
    
    try:
        account = input("Account number (9 digits): ").strip()
        if not account.isdigit() or len(account) != 9:
            print("❌ Invalid account number format")
            return 1
        
        password = input("Password: ").strip()
        if not password:
            print("❌ Password required")
            return 1
        
        server = input("Server (e.g., Exness-MT5 Trial, Exness-MT5): ").strip()
        if not server:
            server = "Exness-MT5 Trial"
        
        # Attempt connection
        result = check_exness_account_access(account, password, server)
        
        if result is True:
            print("\n✅ Exness credentials are working!")
            return 0
        elif result is False:
            print("\n❌ Connection failed - check error details above")
            return 1
        else:
            print("\n⚠️  Could not complete test")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏸️  Test skipped")
        return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

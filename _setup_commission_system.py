"""
Quick Setup Script for Binance Commission Auto-Collection
Integrates commission system into your existing backend
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def setup_commission_system():
    """Setup commission collection system"""
    
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║  Binance Commission Auto-Collection Setup                        ║
║  Integrating into multi_broker_backend_updated.py                ║
╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    # Step 1: Check database
    print("\n📊 Step 1: Checking database...")
    try:
        import sqlite3
        db_path = r'C:\backend\zwesta_trading.db'
        
        if not os.path.exists(db_path):
            print(f"❌ Database not found at {db_path}")
            print("   Creating new database...")
            # Will be created when tables are set up
        else:
            print(f"✅ Database found: {db_path}")
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Create commission tables
        print("\n📋 Creating commission tracking tables...")
        from binance_commission_system import create_commission_tables
        create_commission_tables(cursor)
        conn.commit()
        
        print("✅ Database setup complete")
        conn.close()
    
    except Exception as e:
        print(f"❌ Database setup error: {e}")
        return False
    
    # Step 2: Check backend file
    print("\n📝 Step 2: Checking backend integration...")
    backend_path = r'c:\zwesta-trader\Zwesta Flutter App\multi_broker_backend_updated.py'
    
    if not os.path.exists(backend_path):
        print(f"❌ Backend file not found: {backend_path}")
        return False
    
    with open(backend_path, 'r', encoding='utf-8') as f:
        backend_code = f.read()
    
    # Check if already integrated
    if 'binance_commission_system' in backend_code:
        print("✅ Commission system already integrated in backend")
    else:
        print("⚠️  Commission system NOT yet integrated")
        print("\nTo integrate, add this to your backend file:\n")
        print("=" * 70)
        print("""
# Add near the top of the file (after other imports)
from binance_commission_system import add_commission_endpoints

# Add after Flask app is created (after: app = Flask(__name__))
# and after defining get_db_connection, require_admin, require_session, logger

# Initialize commission endpoints
add_commission_endpoints(app, get_db_connection, require_admin, require_session, logger)
        """)
        print("=" * 70)
    
    # Step 3: Environment variables
    print("\n🔑 Step 3: Environment Variable Setup")
    print("\nYou have 3 options for commission collection:\n")
    
    print("📌 METHOD 1: Sub-Account System (Recommended for Scale)")
    print("   Requires: Binance Corporate Account")
    print("   Environment Variables:")
    print("   - BINANCE_MASTER_API_KEY=<your_master_key>")
    print("   - BINANCE_MASTER_SECRET_KEY=<your_master_secret>\n")
    
    print("📌 METHOD 2: API Key Delegation (Good for Mid-Scale)")
    print("   Requires: Users grant withdrawal API keys")
    print("   Environment Variables:")
    print("   - ZWESTA_USDT_WALLET_ADDRESS=<your_trc20_usdt_address>")
    print("   - ZWESTA_BINANCE_EMAIL=admin@zwestatrader.com\n")
    
    print("📌 METHOD 3: Manual Payment (Start Here)")
    print("   Requires: No special setup, users pay commission manually")
    print("   Environment Variables:")
    print("   - ZWESTA_BINANCE_EMAIL=admin@zwestatrader.com (for Binance Pay transfers)")
    print("   - ZWESTA_USDT_WALLET_ADDRESS=<your_wallet> (for crypto transfers)\n")
    
    # Check current environment
    master_key = os.getenv('BINANCE_MASTER_API_KEY')
    wallet = os.getenv('ZWESTA_USDT_WALLET_ADDRESS')
    email = os.getenv('ZWESTA_BINANCE_EMAIL')
    
    print("\n📍 Current Environment Status:")
    print(f"   BINANCE_MASTER_API_KEY: {'✅ Set' if master_key else '❌ Not set'}")
    print(f"   ZWESTA_USDT_WALLET_ADDRESS: {'✅ Set' if wallet else '❌ Not set'}")
    print(f"   ZWESTA_BINANCE_EMAIL: {'✅ Set' if email else '❌ Not set'}")
    
    if not (master_key or wallet or email):
        print("\n⚠️  No environment variables configured")
        print("   Start with METHOD 3 (Manual) and set ZWESTA_BINANCE_EMAIL")
    
    # Step 4: Available endpoints
    print("\n\n🌐 Step 4: Available API Endpoints")
    print("=" * 70)
    
    endpoints = [
        ("POST", "/api/user/request-withdrawal", "User requests profit withdrawal"),
        ("POST", "/api/admin/collect-commissions", "Auto-collect all commissions"),
        ("GET", "/api/admin/withdrawals/pending", "View pending withdrawals"),
        ("POST", "/api/admin/withdrawals/<id>/approve", "Approve withdrawal request"),
        ("POST", "/api/admin/binance/create-subaccount", "Create sub-account for user"),
    ]
    
    print(f"{'Method':<8} {'Endpoint':<45} {'Description':<30}")
    print("-" * 70)
    for method, endpoint, desc in endpoints:
        print(f"{method:<8} {endpoint:<45} {desc:<30}")
    
    print("=" * 70)
    
    # Step 5: Quick test
    print("\n\n🧪 Step 5: Quick Test")
    print("\nTo test the system:")
    print("1. Restart your backend: python multi_broker_backend_updated.py")
    print("2. Test admin endpoints:")
    print("""
   curl http://localhost:9000/api/admin/withdrawals/pending \\
     -H "X-API-Key: your_admin_api_key"
    """)
    
    print("\n✅ Setup Complete!")
    print("\n📖 Full documentation: C:\\Users\\zwexm\\LPSN\\ZWESTA_TRADER\\ADMIN_SYSTEM_GUIDE.md")
    
    return True

if __name__ == '__main__':
    try:
        success = setup_commission_system()
        if success:
            print("\n🎉 Commission system ready to use!")
        else:
            print("\n❌ Setup incomplete - check errors above")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

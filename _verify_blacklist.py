#!/usr/bin/env python3
"""
Verify symbol blacklist is properly integrated and working
"""
import sqlite3
import json
import os

DB_PATH = r'C:\backend\zwesta_trading.db'
BLACKLIST_PATH = r'C:\backend\symbol_blacklist.json'

def verify_blacklist_file():
    """Check if blacklist file exists and is valid"""
    print("=" * 80)
    print("🔍 BLACKLIST FILE VERIFICATION")
    print("=" * 80)
    print()
    
    if not os.path.exists(BLACKLIST_PATH):
        print(f"❌ FAIL: Blacklist file not found at {BLACKLIST_PATH}")
        return False
    
    try:
        with open(BLACKLIST_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        blacklist = config.get('blacklisted_symbols', [])
        details = config.get('blacklist_details', {})
        
        print(f"✅ PASS: Blacklist file exists and is valid")
        print(f"   Path: {BLACKLIST_PATH}")
        print(f"   Symbols: {len(blacklist)} blacklisted")
        print(f"   Details: {len(details)} symbols with metadata")
        print()
        
        # Show first 10 blacklisted symbols
        print("📋 Blacklisted Symbols (first 10):")
        for i, symbol in enumerate(blacklist[:10], 1):
            info = details.get(symbol, {})
            pf = info.get('pf', 'N/A')
            reason = info.get('reason', 'No reason provided')[:50]
            print(f"   {i:2}. {symbol:12} - PF={pf:4} - {reason}")
        
        if len(blacklist) > 10:
            print(f"   ... and {len(blacklist) - 10} more")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Error reading blacklist file: {e}")
        return False

def verify_database_bots():
    """Check if bots in database have no blacklisted symbols"""
    print("=" * 80)
    print("🔍 DATABASE BOT VERIFICATION")
    print("=" * 80)
    print()
    
    # Load blacklist
    with open(BLACKLIST_PATH, 'r', encoding='utf-8') as f:
        blacklist = json.load(f).get('blacklisted_symbols', [])
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("SELECT bot_id, name, runtime_state FROM user_bots")
    bots = cur.fetchall()
    
    all_pass = True
    
    for bot_id, name, runtime_state in bots:
        rs = json.loads(runtime_state or '{}')
        symbols = rs.get('symbols', [])
        
        if not symbols:
            print(f"⚪ SKIP: Bot {bot_id[:25]}... has no symbols configured")
            continue
        
        blacklisted_found = [s for s in symbols if s in blacklist]
        
        if blacklisted_found:
            print(f"❌ FAIL: Bot {bot_id[:25]}...")
            print(f"   Name: {name}")
            print(f"   Has blacklisted: {blacklisted_found}")
            print(f"   All symbols: {symbols}")
            all_pass = False
        else:
            print(f"✅ PASS: Bot {bot_id[:25]}...")
            print(f"   Name: {name}")
            print(f"   Symbols: {symbols}")
        
        print()
    
    conn.close()
    
    if all_pass:
        print("✅ ALL BOTS CLEAN - No blacklisted symbols found")
    else:
        print("❌ SOME BOTS HAVE BLACKLISTED SYMBOLS - Run _configure_blacklist.py")
    
    print()
    return all_pass

def verify_backend_code():
    """Check if backend code has blacklist integration"""
    print("=" * 80)
    print("🔍 BACKEND CODE VERIFICATION")
    print("=" * 80)
    print()
    
    backend_path = r'C:\backend\multi_broker_backend_updated.py'
    
    if not os.path.exists(backend_path):
        print(f"❌ FAIL: Backend file not found at {backend_path}")
        return False
    
    with open(backend_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = {
        'SYMBOL_BLACKLIST declaration': 'SYMBOL_BLACKLIST = []',
        'Blacklist loading code': 'symbol_blacklist.json',
        'Scanner filtering': 'if SYMBOL_BLACKLIST:',
        'Filter blacklisted symbols': 's not in SYMBOL_BLACKLIST',
    }
    
    all_pass = True
    
    for check_name, search_string in checks.items():
        if search_string in content:
            print(f"✅ PASS: {check_name}")
        else:
            print(f"❌ FAIL: {check_name}")
            all_pass = False
    
    print()
    
    if all_pass:
        print("✅ Backend code has blacklist integration")
        print("⚠️  NOTE: Backend restart required to load changes")
    else:
        print("❌ Backend code missing blacklist integration")
        print("   Run the code integration steps manually")
    
    print()
    return all_pass

def main():
    print("=" * 80)
    print("🚫 SYMBOL BLACKLIST VERIFICATION")
    print("=" * 80)
    print()
    
    # Run all checks
    file_ok = verify_blacklist_file()
    db_ok = verify_database_bots()
    code_ok = verify_backend_code()
    
    # Summary
    print("=" * 80)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 80)
    print()
    
    print(f"{'✅' if file_ok else '❌'} Blacklist File: {'PASS' if file_ok else 'FAIL'}")
    print(f"{'✅' if db_ok else '❌'} Database Bots: {'PASS' if db_ok else 'FAIL'}")
    print(f"{'✅' if code_ok else '❌'} Backend Code: {'PASS' if code_ok else 'FAIL'}")
    print()
    
    if file_ok and db_ok and code_ok:
        print("🎉 ALL CHECKS PASSED!")
        print()
        print("✅ Blacklist system is properly configured")
        print("✅ No blacklisted symbols in database")
        print("✅ Backend code integrated")
        print()
        print("⚠️  NEXT STEP: Restart backend to activate blacklist")
        print()
        print("   cd C:\\backend")
        print("   Remove-Item -Recurse -Force __pycache__")
        print("   python -B multi_broker_backend_updated.py")
        print()
    else:
        print("⚠️  SOME CHECKS FAILED - Review above for details")
        print()
        if not file_ok:
            print("   Run: python _configure_blacklist.py")
        if not db_ok:
            print("   Run: python _configure_blacklist.py")
        if not code_ok:
            print("   Follow integration instructions in BLACKLIST_INTEGRATION.md")
    
    print()

if __name__ == "__main__":
    main()

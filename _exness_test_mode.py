"""Enable Exness bots in test mode OR reverse signals if needed"""
import json
import sqlite3
import sys
from datetime import datetime

DB = r'C:\backend\zwesta_trading.db'
NOW = datetime.now().isoformat()

def enable_test_mode():
    """Re-enable bots in test mode after fix verification"""
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    cur = c.cursor()
    
    print("="*80)
    print("EXNESS TEST MODE - RE-ENABLE BOTS (if fix is working)")
    print("="*80)
    
    cur.execute("""
        SELECT bot_id, runtime_state FROM user_bots 
        WHERE broker_account_id LIKE 'Exness_%'
    """)
    
    for row in cur.fetchall():
        rs = json.loads(row['runtime_state'] or '{}')
        rs['enabled'] = True
        rs['pauseReason'] = None
        rs['testModeStarted'] = NOW
        rs['testModeNotes'] = 'Position size 0.5, TP:SL 1:3, hard limits enabled'
        
        cur.execute(
            "UPDATE user_bots SET runtime_state=?, updated_at=? WHERE bot_id=?",
            (json.dumps(rs), NOW, row['bot_id'])
        )
        print(f"✓ {row['bot_id'][-10:]}: ENABLED (test mode, 0.5 lots)")
    
    c.commit()
    c.close()
    print("\n✅ Bots re-enabled. Monitor for 24-48 hours.")

def enable_signal_reversal():
    """Reverse all signals if they're inverted"""
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    cur = c.cursor()
    
    print("="*80)
    print("EXNESS SIGNAL REVERSAL - TEST INVERTED SIGNALS")
    print("="*80)
    
    cur.execute("""
        SELECT bot_id, runtime_state FROM user_bots 
        WHERE broker_account_id LIKE 'Exness_%'
    """)
    
    for row in cur.fetchall():
        rs = json.loads(row['runtime_state'] or '{}')
        rs['reverseSignals'] = True
        rs['signalInversionTest'] = 'ACTIVE'
        rs['signalReversalStarted'] = NOW
        rs['enabled'] = True
        
        cur.execute(
            "UPDATE user_bots SET runtime_state=?, updated_at=? WHERE bot_id=?",
            (json.dumps(rs), NOW, row['bot_id'])
        )
        print(f"✓ {row['bot_id'][-10:]}: Signals REVERSED")
    
    c.commit()
    c.close()
    print("\n⚠️  Testing reversed signals. If this improves win rate, signals were inverted.")

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python _exness_test_mode.py test      # Re-enable for monitoring")
        print("  python _exness_test_mode.py reverse   # Reverse signals (if inverted)")
        return 1
    
    cmd = sys.argv[1].lower()
    
    if cmd == 'test':
        enable_test_mode()
    elif cmd == 'reverse':
        enable_signal_reversal()
    else:
        print(f"Unknown command: {cmd}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())

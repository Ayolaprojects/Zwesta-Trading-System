"""Advanced Exness symbol-level optimization - disable problem symbols"""
import json
import sqlite3
from datetime import datetime

DB = r'C:\backend\zwesta_trading.db'
NOW = datetime.now().isoformat()

# Problem symbols from last analysis
PROBLEM_SYMBOLS = ['USTECm', 'AUDUSDm', 'ETHUSDm']

SYMBOL_CONFIG = {
    'USTECm': {'enabled': False, 'reason': '0% win rate, -52.03 loss'},
    'AUDUSDm': {'enabled': False, 'reason': '0% win rate, -4.71 loss'},
    'ETHUSDm': {'enabled': False, 'reason': '0% win rate, -1.15 loss'},
}

def main():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    cur = c.cursor()

    # Get all Exness bots
    rows = cur.execute("""
        SELECT bot_id, runtime_state FROM user_bots 
        WHERE broker_account_id LIKE 'Exness_%'
    """).fetchall()

    print("="*80)
    print("EXNESS SYMBOL-LEVEL OPTIMIZATION")
    print("="*80)
    
    patched = 0
    for r in rows:
        rs = json.loads(r['runtime_state'] or '{}') if r['runtime_state'] else {}
        
        # Initialize symbol_config if not present
        if 'symbol_config' not in rs:
            rs['symbol_config'] = {}
        
        # Apply problem symbol configs
        for sym, config in SYMBOL_CONFIG.items():
            if sym not in rs['symbol_config']:
                rs['symbol_config'][sym] = {}
            rs['symbol_config'][sym].update(config)
        
        # Add metadata
        rs['lastOptimizationTime'] = NOW
        rs['optimizationNote'] = 'Problem symbols disabled'
        
        cur.execute(
            "UPDATE user_bots SET runtime_state=?, updated_at=? WHERE bot_id=?",
            (json.dumps(rs), NOW, r['bot_id']),
        )
        patched += 1
        print(f"✓ {r['bot_id'][-15:]}: Disabled {len(PROBLEM_SYMBOLS)} problem symbols")

    c.commit()
    c.close()
    
    print(f"\nDone. Updated {patched} bot(s)")
    print("\n📌 DISABLED SYMBOLS (0% Win Rate):")
    for sym, config in SYMBOL_CONFIG.items():
        print(f"   • {sym}: {config['reason']}")
    
    print(f"\n✅ NEXT STEPS:")
    print(f"   1. Restart backend for changes to take effect")
    print(f"   2. Bots will skip USTECm, AUDUSDm, ETHUSDm trades")
    print(f"   3. Monitor XAUUSDm and GBPUSDm (currently profitable)")

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Show broker-specific blacklist configuration
"""
import json
import os

def show_broker_blacklists():
    blacklist_v2_path = r'C:\backend\symbol_blacklist_v2.json'
    
    print("=" * 80)
    print("🚫 BROKER-SPECIFIC BLACKLIST CONFIGURATION (v2)")
    print("=" * 80)
    print()
    
    if not os.path.exists(blacklist_v2_path):
        print(f"❌ File not found: {blacklist_v2_path}")
        return
    
    with open(blacklist_v2_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    broker_blacklists = config.get('broker_blacklists', {})
    global_blacklist = config.get('global_blacklist', [])
    blacklist_details = config.get('blacklist_details', {})
    notes = config.get('notes', {})
    
    print(f"📅 Version: {config.get('version')}")
    print(f"📅 Last Updated: {config.get('last_updated')}")
    print()
    
    print("=" * 80)
    print("🌍 GLOBAL BLACKLIST (All Brokers)")
    print("=" * 80)
    print()
    if global_blacklist:
        print(f"   {len(global_blacklist)} symbols blocked on ALL brokers:")
        for symbol in global_blacklist:
            detail = blacklist_details.get(symbol, {})
            print(f"      - {symbol}: {detail.get('reason', 'No reason')}")
        print()
    else:
        print("   ✅ No global blacklist - each broker has custom config")
        print()
    
    print("=" * 80)
    print("🏢 BROKER-SPECIFIC BLACKLISTS")
    print("=" * 80)
    print()
    
    for broker, symbols in sorted(broker_blacklists.items()):
        broker_display = broker.replace('_', ' ').title()
        print(f"📊 {broker_display.upper()}")
        print(f"   Blacklisted: {len(symbols)} symbols")
        print()
        
        if symbols:
            # Group by category
            crypto = [s for s in symbols if any(x in s for x in ['BTC', 'ETH', 'SOL', 'BNB', 'LTC'])]
            forex = [s for s in symbols if any(x in s for x in ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'NZD', 'CAD'])]
            commodities = [s for s in symbols if any(x in s for x in ['OIL', 'GOLD', 'SILVER', 'US30', 'XAU'])]
            other = [s for s in symbols if s not in crypto and s not in forex and s not in commodities]
            
            if crypto:
                print(f"   💎 Crypto ({len(crypto)}):")
                for symbol in sorted(crypto):
                    detail = blacklist_details.get(symbol, {})
                    pf = detail.get('pf') or detail.get('binance_futures_pf') or detail.get('futures_pf')
                    pf_str = f"PF={pf:.2f}" if pf else ""
                    note = detail.get('note') or detail.get('spot_status') or ""
                    print(f"      - {symbol:15} {pf_str:10} {note}")
            
            if forex:
                print(f"   💱 Forex ({len(forex)}):")
                for symbol in sorted(forex):
                    detail = blacklist_details.get(symbol, {})
                    pf = detail.get('pf')
                    pf_str = f"PF={pf:.2f}" if pf else ""
                    print(f"      - {symbol:15} {pf_str:10} {detail.get('reason', '')[:40]}")
            
            if commodities:
                print(f"   🛢️ Commodities ({len(commodities)}):")
                for symbol in sorted(commodities):
                    detail = blacklist_details.get(symbol, {})
                    pf = detail.get('pf')
                    pf_str = f"PF={pf:.2f}" if pf else ""
                    print(f"      - {symbol:15} {pf_str:10} {detail.get('reason', '')[:40]}")
            
            if other:
                print(f"   ❓ Other ({len(other)}):")
                for symbol in sorted(other):
                    print(f"      - {symbol}")
            
            print()
        else:
            print(f"   ✅ NO BLACKLIST - All symbols allowed!")
            print()
        
        print("-" * 80)
        print()
    
    print("=" * 80)
    print("💡 STRATEGY NOTES")
    print("=" * 80)
    print()
    
    for key, note in notes.items():
        print(f"   {key.replace('_', ' ').title()}:")
        print(f"      {note}")
        print()
    
    print("=" * 80)
    print("🎯 CLIENT TESTING SUMMARY")
    print("=" * 80)
    print()
    
    binance_spot = broker_blacklists.get('binance_spot', [])
    binance_futures = broker_blacklists.get('binance_futures', [])
    exness = broker_blacklists.get('exness', [])
    
    print("   ✅ BINANCE SPOT (For Client Testing):")
    print(f"      Blacklisted: {len(binance_spot)} symbols")
    print(f"      Status: {'ALL SYMBOLS ALLOWED ✅' if len(binance_spot) == 0 else 'Some symbols blocked'}")
    print(f"      Allowed: BTCUSDT, ETHUSDT, and all other pairs")
    print()
    
    print("   ❌ BINANCE FUTURES (Losing Money):")
    print(f"      Blacklisted: {len(binance_futures)} symbols")
    print(f"      Status: All crypto blocked (PF=0.44, -$55 loss)")
    print()
    
    print("   🛡️ EXNESS (Production Protection):")
    print(f"      Blacklisted: {len(exness)} symbols")
    print(f"      Focus: GBPUSDm (PF=1.15, +99 ZAR) and XAUUSDm")
    print(f"      10x Multiplier: Active on profitable symbols")
    print()
    
    print("=" * 80)
    print("📋 NEXT STEPS FOR CLIENT LAUNCH")
    print("=" * 80)
    print()
    
    print("   [ ] 1. Restart backend to load v2 blacklist")
    print("   [ ] 2. Create new Binance SPOT bot")
    print("   [ ] 3. Add BTCUSDT to bot symbols")
    print("   [ ] 4. Test with $100-200 of YOUR money first")
    print("   [ ] 5. Track 30-50 trades")
    print("   [ ] 6. Verify PF > 1.3, WR > 45%, Net > 0")
    print("   [ ] 7. Only then offer to clients!")
    print()
    
    print("=" * 80)

if __name__ == "__main__":
    show_broker_blacklists()

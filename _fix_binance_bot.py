#!/usr/bin/env python3
"""Manually fix bot_1779229018996 symbol configuration"""
import sqlite3
import json

DB_PATH = r'C:\backend\zwesta_trading.db'
BOT_ID = 'bot_1779229018996'

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Get current runtime_state
cur.execute("SELECT runtime_state FROM user_bots WHERE bot_id = ?", (BOT_ID,))
row = cur.fetchone()

if row:
    rs = json.loads(row[0])
    
    print("BEFORE:")
    print(f"  Symbols: {rs.get('symbols', [])}")
    print(f"  Signal Threshold: {rs.get('signalThreshold', 'NOT SET')}")
    
    # For Binance Futures, we can't use forex symbols like GBPUSDm
    # So we'll keep it empty to effectively pause the bot
    # (Crypto lost -589 ZAR on BTC, -331 on ETH - all losers)
    rs['symbols'] = []  # Disable crypto trading
    rs['signalThreshold'] = 70  # More selective
    rs['strategyVersion'] = 'optimized_v1_manual'
    rs['lastOptimized'] = '2026-05-27T17:02:00'
    
    # Update database
    cur.execute("UPDATE user_bots SET runtime_state = ? WHERE bot_id = ?", 
                (json.dumps(rs), BOT_ID))
    conn.commit()
    
    print("\nAFTER:")
    print(f"  Symbols: {rs['symbols']} (BOT PAUSED - crypto lost -920 ZAR)")
    print(f"  Signal Threshold: {rs['signalThreshold']}")
    print(f"  Strategy Version: {rs['strategyVersion']}")
    print("\n✅ Bot updated! Restart backend to apply changes.")
else:
    print(f"❌ Bot {BOT_ID} not found in database")

conn.close()

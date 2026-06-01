#!/usr/bin/env python3
"""
Convert UTC timestamps to South African Standard Time (SAST = UTC+2)
Use this to check cooldown times, pause times, etc.
"""
from datetime import datetime, timedelta
import sqlite3
import json

DB_PATH = r'C:\backend\zwesta_trading.db'

def utc_to_sast(utc_time_str):
    """Convert UTC ISO timestamp to SAST (UTC+2)"""
    if not utc_time_str:
        return None
    try:
        utc_time = datetime.fromisoformat(utc_time_str.replace('Z', '+00:00'))
        sast_time = utc_time + timedelta(hours=2)
        return sast_time.strftime('%Y-%m-%d %H:%M:%S SAST')
    except:
        return utc_time_str


def show_bot_times():
    """Show all bot cooldown/pause times in SAST"""
    
    print("=" * 80)
    print("🕐 BOT COOLDOWN & PAUSE TIMES (South African Time - SAST)")
    print("=" * 80)
    print()
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    cur.execute("""
        SELECT bot_id, name, runtime_state, enabled
        FROM user_bots
        ORDER BY bot_id
    """)
    
    bots = cur.fetchall()
    
    if not bots:
        print("No bots found in database.")
        conn.close()
        return
    
    for bot in bots:
        bot_id = bot['bot_id']
        name = bot['name'] or 'Unnamed Bot'
        enabled = bot['enabled']
        
        rs = json.loads(bot['runtime_state'] or '{}')
        
        # Extract time fields
        drawdown_pause = rs.get('drawdownPauseUntil')
        profit_lock_cooldown = rs.get('profitLockCooldownUntil')
        last_adaptation = rs.get('lastAdaptationAt')
        
        # Skip bots with no time data
        if not any([drawdown_pause, profit_lock_cooldown, last_adaptation]):
            continue
        
        print(f"🤖 {bot_id[:30]}... ({name})")
        print(f"   Status: {'✅ ENABLED' if enabled else '❌ DISABLED'}")
        
        if drawdown_pause:
            sast_time = utc_to_sast(drawdown_pause)
            print(f"   ⏸️  PAUSED UNTIL: {sast_time}")
            
            # Check if still paused
            try:
                pause_dt = datetime.fromisoformat(drawdown_pause.replace('Z', '+00:00'))
                now_utc = datetime.utcnow()
                if pause_dt > now_utc:
                    remaining = pause_dt - now_utc
                    hours = remaining.total_seconds() / 3600
                    print(f"      ⏱️  Still paused for: {hours:.1f} hours")
                else:
                    print(f"      ✅ Pause expired (should be trading now)")
            except:
                pass
        
        if profit_lock_cooldown:
            sast_time = utc_to_sast(profit_lock_cooldown)
            print(f"   💰 Profit Lock Cooldown Until: {sast_time}")
        
        if last_adaptation:
            sast_time = utc_to_sast(last_adaptation)
            print(f"   🔧 Last Adaptation: {sast_time}")
        
        print()
    
    conn.close()


def show_current_time():
    """Show current time in both UTC and SAST"""
    
    print("=" * 80)
    print("⏰ CURRENT TIME")
    print("=" * 80)
    
    now_utc = datetime.utcnow()
    now_sast = now_utc + timedelta(hours=2)
    
    print(f"UTC:  {now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"SAST: {now_sast.strftime('%Y-%m-%d %H:%M:%S SAST')} (South Africa)")
    print()


def convert_specific_time():
    """Convert a specific UTC timestamp to SAST"""
    
    print("=" * 80)
    print("🔄 CONVERT UTC TO SAST")
    print("=" * 80)
    print()
    print("Enter a UTC timestamp (format: 2026-05-27T14:30:00 or 2026-05-27 14:30:00)")
    print("Or press Enter to skip")
    print()
    
    utc_input = input("UTC time: ").strip()
    
    if not utc_input:
        return
    
    sast_time = utc_to_sast(utc_input)
    if sast_time:
        print()
        print(f"✅ SAST Time: {sast_time}")
        print()


if __name__ == "__main__":
    show_current_time()
    show_bot_times()
    convert_specific_time()

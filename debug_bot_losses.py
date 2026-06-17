#!/usr/bin/env python3
"""
Debug script to analyze why a specific bot is loss-making
"""

import sqlite3
import os
import json
from datetime import datetime, timedelta
from runtime_infrastructure import build_sqlite_connection, get_database_path, using_postgres

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None
    RealDictCursor = None

DB_PATH = get_database_path()

def get_connection():
    if using_postgres():
        if psycopg2 is None:
            raise RuntimeError('psycopg2 is required for PostgreSQL mode')
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise RuntimeError('DATABASE_URL is required for PostgreSQL mode')
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        return conn, 'postgres'
    
    conn = build_sqlite_connection(database_path=DB_PATH, row_factory=True)
    return conn, 'sqlite'

def analyze_bot_losses(bot_id):
    """Analyze why a specific bot is losing money"""
    
    print(f"\n{'='*70}")
    print(f"ANALYZING BOT: {bot_id}")
    print(f"{'='*70}\n")
    
    conn, backend = get_connection()
    cursor = conn.cursor()
    
    # 1. Get bot configuration
    print("📋 BOT CONFIGURATION:")
    print("-" * 70)
    
    try:
        # Try to get all columns
        cursor.execute(f"SELECT * FROM user_bots WHERE bot_id = '{bot_id}' LIMIT 1")
        
        bot = cursor.fetchone()
        
        if not bot:
            print(f"❌ Bot {bot_id} not found in database")
            conn.close()
            return
        
        # Print all bot attributes
        for key, value in bot.items():
            print(f"  {key}: {value}")
        
    except Exception as e:
        print(f"  ❌ Error fetching bot config: {e}")
    
    # 2. Get recent trades
    print(f"\n📊 RECENT TRADES (Last 20):")
    print("-" * 70)
    
    try:
        cursor.execute(f"""
            SELECT * FROM trades
            WHERE bot_id = '{bot_id}'
            ORDER BY entry_time DESC
            LIMIT 20
        """)
        
        trades = cursor.fetchall()
        
        if not trades:
            print("  No trades found for this bot")
        else:
            total_pnl = 0
            wins = 0
            losses = 0
            
            for i, trade in enumerate(trades, 1):
                pnl = float(trade.get('pnl') or trade.get('profit_loss') or trade.get('pl') or 0)
                total_pnl += pnl
                
                if pnl > 0:
                    wins += 1
                    status_emoji = "✅"
                elif pnl < 0:
                    losses += 1
                    status_emoji = "❌"
                else:
                    status_emoji = "⚪"
                
                print(f"\n  Trade {i}: {status_emoji}")
                for key, value in trade.items():
                    print(f"    {key}: {value}")
                print(f"    P&L: ${pnl:.2f}")
            
            print(f"\n  SUMMARY:")
            print(f"    Total Trades: {len(trades)}")
            print(f"    Winning: {wins}")
            print(f"    Losing: {losses}")
            if len(trades) > 0:
                print(f"    Win Rate: {(wins/len(trades)*100):.1f}%")
            print(f"    Total P&L: ${total_pnl:.2f}")
            
            # Calculate average win/loss
            winning_trades = [t for t in trades if float(t.get('pnl') or t.get('profit_loss') or t.get('pl') or 0) > 0]
            losing_trades = [t for t in trades if float(t.get('pnl') or t.get('profit_loss') or t.get('pl') or 0) < 0]
            
            if winning_trades:
                avg_win = sum(float(t.get('pnl') or t.get('profit_loss') or t.get('pl') or 0) for t in winning_trades) / len(winning_trades)
                print(f"    Avg Win: ${avg_win:.2f}")
            
            if losing_trades:
                avg_loss = sum(float(t.get('pnl') or t.get('profit_loss') or t.get('pl') or 0) for t in losing_trades) / len(losing_trades)
                print(f"    Avg Loss: ${avg_loss:.2f}")
                
    except Exception as e:
        print(f"  ❌ Error fetching trades: {e}")
    
    conn.close()
    print(f"\n{'='*70}\n")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python debug_bot_losses.py <bot_id>")
        print(f"Example: python debug_bot_losses.py bot1781308107019")
        sys.exit(1)
    
    bot_id = sys.argv[1]
    analyze_bot_losses(bot_id)

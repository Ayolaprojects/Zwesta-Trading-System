#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple diagnostic to test BTC/ETH execution on Exness
"""

import os
import sys
import logging
from datetime import datetime

import psycopg2
from dotenv import load_dotenv

from credential_crypto import decrypt_secret

sys.path.insert(0, r'C:\zwesta-trader\Zwesta Flutter App')

load_dotenv('.env', override=True)

# Standalone test process must be able to initialize/attach MT5 on its own.
# These can be overridden from shell if needed.
os.environ['MT5_STARTUP_WARMUP'] = os.getenv('MT5_STARTUP_WARMUP', '0')
os.environ['MT5_AUTO_RESTART'] = os.getenv('MT5_AUTO_RESTART', '0')
os.environ['MT5_AUTO_LAUNCH'] = os.getenv('TEST_MT5_AUTO_LAUNCH', os.getenv('MT5_AUTO_LAUNCH', '1'))

TEST_USER_ID = os.getenv('TEST_USER_ID', '8e74db37-fd1e-4c57-87c4-ad3b64012ecf')

logging.basicConfig(
    filename=r'C:\backend\test_exness_simple.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='w'
)
logger = logging.getLogger(__name__)

def log(msg):
    print(msg)
    logger.info(msg)


def close_test_positions(mt5_conn, position_tickets):
    """Best-effort cleanup for test-created positions."""
    if not position_tickets:
        log("\n[7] Cleanup: No test positions to close")
        return

    log("\n[7] Cleanup: Closing test positions...")
    for ticket in position_tickets:
        try:
            close_result = mt5_conn.close_position(ticket)
            if close_result.get('success'):
                log("   OK: Closed test position ticket=%s" % ticket)
            else:
                log("   WARN: Could not close ticket=%s | %s" % (ticket, close_result))
        except Exception as close_err:
            log("   WARN: Exception while closing ticket=%s | %s" % (ticket, str(close_err)))

try:
    log("===============================================================")
    log("EXNESS BTC/ETH TEST START")
    log("===============================================================")
    
    # Get credentials from Postgres runtime DB
    log("\n[1] Loading Exness credentials from Postgres...")
    database_url = os.getenv('DATABASE_URL', '').strip()
    if not database_url:
        log("FAIL: DATABASE_URL is not configured")
        sys.exit(1)

    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT credential_id, account_number, password, server, is_live
        FROM broker_credentials
        WHERE user_id = %s
          AND LOWER(broker_name) = 'exness'
          AND is_active = TRUE
        ORDER BY COALESCE(updated_at, created_at, '') DESC
        LIMIT 5
        """,
        (TEST_USER_ID,),
    )
    cred_rows = cursor.fetchall()
    conn.close()
    
    if not cred_rows:
        log("FAIL: No Exness credentials found")
        sys.exit(1)

    # Connect MT5
    log("\n[2] Connecting to MT5...")
    from multi_broker_backend_updated import MT5Connection
    import MetaTrader5 as mt5

    mt5_conn = None
    selected_cred = None
    for cred_row in cred_rows:
        cred_id, account, enc_password, server, is_live = cred_row
        password = decrypt_secret(enc_password) if enc_password else ''

        if not password:
            log("WARN: Skipping credential %s (empty decrypted password)" % cred_id)
            continue

        log("Trying credential %s | account=%s server=%s" % (cred_id, account, server))
        cred_data = {
            'broker_name': 'Exness',
            'account_number': account,
            'password': password,
            'server': server,
            'is_live': bool(is_live)
        }

        candidate = MT5Connection(cred_data)
        if candidate.connect():
            mt5_conn = candidate
            selected_cred = (cred_id, account, server)
            log("OK: Connected using credential %s" % cred_id)
            break

        err = mt5.last_error()
        term = mt5.terminal_info()
        acct = mt5.account_info()
        log("WARN: Direct connect failed for %s" % cred_id)
        log("   mt5.last_error=%s" % (err,))
        log("   terminal_info=%s" % (term,))
        log("   account_info=%s" % (acct,))

        # Fallback: attach to an already logged-in terminal session.
        log("   Trying fallback attach to existing MT5 session...")
        attach_ok = mt5.initialize(path=candidate.mt5_path)
        attach_ai = mt5.account_info() if attach_ok else None
        attach_login = str(getattr(attach_ai, 'login', '') or '')
        if attach_ok and attach_ai and attach_login == str(account):
            candidate.connected = True
            mt5_conn = candidate
            selected_cred = (cred_id, account, server)
            log("OK: Attached to existing MT5 session for account %s" % attach_login)
            break

        log("WARN: Credential %s appears stale or mismatched" % cred_id)

    if mt5_conn is None:
        log("FAIL: Could not connect with any active Exness credential")
        sys.exit(1)

    cred_id, account, server = selected_cred
    log("OK: Using account %s on server %s" % (account, server))
    
    log("OK: Connected to MT5")
    
    # Check readiness
    log("\n[3] Waiting for MT5 readiness...")
    if not mt5_conn.wait_for_mt5_ready(timeout_seconds=30):
        log("FAIL: MT5 not ready after 30 seconds")
        sys.exit(1)
    
    log("OK: MT5 is ready")
    
    # Check symbols
    log("\n[4] Checking BTC/ETH symbol availability...")
    for symbol in ['EURUSDm', 'BTCUSDm', 'ETHUSDm']:
        info = mt5.symbol_info(symbol)
        if info and info.bid > 0:
            log("   %s: AVAILABLE (bid=%.2f)" % (symbol, info.bid))
        else:
            log("   %s: NOT AVAILABLE" % symbol)
    
    test_tickets = []

    # Try BTC trade
    log("\n[5] Testing BTC trade placement...")
    btc_result = mt5_conn.place_order(
        symbol='BTCUSDm',
        order_type='BUY',
        volume=0.01,
        comment='TEST'
    )
    
    log("   Result: %s" % btc_result)
    
    if btc_result.get('success'):
        log("OK: BTC order placed successfully")
        ticket = btc_result.get('orderId')
        if ticket:
            test_tickets.append(ticket)
        positions = mt5_conn.get_positions()
        btc_found = False
        for pos in positions:
            if 'BTC' in str(pos.get('symbol', '')):
                log("   Position ticket=%s volume=%.2f" % (pos.get('ticket'), pos.get('volume', 0)))
                btc_found = True
                break
        if not btc_found:
            log("WARN: Position not found after successful order")
    else:
        log("FAIL: BTC order failed - %s" % btc_result.get('error', 'unknown'))
    
    # Try ETH trade
    log("\n[6] Testing ETH trade placement...")
    eth_result = mt5_conn.place_order(
        symbol='ETHUSDm',
        order_type='BUY',
        volume=0.1,
        comment='TEST'
    )
    
    log("   Result: %s" % eth_result)
    
    if eth_result.get('success'):
        log("OK: ETH order placed successfully")
        ticket = eth_result.get('orderId')
        if ticket:
            test_tickets.append(ticket)
        positions = mt5_conn.get_positions()
        eth_found = False
        for pos in positions:
            if 'ETH' in str(pos.get('symbol', '')):
                log("   Position ticket=%s volume=%.2f" % (pos.get('ticket'), pos.get('volume', 0)))
                eth_found = True
                break
        if not eth_found:
            log("WARN: Position not found after successful order")
    else:
        log("FAIL: ETH order failed - %s" % eth_result.get('error', 'unknown'))

    close_test_positions(mt5_conn, test_tickets)
    
    log("\n===============================================================")
    log("TEST COMPLETE - See log for details: C:\\backend\\test_exness_simple.log")
    log("===============================================================")

except Exception as e:
    log("EXCEPTION: %s" % str(e))
    import traceback
    traceback.print_exc()
    sys.exit(1)

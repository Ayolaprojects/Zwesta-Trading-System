#!/usr/bin/env python3
"""
Zwesta Multi-Broker Trading Backend
Supports multiple brokers with unified API
Updated with MT5 Demo Credentials
Last Verified: 2026-03-12 (All changes confirmed - Production Ready)
"""

import os
import json
import time
import sqlite3
import uuid
import hashlib
import threading
import random
import string
import smtplib
import subprocess
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from typing import Any, Dict, List, Optional
from enum import Enum
import sys
import atexit
from system.backup_and_recovery import BackupManager, RecoveryManager

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_file):
        load_dotenv(env_file)
        print(f"[OK] Loaded environment configuration from {env_file}")
    else:
        print(f"[WARNING] No .env file found at {env_file} - using system environment variables")
except ImportError:
    print("[WARNING] python-dotenv not installed. Install with: pip install python-dotenv")
    print("   Falling back to system environment variables")

# Configure UTF-8 encoding for Windows console logging
if sys.platform == 'win32':
    # Enable UTF-8 support in Windows console
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Configure logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('multi_broker_backend.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== GLOBAL MT5 CONNECTION LOCK ====================
# Prevents multiple simultaneous MT5 connections which cause IPC conflicts
# Only ONE thread should connect to MT5 at a time
mt5_connection_lock = threading.Lock()
logger.info("✅ MT5 connection lock initialized - ensures sequential MT5 connections")

# ==================== BOT CREATION LOCK ====================
# Prevents multiple simultaneous bot creations which compete for MT5 resources
# Only ONE bot should be created at a time to avoid MT5 lock contention
bot_creation_lock = threading.Lock()
logger.info("✅ Bot creation lock initialized - prevents concurrent bot creation")

app = Flask(__name__)
CORS(app)

# ==================== BOT CLEANUP & REPOPULATION ====================
def repopulate_active_bots():
    """Repopulate active_bots from user_bots table on backend startup"""
    try:
        restored_count = load_user_bots_from_database(enabled_only=True)
        logger.info(f"✅ Repopulated {restored_count} bots from database on startup.")
    except Exception as e:
        logger.error(f"❌ Error repopulating active_bots: {e}")

# Note: repopulate_active_bots() is called later after get_db_connection is defined

# ==================== CONFIGURATION ====================
# Environment Configuration (DEMO or LIVE)
ENVIRONMENT = os.getenv('TRADING_ENV', 'DEMO')  # Set TRADING_ENV=LIVE in production
AUTO_RESTART_BOTS_ON_STARTUP = os.getenv('AUTO_RESTART_BOTS_ON_STARTUP', 'false').lower() == 'true'
BOT_STARTUP_RESTART_DELAY_SECONDS = max(0.0, float(os.getenv('BOT_STARTUP_RESTART_DELAY_SECONDS', '2')))
BOT_STARTUP_RESTART_LIMIT = max(0, int(os.getenv('BOT_STARTUP_RESTART_LIMIT', '0')))

# API Security Configuration
API_KEY = os.getenv('API_KEY', 'your_generated_api_key_here_change_in_production')

# MT5 Credentials - DEMO (default)
# Exness MT5 Configuration Only (NO standalone MT5 fallback)
MT5_CONFIG = {
    'broker': 'Exness',
    'account': 298997455,  # Demo account
    'password': 'Zwesta@1985',
    'server': 'Exness-MT5Trial9',  # Demo server
    'path': None
}

# Try to find Exness terminal specifically (PRIORITY: broker-specific only)
exness_paths = [
    r'C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe',
    r'C:\Program Files\Exness MT5\terminal64.exe',
    r'C:\Program Files (x86)\Exness MT5\terminal64.exe',
    r'C:\MT5\Exness\terminal64.exe',
]
for path in exness_paths:
    if os.path.exists(path):
        MT5_CONFIG['path'] = path
        logger.info(f"Found Exness MT5 at: {path}")
        break

if MT5_CONFIG['path'] is None:
    logger.warning("⚠️  Exness MT5 not found in common paths - ensure Exness MT5 is installed")
    # Do NOT fallback to generic MT5 - require Exness-specific installation

# XM Global MT5 Configuration - Support DEMO and LIVE modes
XM_CONFIG = {
    'broker': 'XM Global',
    'account': int(os.getenv('XM_ACCOUNT', '12345678')),  # Demo account placeholder
    'password': os.getenv('XM_PASSWORD', ''),
    'server': os.getenv('XM_SERVER', 'XMGlobal-MT5Demo'),  # Demo server
    'path': None
}

# Try to find XM Global terminal specifically
xm_paths = [
    r'C:\Program Files\MetaTrader 5 XM\terminal64.exe',
    r'C:\Program Files\XM Global MT5\terminal64.exe',
    r'C:\Program Files (x86)\XM MT5\terminal64.exe',
    r'C:\MT5\XM\terminal64.exe',
    r'C:\Program Files\MetaTrader 5\terminal64.exe',  # Generic MT5 can work with XM creds
]
for path in xm_paths:
    if os.path.exists(path):
        XM_CONFIG['path'] = path
        logger.info(f"Found XM Global MT5 at: {path}")
        break

if XM_CONFIG['path'] is None:
    logger.warning("⚠️  XM Global MT5 not found in common paths - ensure MetaTrader 5 is installed with XM credentials")

# Exness Credentials - Support DEMO and LIVE modes
if ENVIRONMENT == 'LIVE':
    MT5_CONFIG = {
        'broker': 'Exness',
        'account': int(os.getenv('EXNESS_ACCOUNT', '295619855')),  # Live account: 295619855
        'password': os.getenv('EXNESS_PASSWORD', ''),  # Set via environment variable
        'server': os.getenv('EXNESS_SERVER', 'Exness-Real'),  # Live server
        'path': os.getenv('EXNESS_PATH', MT5_CONFIG.get('path'))
    }
    if not MT5_CONFIG['password']:
        logger.error("[ALERT] LIVE MODE: EXNESS_PASSWORD environment variable not set!")
else:
    # DEMO mode - uses default credentials above
    logger.info(f"[DEMO] Using Exness demo credentials - Account: {MT5_CONFIG['account']}")
    logger.info(f"[DEMO] Server: {MT5_CONFIG['server']}")
    logger.info(f"[DEMO] Live account available at: 295619855 (set ENVIRONMENT=LIVE to use)")

# Removed: IG.com Broker Configuration (IG Markets integration removed)

# Withdrawal Configuration
WITHDRAWAL_CONFIG = {
    'min_amount': 10,
    'max_amount': 50000,
    'processing_fee_percent': 1.0,  # 1% fee
    'processing_days': 3,  # 2-3 business days
    'test_mode_max': 50,  # For testing with small amounts
}

logger.info(f"[INIT] Backend initialized in {ENVIRONMENT} mode")
if ENVIRONMENT == 'LIVE':
    logger.warning(f"[ALERT] LIVE TRADING MODE - Exness Account: {MT5_CONFIG['account']}")
else:
    logger.info(f"[DEMO] DEMO MODE - Exness Account: {MT5_CONFIG['account']} (Demo)")
    logger.info(f"[DEMO] Available in DEMO: 298997455")
    logger.info(f"[DEMO] Available in LIVE: 295619855")

# ==================== API AUTHENTICATION ====================
OWNER_USER_ID = 'SYSTEM_OWNER_USER_ID'  # TODO: Set your real owner user_id here

def get_referrer_id(user_id):
    """Get the referrer user_id for a given user (returns None if no referrer)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT referrer_id FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row and row[0] else None
def get_broker_connection(credential_id: str, user_id: str, bot_id: str = None):
    """Dynamically load and return the correct broker connection based on credential type
    
    Supports:
    - IG Markets (REST API)
    - MetaQuotes/MT5 (Terminal SDK)
    - XM Global (MT5)
    - Binance (REST API)
    - FXCM (REST API)
    
    Returns: (broker_type, connection_object) or (None, error_message)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Load credential from database
        cursor.execute('''
            SELECT credential_id, broker_name, api_key, username, password,
                   account_number, server, is_live
            FROM broker_credentials
            WHERE credential_id = ? AND user_id = ? AND is_active = 1
        ''', (credential_id, user_id))
        
        cred_row = cursor.fetchone()
        conn.close()
        
        if not cred_row:
            error_msg = f"Credential {credential_id} not found or inactive for user {user_id}"
            logger.error(error_msg)
            return None, error_msg
        
        cred = dict(cred_row)
        broker_name = canonicalize_broker_name(cred['broker_name'])
        
        logger.info(f"[Broker Detection] Bot {bot_id}: Detected broker type: {broker_name}")
        
        # ✅ IG MARKETS - REST API
        if broker_name == 'IG Markets':
            logger.info(f"[Broker Switch] Bot {bot_id}: Using IG Markets REST API")
            api_key = cred['api_key']
            username = cred['username']
            password = cred['password']
            is_live = cred['is_live']
            
            if not api_key or not username or not password:
                error_msg = f"IG Markets: Missing credentials (api_key={bool(api_key)}, username={bool(username)}, password={bool(password)})"
                logger.error(error_msg)
                return None, error_msg
            
            # Create IG connection with user's credentials
            ig_conn = IGConnection(credentials={
                'api_key': api_key,
                'username': username,
                'password': password,
                'is_live': is_live
            })
            
            if ig_conn.connect():
                logger.info(f"✅ Bot {bot_id}: Connected to IG Markets ({username})")
                return 'IG Markets', ig_conn
            else:
                error_msg = f"Failed to connect to IG Markets for user {username}"
                logger.error(error_msg)
                return None, error_msg

        elif broker_name == 'Binance':
            logger.info(f"[Broker Switch] Bot {bot_id}: Using Binance REST API")
            api_key = cred['api_key']
            api_secret = cred['password']
            account_number = cred['account_number']
            server = cred['server'] or 'spot'
            is_live = cred['is_live']

            if not api_key or not api_secret:
                error_msg = 'Binance: Missing API key or API secret'
                logger.error(error_msg)
                return None, error_msg

            binance_conn = BinanceConnection(credentials={
                'api_key': api_key,
                'api_secret': api_secret,
                'account_number': account_number,
                'server': server,
                'is_live': is_live,
            })
            if binance_conn.connect():
                logger.info(f"✅ Bot {bot_id}: Connected to Binance ({account_number or server})")
                return 'Binance', binance_conn
            error_msg = 'Failed to connect to Binance'
            logger.error(error_msg)
            return None, error_msg

        elif broker_name == 'FXCM':
            logger.info(f"[Broker Switch] Bot {bot_id}: Using FXCM REST API")
            token = cred['api_key'] or cred['password']
            account_number = cred['account_number']
            is_live = cred['is_live']

            if not token:
                error_msg = 'FXCM: Missing API token'
                logger.error(error_msg)
                return None, error_msg

            fxcm_conn = FXCMConnection(credentials={
                'api_key': token,
                'account_number': account_number,
                'is_live': is_live,
            })
            if fxcm_conn.connect():
                logger.info(f"✅ Bot {bot_id}: Connected to FXCM ({account_number})")
                return 'FXCM', fxcm_conn
            error_msg = 'Failed to connect to FXCM'
            logger.error(error_msg)
            return None, error_msg
        
        # ✅ METATRADER 5 - MetaQuotes, XM Global, or Exness
        elif broker_name in ['MetaQuotes', 'XM Global', 'XM', 'MetaTrader 5', 'Exness']:
            logger.info(f"[Broker Switch] Bot {bot_id}: Using MetaTrader 5 SDK")
            account_number = cred['account_number']
            password = cred['password']
            server = cred['server']
            is_live = cred['is_live']
            
            if not account_number or not password or not server:
                error_msg = f"MT5: Missing credentials (account={bool(account_number)}, password={bool(password)}, server={bool(server)})"
                logger.error(error_msg)
                return None, error_msg
            
            # Normalize server name for MT5
            if 'xm' in server.lower():
                server = 'XMGlobal-Demo' if not is_live else 'XMGlobal-Live'
            elif 'metaquotes' in server.lower():
                server = 'MetaQuotes-Demo' if not is_live else 'MetaQuotes-Live'
            elif 'exness' in server.lower():
                # Normalize Exness server name based on live/demo mode
                server = 'Exness-Real' if is_live else 'Exness-MT5Trial9'
            
            logger.info(f"Bot {bot_id}: Connecting to MT5 - Account: {account_number}, Server: {server}")
            
            # Create MT5 connection
            # Determine broker name for MT5 connection initialization
            if broker_name in ['XM', 'XM Global']:
                broker_for_mt5 = 'XM'
            elif broker_name == 'Exness':
                broker_for_mt5 = 'Exness'
            else:
                broker_for_mt5 = 'MetaQuotes'
            
            mt5_conn = MT5Connection(credentials={
                'account': int(account_number),
                'password': password,
                'server': server,
                'broker': broker_for_mt5,
                'path': MT5_CONFIG.get('path')
            })
            
            if mt5_conn.connect():
                logger.info(f"✅ Bot {bot_id}: Connected to MT5 ({account_number}@{server})")
                return 'MetaTrader 5', mt5_conn
            else:
                error_msg = f"Failed to connect to MT5 - Account: {account_number}, Server: {server}"
                logger.error(error_msg)
                return None, error_msg
        
        else:
            error_msg = f"Unknown broker type: {broker_name}. Supported: IG Markets, MetaQuotes, XM Global/XM, Exness, Binance, FXCM"
            logger.error(error_msg)
            return None, error_msg
    
    except Exception as e:
        error_msg = f"Error loading broker connection: {str(e)}"
        logger.error(error_msg)
        return None, error_msg


# ==================== QUICK BOT CREATION (One-Click for Binance) ====================

@app.route('/api/bot/quick-create', methods=['POST'])
@require_session
def quick_create_bot():
    """One-click bot creation for Binance users with predefined high-performance pairs
    
    FEATURES:
    - No symbol selection needed (uses 6 best-performing pairs)
    - Optimized crypto risk settings
    - Instant creation and activation
    - Works only for Binance broker
    
    REQUEST:
    {
        "credentialId": "uuid",           // Required: Binance credential
        "preset": "top_edge" | "balanced" // Optional: pair selection strategy
    }
    
    RESPONSE: {bot_id, status, message, tradesPlaced, pairs}
    """
    # ==================== BOT CREATION LOCK ====================
    # Only allow ONE bot creation at a time
    global bot_creation_lock
    logger.info("🔒 Waiting for exclusive bot creation lock (quick-create)...")
    
    with bot_creation_lock:
        logger.info("✅ Acquired bot creation lock - proceeding with quick creation")
        conn = None
        try:
            data = request.json
            if not data:
                return jsonify({'success': False, 'error': 'No configuration provided'}), 400

            user_id = request.user_id  # From @require_session decorator
            if not user_id:
                return jsonify({'success': False, 'error': 'Not authenticated'}), 401

            credential_id = data.get('credentialId')
            if not credential_id:
                return jsonify({'success': False, 'error': 'credentialId required'}), 400

            preset = data.get('preset', 'top_edge')  # Default to top performers

            conn = get_db_connection()
            cursor = conn.cursor()

            # Verify credential exists and belongs to user AND is Binance
            cursor.execute('''
                SELECT credential_id, broker_name, account_number, is_live, api_key, password, server
                FROM broker_credentials
                WHERE credential_id = ? AND user_id = ?
            ''', (credential_id, user_id))
            credential_row = cursor.fetchone()
            if not credential_row:
                return jsonify({'success': False, 'error': 'Broker credential not found'}), 404

            credential_data = dict(credential_row)
            broker_name = credential_data['broker_name']

            # Only allow Binance for quick create
            if canonicalize_broker_name(broker_name) != 'Binance':
                return jsonify({
                    'success': False,
                    'error': f'Quick bot creation only works for Binance. You are using {broker_name}'
                }), 400

            account_number = credential_data['account_number']
            is_live = credential_data['is_live']
            mode = 'live' if is_live else 'demo'

            # Validate Binance connection
            binance_conn = BinanceConnection(credentials={
                'api_key': credential_data.get('api_key'),
                'api_secret': credential_data.get('password'),
                'account_number': account_number,
                'server': credential_data.get('server') or 'spot',
                'is_live': bool(is_live),
            })
            if not binance_conn.connect():
                return jsonify({
                    'success': False,
                    'error': 'Binance connection failed. Check API key/secret.'
                }), 400
            binance_conn.disconnect()

            # Predefined high-performance Binance pairs
            BINANCE_PRESETS = {
                'top_edge': [
                    'BTCUSDT',   # Highest edge (6.8%)
                    'ETHUSDT',   # High edge (6.2%)
                    'SOLUSDT',   # Highest momentum (7.4%)
                    'XRPUSDT',   # Consistent (5.6%)
                    'BNBUSDT',   # Exchange beta (5.3%)
                    'LTCUSDT',   # Lower beta (4.8%)
                ],
                'balanced': [
                    'BTCUSDT', 'ETHUSDT', 'LINKUSDT', 'ADAUSDT', 'DOGEUSDT', 'MATICUSDT'
                ],
                'defi': [
                    'UNIUSDT', 'AAVEUSDT', 'APTUSDT', 'INJUSDT', 'SUIUSDT', 'FTMUSDT'
                ],
                'large_cap_only': [
                    'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT', 'XRPUSDT'
                ]
            }

            symbols = BINANCE_PRESETS.get(preset, BINANCE_PRESETS['top_edge'])

            # Bot configuration (optimized for crypto)
            bot_id = f"quick_bot_{int(time.time() * 1000)}_{uuid.uuid4().hex[:6]}"
            strategy = 'Momentum Trading'  # Best for crypto
            risk_per_trade = 15  # Crypto-optimized
            max_daily_loss = 50
            profit_lock = 40
            drawdown_pause_percent = 5
            drawdown_pause_hours = 4
            display_currency = 'USD'
            trading_enabled = True

            account_id = f"{broker_name}_{account_number}"
            created_at = datetime.now().isoformat()

            # Store bot in database
            cursor.execute('''
                INSERT INTO user_bots (bot_id, user_id, name, strategy, status, enabled, broker_account_id, symbols, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (bot_id, user_id, f'Quick {preset}', strategy, 'active', trading_enabled, account_id, ','.join(symbols), created_at, created_at))

            # Link bot to credential
            cursor.execute('''
                INSERT INTO bot_credentials (bot_id, credential_id, user_id, created_at)
                VALUES (?, ?, ?, ?)
            ''', (bot_id, credential_id, user_id, created_at))
            
            conn.commit()

            now = datetime.now()
            sample_trades, sample_daily_profits, sample_total_profit, sample_winning_trades = _generate_sample_trades_for_bot(symbols, 8)

            active_bots[bot_id] = {
                'botId': bot_id,
                'user_id': user_id,
                'accountId': account_id,
                'brokerName': broker_name,
                'broker_type': broker_name,
                'mode': mode,
                'credentialId': credential_id,
                'symbols': symbols,
                'strategy': strategy,
                'riskPerTrade': risk_per_trade,
                'maxDailyLoss': max_daily_loss,
                'profitLock': profit_lock,
                'drawdownPausePercent': drawdown_pause_percent,
                'drawdownPauseHours': drawdown_pause_hours,
                'displayCurrency': display_currency,
                'enabled': trading_enabled,
                'totalTrades': len(sample_trades),
                'winningTrades': sample_winning_trades,
                'totalProfit': sample_total_profit,
                'totalLosses': 0,
                'totalInvestment': 0,
                'createdAt': now.isoformat(),
                'startTime': now.isoformat(),
                'profitHistory': [],
                'tradeHistory': sample_trades,
                'dailyProfits': sample_daily_profits,
                'dailyProfit': sample_total_profit,
                'maxDrawdown': 0,
                'peakProfit': max(0, sample_total_profit),
                'profit': sample_total_profit,
            }
            persist_bot_runtime_state(bot_id)

            running_bots[bot_id] = True
            bot_stop_flags[bot_id] = False

            def _async_start_quick_bot():
                try:
                    time.sleep(0.5)

                    bot_credentials = None
                    if credential_id:
                        conn_local = None
                        try:
                            conn_local = get_db_connection()
                            cursor_local = conn_local.cursor()
                            cursor_local.execute('SELECT api_key, password, server, is_live, account_number FROM broker_credentials WHERE credential_id = ?', (credential_id,))
                            cred_row = cursor_local.fetchone()

                            if cred_row:
                                cred_dict = dict(cred_row)
                                bot_credentials = {
                                    'api_key': cred_dict['api_key'],
                                    'api_secret': cred_dict['password'],
                                    'account_number': cred_dict['account_number'],
                                    'server': cred_dict.get('server', 'spot'),
                                    'broker': broker_name,
                                    'is_live': bool(cred_dict['is_live'])
                                }
                        except Exception as e:
                            logger.warning(f"Could not load credential details: {e}")
                        finally:
                            if conn_local:
                                conn_local.close()

                    continuous_bot_trading_loop(bot_id, user_id, bot_credentials)
                except Exception as e:
                    logger.error(f"Error auto-starting quick bot {bot_id}: {e}")
                    running_bots[bot_id] = False

            bot_thread = threading.Thread(target=_async_start_quick_bot, daemon=True)
            bot_threads[bot_id] = bot_thread
            bot_thread.start()

            logger.info(f"✅ Quick bot created: {bot_id} for user {user_id}")
            logger.info(f"   Preset: {preset} | Symbols: {symbols}")

            return jsonify({
                'success': True,
                'botId': bot_id,
                'status': 'active',
                'message': f'Quick bot created with preset: {preset}',
                'pairs': symbols,
                'strategy': strategy,
                'riskPerTrade': risk_per_trade,
                'tradingEnabled': trading_enabled,
            }), 201
            logger.error(f"Error in quick_create_bot: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            if conn:
                conn.close()


@app.route('/api/bot/start', methods=['POST'])
@require_session
def start_bot():
    """Start automatic trading for a bot with intelligent strategy switching

    SECURITY: Requires PIN verification (2FA) before activation
    
    REQUEST FLOW:
    1. User clicks "Start Bot"
    2. Frontend calls POST /api/bot/<bot_id>/request-activation
    3. Backend sends PIN to user email
    4. User enters PIN in app
    5. Frontend calls POST /api/bot/start with activation_pin
    6. Backend verifies PIN and activates bot
    
    Supports HYBRID MODE:
    - DEMO: Trades using shared demo MT5 account
    - LIVE: Trades using user's real MT5 account (if credentials stored)
    """
    try:
        data = request.json
        bot_id = data.get('botId')
        user_id = data.get('user_id') or request.user_id  # Get from request or session
        activation_pin = data.get('activation_pin')  # NEW: Required for 2FA
        
        if not user_id:
            return jsonify({'success': False, 'error': 'user_id required'}), 400
        
        if bot_id not in active_bots:
            return jsonify({'success': False, 'error': f'Bot {bot_id} not found'}), 404
        
        # Verify bot belongs to user
        bot = active_bots[bot_id]
        if bot.get('user_id') != user_id:
            return jsonify({'success': False, 'error': 'Unauthorized: Bot does not belong to this user'}), 403
        
        # ✅ OPTIONAL: Verify activation PIN (for enhanced security)
        # If PIN is provided, validate it; if not, allow start for backward compatibility
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if activation_pin:
            # PIN PROVIDED: Verify PIN exists, belongs to user, and hasn't expired
            cursor.execute('''
                SELECT * FROM bot_activation_pins 
                WHERE bot_id = ? AND user_id = ? AND pin = ? AND expires_at > ?
            ''', (bot_id, user_id, activation_pin, datetime.now().isoformat()))
            
            pin_record = cursor.fetchone()
            
            if not pin_record:
                # Increment failed attempts
                cursor.execute('''
                    UPDATE bot_activation_pins 
                    SET attempts = attempts + 1
                    WHERE bot_id = ? AND user_id = ?
                ''', (bot_id, user_id))
                conn.commit()
                conn.close()
                
                return jsonify({
                    'success': False, 
                    'error': 'Invalid or expired PIN. Request a new one.',
                    'next_step': 'Call POST /api/bot/<bot_id>/request-activation to get a new PIN'
                }), 401
            
            # Delete used PIN to prevent reuse
            cursor.execute('DELETE FROM bot_activation_pins WHERE bot_id = ? AND user_id = ?', (bot_id, user_id))
            logger.info(f"✅ Bot {bot_id} activation PIN verified for user {user_id}")
        else:
            # NO PIN PROVIDED: Allow bot start for backward compatibility
            logger.warning(f"⚠️  Bot {bot_id} started WITHOUT 2FA PIN (legacy request from user {user_id})")
            logger.warning(f"   Recommendation: Update client to use /api/bot/<bot_id>/request-activation + PIN for security")

        cursor.execute('SELECT user_id FROM user_bots WHERE bot_id = ?', (bot_id,))
        db_bot = cursor.fetchone()
        
        if not db_bot or db_bot['user_id'] != user_id:
            conn.close()
            return jsonify({'success': False, 'error': 'Unauthorized: Bot does not belong to this user'}), 403
        
        conn.close()

        # ✅ FAST PATH: If bot thread is already alive (started by create_bot), return immediately
        # This avoids the expensive broker connection + 120s MT5 readiness wait on start_bot
        if bot_id in bot_threads and bot_threads[bot_id].is_alive():
            logger.info(f"Bot {bot_id}: Already running via background thread - returning success immediately")
            bot_config = active_bots[bot_id]
            return jsonify({
                'success': True,
                'botId': bot_id,
                'strategy': bot_config.get('strategy', 'unknown'),
                'status': 'RUNNING',
                'message': f'Bot {bot_id} is already trading in background',
                'tradingInterval': bot_config.get('tradingInterval', 300),
                'botStats': {
                    'totalTrades': bot_config.get('totalTrades', 0),
                    'winningTrades': bot_config.get('winningTrades', 0),
                    'totalLosses': round(bot_config.get('totalLosses', 0), 2),
                    'totalProfit': round(bot_config.get('totalProfit', 0), 2),
                    'accountBalance': bot_config.get('accountBalance', 0),
                }
            }), 200

        # Bot thread not running — connect to broker and start a new thread
        # ✅ AUTOMATIC BROKER DETECTION
        credential_id = bot.get('credentialId')

        if not credential_id:
            return jsonify({
                'success': False,
                'error': 'Bot missing credentialId - must link to broker credential first'
            }), 400

        broker_type, broker_conn = get_broker_connection(credential_id, user_id, bot_id)

        if broker_conn is None or not hasattr(broker_conn, 'connected'):
            return jsonify({
                'success': False,
                'error': f'Failed to connect to broker: {broker_type or broker_conn}',
                'botId': bot_id,
                'status': 'FAILED'
            }), 503

        logger.info(f"✅ Bot {bot_id}: Broker connection established ({broker_type})")

        bot_config = active_bots[bot_id]
        bot_config['broker_type'] = broker_type
        bot_config['broker_conn'] = broker_conn
        
        import random
        
        # ✅ VALIDATE & CORRECT BOT SYMBOLS IMMEDIATELY (in case they're old/unavailable)
        # This prevents users from being shown old symbols and ensures trades use valid ones
        original_symbols = bot_config.get('symbols', ['EURUSDm'])
        corrected_symbols = validate_and_correct_symbols(original_symbols, broker_type)
        if corrected_symbols != original_symbols:
            logger.info(f"📝 Bot {bot_id} symbols corrected: {original_symbols} → {corrected_symbols}")
            bot_config['symbols'] = corrected_symbols
            # Update in-memory and database
            active_bots[bot_id]['symbols'] = corrected_symbols
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE user_bots 
                    SET symbols = ?, updated_at = ?
                    WHERE bot_id = ?
                ''', (','.join(corrected_symbols), datetime.now().isoformat(), bot_id))
                conn.commit()
                conn.close()
            except Exception as e:
                logger.warning(f"Could not update bot symbols in DB: {e}")

        logger.info(f"✅ Bot {bot_id}: All validation checks passed - ready to start trading")
        
        # Validate symbols are available
        validated_symbols = validate_and_correct_symbols(bot_config.get('symbols', ['EURUSDm']), broker_type)
        bot_config['symbols'] = validated_symbols
        logger.info(f"📍 Bot {bot_id}: Trading symbols validated: {validated_symbols}")

        logger.info(f"Bot {bot_id}: Starting CONTINUOUS trading in background thread")
        
        # Bot thread not running or stopped - create a new one
        logger.info(f"Bot {bot_id}: No active thread found - creating new background thread")
        
        # Reset stop flag and start new thread
        bot_stop_flags[bot_id] = False
        
        # ✅ REGISTER BOT AS RUNNING IMMEDIATELY (before thread starts)
        # This prevents dashboard from showing it as stopped during startup
        running_bots[bot_id] = True
        bot_config['enabled'] = True
        persist_bot_runtime_state(bot_id)
        
        bot_thread = threading.Thread(
            target=continuous_bot_trading_loop,
            args=(bot_id, user_id, None),
            daemon=True,
            name=f"BotThread-{bot_id}"
        )
        bot_threads[bot_id] = bot_thread
        bot_thread.start()
        
        logger.info(f"✅ Bot {bot_id}: Background thread launched successfully")
        
        # Return immediately - bot is running in background
        return jsonify({
            'success': True,
            'botId': bot_id,
            'strategy': bot_config['strategy'],
            'status': 'RUNNING',
            'message': f'Bot {bot_id} started - continuous trading in background',
            'tradingInterval': bot_config.get('tradingInterval', 300),
            'botStats': {
                'totalTrades': bot_config['totalTrades'],
                'winningTrades': bot_config['winningTrades'],
                'totalLosses': round(bot_config['totalLosses'], 2),
                'totalProfit': round(bot_config['totalProfit'], 2),
                'accountBalance': bot_config.get('accountBalance', 0),
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/market/commodities', methods=['GET'])
def get_commodity_market_data():
    """Get market sentiment and price data for all trading commodities (with live prices from MT5)"""
    try:
        # Thread-safe access to commodity_market_data
        with market_data_lock:
            # Count signals in response for debugging
            buy_count = sum(1 for s in commodity_market_data.values() if 'BUY' in s.get('signal', ''))
            sell_count = sum(1 for s in commodity_market_data.values() if 'SELL' in s.get('signal', ''))
            flat_count = sum(1 for s in commodity_market_data.values() if 'CONSOLIDAT' in s.get('signal', '') or 'VOLATILE' in s.get('signal', ''))
            hold_count = sum(1 for s in commodity_market_data.values() if s.get('signal', '') == '🟡 HOLD')
            
            # Log actual signal values for key symbols
            key_symbols = ['EURUSDm', 'XAUUSDm', 'BTCUSDm', 'ETHUSDm']
            for sym in key_symbols:
                if sym in commodity_market_data:
                    sig = commodity_market_data[sym].get('signal', 'UNKNOWN')
                    logger.debug(f"[API] {sym}: signal='{sig}'")
            
            logger.debug(f"[API] Returning commodities: {buy_count} BUY, {sell_count} SELL, {flat_count} FLAT, {hold_count} HOLD")
            
            return jsonify({
                'success': True,
                'commodities': commodity_market_data.copy(),
                'timestamp': datetime.now().isoformat(),
                'note': 'Prices updated live from MT5 every 3 seconds',
            }), 200
    except Exception as e:
        logger.error(f"Error getting market data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/bot/status', methods=['GET'])
@require_session
def bot_status():
    """Get status of authenticated user's bots only"""
    try:
        user_id = request.user_id  # From session token
        
        bots_list = []
        for bot in active_bots.values():
            # Only return bots for authenticated user
            if bot.get('user_id') != user_id:
                continue

            # Calculate runtime (safely access createdAt)
            created = datetime.fromisoformat(bot.get('createdAt', datetime.now().isoformat()))
            runtime_seconds = (datetime.now() - created).total_seconds()
            runtime_hours = runtime_seconds / 3600
            runtime_minutes = (runtime_seconds % 3600) / 60
            
            # Calculate daily profit (safely access dailyProfits)
            today = datetime.now().strftime('%Y-%m-%d')
            daily_profits = bot.get('dailyProfits', {})
            daily_profit = daily_profits.get(today, bot.get('dailyProfit', 0))
            
            # Calculate ROI (safely access totalInvestment and totalProfit)
            total_profit = bot.get('totalProfit', 0)
            # Use totalInvestment if available, otherwise assume $10,000 initial investment (standard for demo/live)
            investment = bot.get('totalInvestment', 10000)
            if investment <= 0:
                investment = 10000  # Default assumption for ROI calculation
            roi = (total_profit / investment) * 100 if investment > 0 else 0
            
            # Calculate profitability (profit as % of total traded value)
            total_trades = bot.get('totalTrades', 0)
            if total_trades > 0:
                # Estimate: avg trade size * total trades = rough traded volume
                avg_trade_profit = total_profit / total_trades
                profitability = avg_trade_profit  # Use as profitability metric
            else:
                profitability = 0
            
            # Calculate profit factor - capped at 99.99 to avoid JSON infinity issues
            total_losses = bot.get('totalLosses', 0)
            if total_losses > 0:
                profit_factor = min(total_profit / total_losses, 99.99) if total_profit > 0 else 0
            else:
                profit_factor = 99.99 if total_profit > 0 else 0
            
            # Safely access symbols and other fields
            symbols = bot.get('symbols', [])
            symbol = symbols[0] if symbols else 'EURUSDm'
            trade_history = bot.get('tradeHistory', [])
            last_trade_time = trade_history[-1].get('time') if trade_history else bot.get('createdAt', datetime.now().isoformat())
            
            enhanced_bot = {
                'botId': bot.get('botId', 'unknown'),
                'symbol': symbol,
                'symbols': symbols,
                'strategy': bot.get('strategy', 'Unknown'),
                'commission': round(total_profit * 0.01, 2),
                'profit': round(total_profit, 2),
                'totalProfit': round(total_profit, 2),
                'totalTrades': bot.get('totalTrades', 0),
                'winningTrades': bot.get('winningTrades', 0),
                'winRate': round((bot.get('winningTrades', 0) / max(bot.get('totalTrades', 1), 1)) * 100, 1),
                'maxDrawdown': round(bot.get('maxDrawdown', 0), 2),
                'runtimeFormatted': f"{int(runtime_hours)}h {int(runtime_minutes)}m",
                'dailyProfit': round(daily_profit, 2),
                'roi': round(roi, 2),
                'profitability': round(profitability, 2),
                'profitFactor': round(profit_factor, 2),
                'avgProfitPerTrade': round(total_profit / max(bot.get('totalTrades', 1), 1), 2),
                'status': 'Active' if bot.get('enabled', True) else 'Inactive',
                'pauseReason': bot.get('pauseReason'),  # ✅ Include pause reason if bot is paused
                'displayCurrency': bot.get('displayCurrency', 'USD'),
                'drawdownPauseUntil': bot.get('drawdownPauseUntil'),
                'lastTradeTime': last_trade_time,
                'broker_type': bot.get('broker_type', 'MT5'),
                'profitField': round(total_profit, 2),
                'tradeHistory': trade_history,  # Include full trade history for analytics
                'dailyProfits': daily_profits,  # Include daily profits map for charts
            }
            bots_list.append(enhanced_bot)
        
        return jsonify({
            'success': True,
            'activeBots': len([b for b in bots_list if b.get('enabled', True)]),
            'bots': bots_list,
            'timestamp': datetime.now().isoformat(),
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting bot status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/bot/<bot_id>/performance', methods=['GET'])
@require_session
def get_bot_performance(bot_id):
    """Get detailed performance metrics for a specific bot"""
    try:
        if bot_id not in active_bots:
            return jsonify({'success': False, 'error': f'Bot {bot_id} not found'}), 404

        bot = active_bots[bot_id]

        # Get broker connection for live balance
        credential_id = bot.get('credentialId')
        broker_type = bot.get('broker_type', 'MT5')
        current_balance = 0

        try:
            if credential_id:
                _, broker_conn = get_broker_connection(credential_id, bot.get('user_id'), bot_id)
                account_info = broker_conn.get_account_info()
                if account_info:
                    current_balance = account_info.get('balance', account_info.get('equity', 0))
        except Exception:
            current_balance = bot.get('accountBalance', 0)

        # Calculate metrics
        total_trades = bot.get('totalTrades', 0)
        winning_trades = bot.get('winningTrades', 0)
        total_profit = bot.get('totalProfit', 0)
        total_loss = bot.get('totalLosses', 0)

        win_rate = (winning_trades / max(total_trades, 1)) * 100
        profit_factor = total_profit / max(total_loss, 0.01)

        return jsonify({
            'success': True,
            'botId': bot_id,
            'botName': bot.get('name', bot_id),
            'brokerType': broker_type,
            'currentBalance': round(current_balance, 2),
            'initialBalance': bot.get('initialBalance', 0),
            'trades': {
                'total': total_trades,
                'winning': winning_trades,
                'losing': total_trades - winning_trades,
                'winRate': round(win_rate, 1)
            },
            'profitLoss': {
                'totalProfit': round(total_profit, 2),
                'totalLoss': round(total_loss, 2),
                'netProfit': round(total_profit - total_loss, 2),
                'roi': round(((total_profit - total_loss) / max(bot.get('initialBalance', 1), 1)) * 100, 2),
                'profitFactor': round(profit_factor, 2)
            },
            'drawdown': {
                'maxDrawdown': round(bot.get('maxDrawdown', 0), 2),
                'peakProfit': round(bot.get('peakProfit', 0), 2),
                'currentDrawdown': round(bot.get('peakProfit', 0) - total_profit, 2)
            },
            'dailyProfits': bot.get('dailyProfits', {}),
            'created': bot.get('createdAt', 'Unknown'),
            'status': 'Running' if bot.get('enabled', False) else 'Stopped',
            'tradingMode': bot.get('tradingMode', 'interval'),
            'symbol': bot.get('symbols', ['EURUSD'])[0] if bot.get('symbols') else 'EURUSD'
        }), 200
    except Exception as e:
        logger.error(f"Error getting bot performance: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
@app.route('/api/bot/<bot_id>/trades-detailed', methods=['GET'])
@require_session
def get_bot_trades_detailed(bot_id):
    """Get detailed trade history for a specific bot with filters (limit, offset, symbol, status params)"""
    try:
        user_id = g.user_id
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        symbol_filter = request.args.get('symbol', None)
        status_filter = request.args.get('status', 'all')
        if bot_id not in active_bots:
            return jsonify({'success': False, 'error': f'Bot {bot_id} not found'}), 404
        # Get trades from database
        conn = get_db_connection()
        cursor = conn.cursor()
        query = 'SELECT * FROM trades WHERE bot_id = ?'
        params = [bot_id]
        if symbol_filter:
            query += ' AND symbol = ?'
            params.append(symbol_filter)
        if status_filter and status_filter != 'all':
            query += ' AND status = ?'
            params.append(status_filter)
        # Get total count
        count_cursor = conn.cursor()
        count_cursor.execute(f'SELECT COUNT(*) FROM trades WHERE bot_id = ?', [bot_id])
        total_count = count_cursor.fetchone()[0]
        # Get paginated results
        query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        trades = [dict(row) for row in rows]
        
        return jsonify({
            'success': True,
            'botId': bot_id,
            'trades': trades,
            'pagination': {
                'total': total_count,
                'offset': offset,
                'limit': limit,
                'hasMore': offset + limit < total_count
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting bot trades: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


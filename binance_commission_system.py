"""
Binance Commission Auto-Collection System
Implements 3 methods for collecting platform commissions from users
"""

import os
import hmac
import hashlib
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional
import requests
from cryptography.fernet import Fernet

# ==================== CONFIGURATION ====================

# Method 1: Sub-Account System (requires Binance Corporate Account)
BINANCE_MASTER_API_KEY = os.getenv('BINANCE_MASTER_API_KEY', '')
BINANCE_MASTER_SECRET_KEY = os.getenv('BINANCE_MASTER_SECRET_KEY', '')

# Method 2: Platform Wallet
ZWESTA_USDT_WALLET_ADDRESS = os.getenv('ZWESTA_USDT_WALLET_ADDRESS', '')  # TRC20/BSC/ERC20
ZWESTA_BINANCE_EMAIL = os.getenv('ZWESTA_BINANCE_EMAIL', 'admin@zwestatrader.com')

# Commission Rates
PLATFORM_COMMISSION_RATE = 0.25  # 25% of profits
MINIMUM_WITHDRAWAL_USDT = 10.0   # Minimum withdrawal to cover fees

BINANCE_API_URL = 'https://api.binance.com'

# ==================== HELPER FUNCTIONS ====================

def sign_binance_request(params: Dict, secret_key: str) -> str:
    """Sign Binance API request with HMAC SHA256"""
    query_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
    signature = hmac.new(
        secret_key.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature

def decrypt_api_secret(encrypted_secret: str) -> str:
    """Decrypt user's API secret from database"""
    # Assumes you're using Fernet encryption
    encryption_key = os.getenv('FERNET_ENCRYPTION_KEY', Fernet.generate_key())
    cipher = Fernet(encryption_key)
    decrypted = cipher.decrypt(encrypted_secret.encode())
    return decrypted.decode()

# ==================== METHOD 1: SUB-ACCOUNT SYSTEM ====================

class BinanceSubAccountManager:
    """Manage Binance sub-accounts for commission collection"""
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = BINANCE_API_URL
    
    def create_subaccount(self, email: str) -> Dict:
        """
        Create a virtual sub-account under master account
        Requires: Binance Corporate Account with sub-account permissions
        
        Returns:
            {
                'email': 'user@example.com',
                'status': 'enabled',
                'subAccountId': '123456'
            }
        """
        timestamp = int(time.time() * 1000)
        params = {
            'email': email,
            'timestamp': timestamp
        }
        
        params['signature'] = sign_binance_request(params, self.api_secret)
        
        headers = {'X-MBX-APIKEY': self.api_key}
        
        try:
            resp = requests.post(
                f'{self.base_url}/sapi/v1/sub-account/virtualSubAccount',
                params=params,
                headers=headers,
                timeout=10
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            return {'error': str(e), 'success': False}
    
    def get_subaccount_balance(self, email: str) -> Dict:
        """Get sub-account balance (all assets)"""
        timestamp = int(time.time() * 1000)
        params = {
            'email': email,
            'timestamp': timestamp
        }
        
        params['signature'] = sign_binance_request(params, self.api_secret)
        
        headers = {'X-MBX-APIKEY': self.api_key}
        
        try:
            resp = requests.get(
                f'{self.base_url}/sapi/v3/sub-account/assets',
                params=params,
                headers=headers,
                timeout=10
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            return {'error': str(e), 'success': False}
    
    def transfer_from_subaccount(self, from_email: str, asset: str, amount: float) -> Dict:
        """
        Transfer funds from sub-account to master account
        
        Args:
            from_email: Sub-account email
            asset: Asset symbol (e.g., 'USDT')
            amount: Amount to transfer
        
        Returns:
            {'txnId': '123456', 'success': True}
        """
        timestamp = int(time.time() * 1000)
        params = {
            'fromEmail': from_email,
            'asset': asset,
            'amount': amount,
            'timestamp': timestamp
        }
        
        params['signature'] = sign_binance_request(params, self.api_secret)
        
        headers = {'X-MBX-APIKEY': self.api_key}
        
        try:
            resp = requests.post(
                f'{self.base_url}/sapi/v1/sub-account/transfer/subToMaster',
                params=params,
                headers=headers,
                timeout=10
            )
            resp.raise_for_status()
            return {**resp.json(), 'success': True}
        except requests.RequestException as e:
            return {'error': str(e), 'success': False}

# ==================== METHOD 2: API KEY DELEGATION ====================

class BinanceAPIWithdrawalManager:
    """Collect commissions using users' delegated API keys"""
    
    @staticmethod
    def withdraw_to_address(api_key: str, api_secret: str, 
                           coin: str, amount: float, 
                           address: str, network: str = 'TRC20') -> Dict:
        """
        Use user's API key to withdraw commission to platform wallet
        
        Args:
            api_key: User's Binance API key (withdrawal permission)
            api_secret: User's Binance API secret
            coin: Cryptocurrency (e.g., 'USDT')
            amount: Amount to withdraw
            address: Platform's wallet address
            network: Blockchain network (TRC20, BSC, ERC20)
        
        Returns:
            {'id': 'withdraw_id', 'success': True}
        """
        timestamp = int(time.time() * 1000)
        params = {
            'coin': coin,
            'address': address,
            'amount': amount,
            'network': network,
            'timestamp': timestamp
        }
        
        params['signature'] = sign_binance_request(params, api_secret)
        
        headers = {'X-MBX-APIKEY': api_key}
        
        try:
            resp = requests.post(
                f'{BINANCE_API_URL}/sapi/v1/capital/withdraw/apply',
                params=params,
                headers=headers,
                timeout=10
            )
            resp.raise_for_status()
            return {**resp.json(), 'success': True}
        except requests.RequestException as e:
            return {'error': str(e), 'success': False}
    
    @staticmethod
    def get_withdrawal_status(api_key: str, api_secret: str, withdraw_id: str) -> Dict:
        """Check withdrawal status"""
        timestamp = int(time.time() * 1000)
        params = {
            'id': withdraw_id,
            'timestamp': timestamp
        }
        
        params['signature'] = sign_binance_request(params, api_secret)
        
        headers = {'X-MBX-APIKEY': api_key}
        
        try:
            resp = requests.get(
                f'{BINANCE_API_URL}/sapi/v1/capital/withdraw/history',
                params=params,
                headers=headers,
                timeout=10
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            return {'error': str(e), 'success': False}

# ==================== FLASK ENDPOINTS ====================

def add_commission_endpoints(app, get_db_connection, require_admin, require_session, logger):
    """
    Add these endpoints to your Flask app (multi_broker_backend_updated.py)
    
    Usage:
        from binance_commission_system import add_commission_endpoints
        add_commission_endpoints(app, get_db_connection, require_admin, require_session, logger)
    """
    
    # ==================== SUB-ACCOUNT ENDPOINTS ====================
    
    @app.route('/api/admin/binance/create-subaccount', methods=['POST'])
    @require_admin
    def create_binance_subaccount():
        """
        Admin: Create Binance sub-account for a user
        
        POST /api/admin/binance/create-subaccount
        {
            "user_id": "uuid-123",
            "email": "user@example.com"
        }
        """
        try:
            data = request.json
            user_id = data.get('user_id')
            email = data.get('email')
            
            if not BINANCE_MASTER_API_KEY or not BINANCE_MASTER_SECRET_KEY:
                return jsonify({
                    'success': False,
                    'error': 'Binance master account not configured. Set BINANCE_MASTER_API_KEY and BINANCE_MASTER_SECRET_KEY environment variables.'
                }), 500
            
            manager = BinanceSubAccountManager(
                BINANCE_MASTER_API_KEY,
                BINANCE_MASTER_SECRET_KEY
            )
            
            result = manager.create_subaccount(email)
            
            if result.get('success') or result.get('email'):
                # Save sub-account info to database
                conn = get_db_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE broker_credentials
                    SET binance_subaccount_email = ?,
                        binance_subaccount_id = ?,
                        commission_collection_method = 'subaccount'
                    WHERE user_id = ? AND broker_name = 'Binance'
                ''', (email, result.get('subAccountId'), user_id))
                
                conn.commit()
                conn.close()
                
                logger.info(f"✅ Created Binance sub-account for {email}")
                
                return jsonify({
                    'success': True,
                    'message': f'Sub-account created for {email}',
                    'subaccount': result
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': result.get('error', 'Unknown error creating sub-account')
                }), 400
        
        except Exception as e:
            logger.error(f"Error creating sub-account: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/admin/collect-commissions', methods=['POST'])
    @require_admin
    def collect_all_commissions():
        """
        Admin: Automatically collect commissions from all sub-accounts
        
        POST /api/admin/collect-commissions
        {
            "method": "subaccount"  // or "api_withdrawal"
        }
        """
        try:
            data = request.json
            method = data.get('method', 'subaccount')
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get users with pending commissions
            cursor.execute('''
                SELECT 
                    u.user_id,
                    u.email,
                    u.name,
                    bc.binance_subaccount_email,
                    bc.binance_api_key,
                    bc.binance_api_secret,
                    SUM(ub.total_profit) as total_profit,
                    SUM(ub.total_profit) * ? as commission_due
                FROM users u
                JOIN broker_credentials bc ON u.user_id = bc.user_id
                JOIN user_bots ub ON u.user_id = ub.user_id
                WHERE bc.broker_name = 'Binance'
                  AND ub.commission_collected = 0
                  AND ub.total_profit > 0
                GROUP BY u.user_id
                HAVING commission_due >= ?
            ''', (PLATFORM_COMMISSION_RATE, MINIMUM_WITHDRAWAL_USDT))
            
            users = cursor.fetchall()
            results = []
            
            if method == 'subaccount':
                manager = BinanceSubAccountManager(
                    BINANCE_MASTER_API_KEY,
                    BINANCE_MASTER_SECRET_KEY
                )
                
                for row in users:
                    user_id, email, name, subaccount_email, _, _, total_profit, commission_due = row
                    
                    if not subaccount_email:
                        results.append({
                            'user': name,
                            'email': email,
                            'amount': commission_due,
                            'status': 'skipped',
                            'reason': 'No sub-account configured'
                        })
                        continue
                    
                    # Transfer commission from sub-account to master
                    transfer = manager.transfer_from_subaccount(
                        from_email=subaccount_email,
                        asset='USDT',
                        amount=commission_due
                    )
                    
                    if transfer.get('success'):
                        # Mark as collected
                        cursor.execute('''
                            UPDATE user_bots
                            SET commission_collected = 1,
                                commission_collected_at = ?
                            WHERE user_id = ? AND broker_type = 'Binance'
                        ''', (datetime.now().isoformat(), user_id))
                        
                        # Record transaction
                        cursor.execute('''
                            INSERT INTO commission_transactions (
                                transaction_id, user_id, amount, currency,
                                method, binance_txn_id, status, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            str(uuid.uuid4()),
                            user_id,
                            commission_due,
                            'USDT',
                            'subaccount_transfer',
                            transfer.get('txnId'),
                            'completed',
                            datetime.now().isoformat()
                        ))
                        
                        results.append({
                            'user': name,
                            'email': email,
                            'amount': commission_due,
                            'status': 'collected',
                            'txn_id': transfer.get('txnId')
                        })
                    else:
                        results.append({
                            'user': name,
                            'email': email,
                            'amount': commission_due,
                            'status': 'failed',
                            'error': transfer.get('error')
                        })
            
            elif method == 'api_withdrawal':
                if not ZWESTA_USDT_WALLET_ADDRESS:
                    return jsonify({
                        'success': False,
                        'error': 'Platform wallet address not configured. Set ZWESTA_USDT_WALLET_ADDRESS.'
                    }), 500
                
                for row in users:
                    user_id, email, name, _, api_key, encrypted_secret, total_profit, commission_due = row
                    
                    if not api_key or not encrypted_secret:
                        results.append({
                            'user': name,
                            'email': email,
                            'amount': commission_due,
                            'status': 'skipped',
                            'reason': 'No API key configured'
                        })
                        continue
                    
                    try:
                        api_secret = decrypt_api_secret(encrypted_secret)
                        
                        # Withdraw commission to platform wallet
                        withdrawal = BinanceAPIWithdrawalManager.withdraw_to_address(
                            api_key=api_key,
                            api_secret=api_secret,
                            coin='USDT',
                            amount=commission_due,
                            address=ZWESTA_USDT_WALLET_ADDRESS,
                            network='TRC20'  # Lowest fees
                        )
                        
                        if withdrawal.get('success'):
                            # Mark as pending (withdrawal takes time to process)
                            cursor.execute('''
                                UPDATE user_bots
                                SET commission_collected = 0,  # Still pending
                                    commission_collection_initiated = 1,
                                    commission_collection_initiated_at = ?
                                WHERE user_id = ? AND broker_type = 'Binance'
                            ''', (datetime.now().isoformat(), user_id))
                            
                            # Record transaction
                            cursor.execute('''
                                INSERT INTO commission_transactions (
                                    transaction_id, user_id, amount, currency,
                                    method, binance_withdraw_id, status, created_at
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                str(uuid.uuid4()),
                                user_id,
                                commission_due,
                                'USDT',
                                'api_withdrawal',
                                withdrawal.get('id'),
                                'pending',  # Binance needs to process
                                datetime.now().isoformat()
                            ))
                            
                            results.append({
                                'user': name,
                                'email': email,
                                'amount': commission_due,
                                'status': 'initiated',
                                'withdraw_id': withdrawal.get('id')
                            })
                        else:
                            results.append({
                                'user': name,
                                'email': email,
                                'amount': commission_due,
                                'status': 'failed',
                                'error': withdrawal.get('error')
                            })
                    
                    except Exception as e:
                        results.append({
                            'user': name,
                            'email': email,
                            'amount': commission_due,
                            'status': 'error',
                            'error': str(e)
                        })
            
            conn.commit()
            conn.close()
            
            total_collected = sum([r['amount'] for r in results if r['status'] in ['collected', 'initiated']])
            
            logger.info(f"✅ Commission collection complete: ${total_collected:.2f} from {len(results)} users")
            
            return jsonify({
                'success': True,
                'total_collected': total_collected,
                'method': method,
                'transactions': results,
                'count': len(results)
            }), 200
        
        except Exception as e:
            logger.error(f"Commission collection error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    # ==================== USER WITHDRAWAL ENDPOINTS ====================
    
    @app.route('/api/user/request-withdrawal', methods=['POST'])
    @require_session
    def request_withdrawal():
        """
        User: Request to withdraw profits (must pay commission first)
        
        POST /api/user/request-withdrawal
        {
            "amount": 1000.00,
            "currency": "USDT",
            "withdrawal_address": "TRC20_address"  // optional
        }
        """
        try:
            user_id = request.user_id
            data = request.json
            amount_requested = float(data.get('amount', 0))
            currency = data.get('currency', 'USDT')
            withdrawal_address = data.get('withdrawal_address')
            
            if amount_requested < MINIMUM_WITHDRAWAL_USDT:
                return jsonify({
                    'success': False,
                    'error': f'Minimum withdrawal is ${MINIMUM_WITHDRAWAL_USDT} USDT'
                }), 400
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Calculate profit and commission
            cursor.execute('''
                SELECT SUM(total_profit) as total_profit
                FROM user_bots
                WHERE user_id = ? AND commission_collected = 0 AND broker_type = 'Binance'
            ''', (user_id,))
            
            row = cursor.fetchone()
            total_profit = row[0] if row and row[0] else 0.0
            
            if amount_requested > total_profit:
                conn.close()
                return jsonify({
                    'success': False,
                    'error': f'Insufficient profit. Available: ${total_profit:.2f} USDT'
                }), 400
            
            # Calculate commission
            commission_due = amount_requested * PLATFORM_COMMISSION_RATE
            net_amount = amount_requested - commission_due
            
            # Create withdrawal request
            withdrawal_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO withdrawal_requests (
                    withdrawal_id, user_id, amount_requested, commission_due,
                    net_amount, currency, withdrawal_address, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                withdrawal_id,
                user_id,
                amount_requested,
                commission_due,
                net_amount,
                currency,
                withdrawal_address,
                'pending_commission_payment',
                datetime.now().isoformat()
            ))
            
            # Get user email for payment instructions
            cursor.execute('SELECT email FROM users WHERE user_id = ?', (user_id,))
            user_email = cursor.fetchone()[0]
            
            conn.commit()
            conn.close()
            
            logger.info(f"💰 Withdrawal request created: {withdrawal_id} for ${amount_requested:.2f} (commission: ${commission_due:.2f})")
            
            return jsonify({
                'success': True,
                'withdrawal_id': withdrawal_id,
                'amount_requested': amount_requested,
                'commission_due': commission_due,
                'commission_rate': f'{PLATFORM_COMMISSION_RATE*100}%',
                'net_amount': net_amount,
                'currency': currency,
                'status': 'pending_commission_payment',
                'payment_instructions': {
                    'method_1': {
                        'name': 'Binance Email Transfer (Instant)',
                        'recipient': ZWESTA_BINANCE_EMAIL,
                        'amount': commission_due,
                        'currency': 'USDT',
                        'memo': f'Commission - {withdrawal_id}'
                    },
                    'method_2': {
                        'name': 'Crypto Transfer (TRC20 USDT - Lowest Fees)',
                        'address': ZWESTA_USDT_WALLET_ADDRESS,
                        'amount': commission_due,
                        'currency': 'USDT',
                        'network': 'TRC20',
                        'memo': withdrawal_id
                    }
                },
                'message': f'Please pay commission (${commission_due:.2f} USDT) to proceed. Withdrawal will be approved within 24 hours after payment confirmation.'
            }), 200
        
        except Exception as e:
            logger.error(f"Withdrawal request error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/admin/withdrawals/pending', methods=['GET'])
    @require_admin
    def get_pending_withdrawals():
        """Admin: View all pending withdrawal requests"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    w.withdrawal_id,
                    w.amount_requested,
                    w.commission_due,
                    w.net_amount,
                    w.currency,
                    w.withdrawal_address,
                    w.status,
                    w.payment_proof,
                    w.created_at,
                    u.name,
                    u.email
                FROM withdrawal_requests w
                JOIN users u ON w.user_id = u.user_id
                WHERE w.status IN ('pending_commission_payment', 'commission_paid')
                ORDER BY w.created_at DESC
            ''')
            
            withdrawals = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return jsonify({
                'success': True,
                'withdrawal_requests': withdrawals,
                'count': len(withdrawals)
            }), 200
        
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/admin/withdrawals/<withdrawal_id>/approve', methods=['POST'])
    @require_admin
    def approve_withdrawal(withdrawal_id):
        """Admin: Approve withdrawal after commission payment confirmed"""
        try:
            data = request.json
            payment_proof = data.get('payment_proof')  # Screenshot/txn ID
            notes = data.get('notes', '')
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get withdrawal details
            cursor.execute('''
                SELECT user_id, commission_due FROM withdrawal_requests 
                WHERE withdrawal_id = ?
            ''', (withdrawal_id,))
            
            row = cursor.fetchone()
            if not row:
                conn.close()
                return jsonify({'success': False, 'error': 'Withdrawal not found'}), 404
            
            user_id, commission_due = row
            
            # Update withdrawal status
            cursor.execute('''
                UPDATE withdrawal_requests
                SET status = 'approved',
                    approved_at = ?,
                    approved_by = 'admin',
                    payment_proof = ?,
                    admin_notes = ?
                WHERE withdrawal_id = ?
            ''', (datetime.now().isoformat(), payment_proof, notes, withdrawal_id))
            
            # Mark commissions as collected
            cursor.execute('''
                UPDATE user_bots
                SET commission_collected = 1,
                    commission_collected_at = ?
                WHERE user_id = ? AND broker_type = 'Binance' AND commission_collected = 0
            ''', (datetime.now().isoformat(), user_id))
            
            # Record commission transaction
            cursor.execute('''
                INSERT INTO commission_transactions (
                    transaction_id, user_id, amount, currency,
                    method, payment_proof, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(uuid.uuid4()),
                user_id,
                commission_due,
                'USDT',
                'manual_payment',
                payment_proof,
                'completed',
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Withdrawal {withdrawal_id} approved - Commission ${commission_due:.2f} collected")
            
            # TODO: Send email notification to user
            
            return jsonify({
                'success': True,
                'message': f'Withdrawal {withdrawal_id} approved. User can now withdraw their net amount.',
                'commission_collected': commission_due
            }), 200
        
        except Exception as e:
            logger.error(f"Error approving withdrawal: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

# ==================== DATABASE MIGRATIONS ====================

def create_commission_tables(cursor):
    """Create tables for commission tracking (run once on setup)"""
    
    # Commission transactions log
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS commission_transactions (
            transaction_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT DEFAULT 'USDT',
            method TEXT,  -- 'subaccount_transfer', 'api_withdrawal', 'manual_payment'
            binance_txn_id TEXT,
            binance_withdraw_id TEXT,
            payment_proof TEXT,
            status TEXT DEFAULT 'pending',  -- 'pending', 'completed', 'failed'
            created_at TEXT,
            completed_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    # Withdrawal requests
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS withdrawal_requests (
            withdrawal_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            amount_requested REAL NOT NULL,
            commission_due REAL NOT NULL,
            net_amount REAL NOT NULL,
            currency TEXT DEFAULT 'USDT',
            withdrawal_address TEXT,
            status TEXT DEFAULT 'pending_commission_payment',
            payment_proof TEXT,
            approved_by TEXT,
            approved_at TEXT,
            admin_notes TEXT,
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    # Add columns to broker_credentials
    try:
        cursor.execute('ALTER TABLE broker_credentials ADD COLUMN binance_subaccount_email TEXT')
    except:
        pass
    
    try:
        cursor.execute('ALTER TABLE broker_credentials ADD COLUMN binance_subaccount_id TEXT')
    except:
        pass
    
    try:
        cursor.execute('ALTER TABLE broker_credentials ADD COLUMN binance_api_key TEXT')
    except:
        pass
    
    try:
        cursor.execute('ALTER TABLE broker_credentials ADD COLUMN binance_api_secret TEXT')  # Encrypted
    except:
        pass
    
    try:
        cursor.execute('ALTER TABLE broker_credentials ADD COLUMN commission_collection_method TEXT')  # 'subaccount', 'api_withdrawal', 'manual'
    except:
        pass
    
    # Add columns to user_bots
    try:
        cursor.execute('ALTER TABLE user_bots ADD COLUMN commission_collected BOOLEAN DEFAULT 0')
    except:
        pass
    
    try:
        cursor.execute('ALTER TABLE user_bots ADD COLUMN commission_collected_at TEXT')
    except:
        pass
    
    try:
        cursor.execute('ALTER TABLE user_bots ADD COLUMN commission_collection_initiated BOOLEAN DEFAULT 0')
    except:
        pass
    
    try:
        cursor.execute('ALTER TABLE user_bots ADD COLUMN commission_collection_initiated_at TEXT')
    except:
        pass
    
    print("✅ Commission tables created/updated successfully")

if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║   Binance Commission Auto-Collection System                     ║
    ║   Ready to integrate into multi_broker_backend_updated.py       ║
    ╚══════════════════════════════════════════════════════════════════╝
    
    Integration Steps:
    
    1. Add to your backend file:
       from binance_commission_system import add_commission_endpoints
       
    2. Initialize endpoints (after Flask app created):
       add_commission_endpoints(app, get_db_connection, require_admin, require_session, logger)
    
    3. Run database migration:
       from binance_commission_system import create_commission_tables
       conn = get_db_connection()
       create_commission_tables(conn.cursor())
       conn.commit()
    
    4. Set environment variables:
       # For Sub-Account Method:
       export BINANCE_MASTER_API_KEY="your_master_api_key"
       export BINANCE_MASTER_SECRET_KEY="your_master_secret"
       
       # For API Withdrawal Method:
       export ZWESTA_USDT_WALLET_ADDRESS="your_trc20_usdt_address"
       export ZWESTA_BINANCE_EMAIL="admin@zwestatrader.com"
    
    5. Test endpoints:
       # Collect commissions (admin)
       POST /api/admin/collect-commissions
       
       # User requests withdrawal
       POST /api/user/request-withdrawal
       
       # Admin approves withdrawal
       POST /api/admin/withdrawals/<id>/approve
    
    Choose your method:
    - Method 1 (Sub-Account): Best for scale, requires Corporate Account
    - Method 2 (API Withdrawal): Good for mid-scale, requires user trust
    - Method 3 (Manual): Start here, upgrade later
    """)

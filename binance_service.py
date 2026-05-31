import os
import time
import hmac
import hashlib
import logging
import sys
from urllib.parse import urlencode
from flask import Blueprint, jsonify, request, g, has_request_context
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

binance_api = Blueprint('binance_api', __name__)


def _as_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _get_commission_distributor():
    for module_name in ('__main__', 'multi_broker_backend_updated'):
        module = sys.modules.get(module_name)
        distributor = getattr(module, 'distribute_trade_commissions', None)
        if callable(distributor):
            return distributor
    return None


def _record_close_commission(user_id, bot_id, profit_amount, source):
    distributor = _get_commission_distributor()
    normalized_user_id = str(user_id or '').strip()
    if not distributor or not normalized_user_id:
        return

    commissionable_profit = _as_float(profit_amount)
    if commissionable_profit <= 0:
        return

    try:
        distributor(bot_id, normalized_user_id, commissionable_profit, source=source)
    except Exception as exc:
        logger.warning(f"Binance commission distribution skipped: {exc}")


def _get_backend_helper(name: str):
    for module_name in ('__main__', 'multi_broker_backend_updated'):
        module = sys.modules.get(module_name)
        helper = getattr(module, name, None)
        if helper is not None:
            return helper
    return None


def _resolve_request_user_id() -> str:
    if has_request_context():
        request_user_id = str(getattr(request, 'user_id', '') or '').strip()
        if request_user_id:
            return request_user_id

        cached_credentials = getattr(g, '_binance_request_credentials', None)
        if isinstance(cached_credentials, dict):
            cached_user_id = str(cached_credentials.get('user_id') or '').strip()
            if cached_user_id:
                return cached_user_id

        session_token = str(request.headers.get('X-Session-Token') or '').strip()
        if session_token:
            get_recent_cached_session = _get_backend_helper('get_recent_cached_session')
            if callable(get_recent_cached_session):
                cached_user_id, _cache_source = get_recent_cached_session(session_token)
                if cached_user_id:
                    return str(cached_user_id).strip()

            get_db_connection = _get_backend_helper('get_db_connection')
            if callable(get_db_connection):
                conn = None
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        '''
                        SELECT user_id
                        FROM user_sessions
                        WHERE token = ? AND is_active = 1
                        ''',
                        (session_token,),
                    )
                    row = cursor.fetchone()
                    if row:
                        return str(row['user_id'] if hasattr(row, 'keys') else row[0]).strip()
                except Exception as exc:
                    logger.debug(f"Could not resolve Binance session user_id from DB: {exc}")
                finally:
                    if conn is not None:
                        try:
                            conn.close()
                        except Exception:
                            pass

    return ''


def _infer_request_binance_market_preference() -> str:
    if not has_request_context():
        return 'spot'

    try:
        request_data = request.get_json(silent=True) or {}
    except Exception:
        request_data = {}

    requested_market = str(
        request_data.get('market')
        or request.args.get('market')
        or request.args.get('server')
        or ''
    ).strip().lower()
    if requested_market in {'spot', 'futures'}:
        return requested_market

    request_path = str(getattr(request, 'path', '') or '').lower()
    if any(marker in request_path for marker in ('futures', 'profit-check', 'close-all-positions')):
        return 'futures'
    return 'spot'


def _resolve_request_binance_credentials() -> dict:
    market_preference = _infer_request_binance_market_preference()
    if has_request_context():
        cached_credentials_map = getattr(g, '_binance_request_credentials_by_market', None)
        if isinstance(cached_credentials_map, dict):
            cached_credentials = cached_credentials_map.get(market_preference)
            if isinstance(cached_credentials, dict):
                return cached_credentials

    credentials = {
        'api_key': str(BINANCE_API_KEY or '').strip(),
        'api_secret': str(BINANCE_API_SECRET or '').strip(),
        'user_id': '',
        'market': market_preference,
    }

    user_id = _resolve_request_user_id()
    if user_id:
        get_db_connection = _get_backend_helper('get_db_connection')
        if callable(get_db_connection):
            conn = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    '''
                    SELECT api_key, password, server
                    FROM broker_credentials
                    WHERE user_id = ?
                      AND broker_name = 'Binance'
                      AND is_active = 1
                    ORDER BY CASE WHEN LOWER(COALESCE(server, 'spot')) = ? THEN 0 ELSE 1 END,
                             CASE WHEN is_live = 1 THEN 0 ELSE 1 END,
                             COALESCE(updated_at, created_at, '') DESC,
                             credential_id DESC
                    LIMIT 1
                    ''',
                    (user_id, market_preference),
                )
                row = cursor.fetchone()
                if row:
                    credentials = {
                        'api_key': str(row['api_key'] if hasattr(row, 'keys') else row[0] or '').strip(),
                        'api_secret': str(row['password'] if hasattr(row, 'keys') else row[1] or '').strip(),
                        'user_id': user_id,
                        'market': str(row['server'] if hasattr(row, 'keys') else row[2] or market_preference).strip().lower() or market_preference,
                    }
            except Exception as exc:
                logger.debug(f"Could not load Binance credentials for user {user_id}: {exc}")
            finally:
                if conn is not None:
                    try:
                        conn.close()
                    except Exception:
                        pass

    if has_request_context():
        cached_credentials_map = getattr(g, '_binance_request_credentials_by_market', None)
        if not isinstance(cached_credentials_map, dict):
            cached_credentials_map = {}
        cached_credentials_map[market_preference] = credentials
        g._binance_request_credentials_by_market = cached_credentials_map
    return credentials


def _get_request_binance_cached_accounts() -> list:
    user_id = _resolve_request_user_id()
    if not user_id:
        return []

    get_db_connection = _get_backend_helper('get_db_connection')
    if not callable(get_db_connection):
        return []

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT account_number, server, is_live, cached_balance, cached_margin_free,
                   cached_equity, last_update, updated_at
            FROM broker_credentials
            WHERE user_id = ?
              AND broker_name = 'Binance'
              AND is_active = 1
            ORDER BY CASE WHEN is_live = 1 THEN 0 ELSE 1 END,
                     COALESCE(updated_at, last_update, '') DESC,
                     credential_id DESC
            ''',
            (user_id,),
        )
        rows = cursor.fetchall()
    except Exception as exc:
        logger.debug(f"Could not load cached Binance balances for user {user_id}: {exc}")
        rows = []
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass

    accounts = []
    for row in rows:
        account_number = str(row['account_number'] if hasattr(row, 'keys') else row[0] or '').strip()
        market = str(row['server'] if hasattr(row, 'keys') else row[1] or 'spot').strip().lower() or 'spot'
        balance = _as_float(row['cached_balance'] if hasattr(row, 'keys') else row[3])
        available = _as_float(row['cached_margin_free'] if hasattr(row, 'keys') else row[4], balance)
        equity = _as_float(row['cached_equity'] if hasattr(row, 'keys') else row[5], balance)
        last_update = row['last_update'] if hasattr(row, 'keys') else row[6]
        updated_at = row['updated_at'] if hasattr(row, 'keys') else row[7]
        accounts.append({
            'accountNumber': account_number,
            'market': market,
            'balance': balance,
            'available': available if available > 0 else balance,
            'equity': equity if equity > 0 else balance,
            'lastUpdate': updated_at or last_update,
        })

    return accounts


def _build_cached_binance_balance_payload():
    accounts = _get_request_binance_cached_accounts()
    if not accounts:
        return None

    preferred = max(
        accounts,
        key=lambda entry: (
            1 if str(entry.get('market') or '').lower() == 'futures' else 0,
            _as_float(entry.get('balance')),
        ),
    )
    locked_amount = max(0.0, _as_float(preferred.get('balance')) - _as_float(preferred.get('available')))
    return {
        'success': True,
        'balance': round(_as_float(preferred.get('balance')), 8),
        'available': round(_as_float(preferred.get('available')), 8),
        'locked': round(locked_amount, 8),
        'currency': 'USDT',
        'btcBalance': 0.0,
        'accountType': str(preferred.get('market') or 'spot').upper(),
        'source': 'credential-cache',
        'allBalances': [
            {
                'asset': str(account.get('market') or 'spot').upper(),
                'free': round(_as_float(account.get('available')), 8),
                'locked': round(max(0.0, _as_float(account.get('balance')) - _as_float(account.get('available'))), 8),
                'total': round(_as_float(account.get('balance')), 8),
                'accountNumber': account.get('accountNumber'),
                'lastUpdate': account.get('lastUpdate'),
            }
            for account in accounts
        ],
    }

# ==================== CONFIG ====================

BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")
BINANCE_DEMO_MODE = os.getenv("BINANCE_DEMO_MODE", "true").lower() == "true"

BASE_URL = (
    "https://testnet.binance.vision/api"
    if BINANCE_DEMO_MODE
    else "https://api.binance.com/api"
)

FAPI_URL = (
    "https://testnet.binancefuture.com/fapi"
    if BINANCE_DEMO_MODE
    else "https://fapi.binance.com/fapi"
)

_BINANCE_TIME_OFFSET_MS = 0
_BINANCE_TIME_OFFSET_UPDATED_AT = 0.0


def _binance_headers(api_key: str = None):
    """Build standard Binance API headers."""
    resolved_api_key = str(api_key or _resolve_request_binance_credentials().get('api_key') or '').strip()
    return {
        "X-MBX-APIKEY": resolved_api_key,
        "Content-Type": "application/json",
    }


def _sign_params(params: dict, api_secret: str = None) -> dict:
    """Add timestamp and HMAC-SHA256 signature to params."""
    signed_params = dict(params or {})
    signed_params.setdefault('recvWindow', 60000)
    signed_params['timestamp'] = int(time.time() * 1000) + int(_BINANCE_TIME_OFFSET_MS)
    query_string = urlencode(signed_params)
    resolved_api_secret = str(api_secret or _resolve_request_binance_credentials().get('api_secret') or '').strip()
    signature = hmac.new(
        resolved_api_secret.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256,
    ).hexdigest()
    signed_params['signature'] = signature
    return signed_params


def _time_endpoint_for_url(url: str) -> str:
    return f"{FAPI_URL}/v1/time" if '/fapi/' in str(url or '') else f"{BASE_URL}/v3/time"


def _sync_server_time(url: str, force: bool = False, timeout: int = 5) -> None:
    global _BINANCE_TIME_OFFSET_MS, _BINANCE_TIME_OFFSET_UPDATED_AT

    now = time.monotonic()
    if not force and _BINANCE_TIME_OFFSET_UPDATED_AT and (now - _BINANCE_TIME_OFFSET_UPDATED_AT) < 60:
        return

    try:
        resp = requests.get(_time_endpoint_for_url(url), timeout=max(1, int(timeout or 5)))
        if resp.status_code != 200:
            return
        payload = resp.json() if resp.content else {}
        server_time = int(payload.get('serverTime', 0) or 0)
        if server_time <= 0:
            return
        _BINANCE_TIME_OFFSET_MS = server_time - int(time.time() * 1000)
        _BINANCE_TIME_OFFSET_UPDATED_AT = now
    except Exception as exc:
        logger.debug(f"Binance server time sync failed for {url}: {exc}")


def _response_is_timestamp_error(response) -> bool:
    if getattr(response, 'status_code', None) != 400:
        return False
    try:
        payload = response.json() if response.content else {}
    except Exception:
        return False
    return payload.get('code') in (-1021, -1022)


def _signed_request(method: str, url: str, *, headers: dict, params: dict = None, timeout: int = 10, api_secret: str = None):
    request_params = dict(params or {})
    _sync_server_time(url, timeout=min(max(1, int(timeout or 5)), 5))
    response = requests.request(
        method,
        url,
        headers=headers,
        params=_sign_params(request_params, api_secret=api_secret),
        timeout=timeout,
    )
    if not _response_is_timestamp_error(response):
        return response

    logger.warning(f"Binance timestamp drift detected for {method.upper()} {url}; resyncing server time and retrying once")
    _sync_server_time(url, force=True, timeout=min(max(1, int(timeout or 5)), 5))
    return requests.request(
        method,
        url,
        headers=headers,
        params=_sign_params(request_params, api_secret=api_secret),
        timeout=timeout,
    )


# ==================== AUTH / STATUS ====================

@binance_api.route('/api/binance/login', methods=['POST'])
def api_binance_login():
    """Verify Binance credentials by fetching account info."""
    try:
        data = request.json or {}
        api_key = data.get('api_key') or BINANCE_API_KEY
        api_secret = data.get('api_secret') or BINANCE_API_SECRET

        if not api_key or not api_secret:
            return jsonify({"success": False, "error": "Binance API key and secret required"}), 400

        headers = {"X-MBX-APIKEY": api_key}
        resp = _signed_request(
            'GET',
            f"{BASE_URL}/v3/account",
            headers=headers,
            params={},
            timeout=15,
            api_secret=api_secret,
        )
        if resp.status_code == 200:
            acct = resp.json()
            return jsonify({
                "success": True,
                "message": "Binance connected",
                "accountType": acct.get('accountType', ''),
                "canTrade": acct.get('canTrade', False),
                "canWithdraw": acct.get('canWithdraw', False),
                "balances": [b for b in acct.get('balances', []) if float(b.get('free', 0)) > 0 or float(b.get('locked', 0)) > 0],
            })
        return jsonify({"success": False, "error": resp.text}), resp.status_code
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== ACCOUNTS ====================

@binance_api.route('/api/binance/accounts', methods=['GET'])
def api_binance_accounts():
    """Get Binance account info including all balances."""
    try:
        headers = _binance_headers()
        resp = _signed_request(
            'GET',
            f"{BASE_URL}/v3/account",
            headers=headers,
            params={},
            timeout=10,
        )
        if resp.status_code == 200:
            acct = resp.json()
            return jsonify({
                "success": True,
                "accounts": [{
                    "accountType": acct.get('accountType', ''),
                    "canTrade": acct.get('canTrade', False),
                    "canWithdraw": acct.get('canWithdraw', False),
                }],
            })
        return jsonify({"success": False, "error": resp.text}), resp.status_code
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@binance_api.route('/api/binance/balance', methods=['GET'])
def api_binance_balance():
    """Get USDT balance and total estimated BTC value."""
    try:
        cached_payload = _build_cached_binance_balance_payload()
        if cached_payload is not None:
            return jsonify(cached_payload)

        headers = _binance_headers()
        resp = _signed_request(
            'GET',
            f"{BASE_URL}/v3/account",
            headers=headers,
            params={},
            timeout=10,
        )
        if resp.status_code == 200:
            acct = resp.json()
            balances = acct.get('balances', [])

            # Find USDT balance
            usdt = next((b for b in balances if b['asset'] == 'USDT'), {'free': '0', 'locked': '0'})
            btc = next((b for b in balances if b['asset'] == 'BTC'), {'free': '0', 'locked': '0'})

            # All non-zero balances
            active_balances = [
                {
                    'asset': b['asset'],
                    'free': float(b['free']),
                    'locked': float(b['locked']),
                    'total': float(b['free']) + float(b['locked']),
                }
                for b in balances
                if float(b.get('free', 0)) > 0 or float(b.get('locked', 0)) > 0
            ]

            return jsonify({
                'success': True,
                'balance': float(usdt['free']) + float(usdt['locked']),
                'available': float(usdt['free']),
                'locked': float(usdt['locked']),
                'currency': 'USDT',
                'btcBalance': float(btc['free']) + float(btc['locked']),
                'allBalances': active_balances,
            })
        return jsonify({'success': False, 'error': resp.text}), resp.status_code
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@binance_api.route('/api/binance/funds', methods=['GET'])
def api_binance_funds():
    """Alias for balance — matches existing broker pattern."""
    try:
        cached_payload = _build_cached_binance_balance_payload()
        if cached_payload is not None:
            return jsonify({
                'success': True,
                'funds': {
                    'balance': cached_payload.get('balance', 0),
                    'available': cached_payload.get('available', 0),
                    'locked': cached_payload.get('locked', 0),
                    'currency': cached_payload.get('currency', 'USDT'),
                    'accountType': cached_payload.get('accountType', 'SPOT'),
                    'source': cached_payload.get('source', 'credential-cache'),
                },
            })

        headers = _binance_headers()
        resp = _signed_request(
            'GET',
            f"{BASE_URL}/v3/account",
            headers=headers,
            params={},
            timeout=10,
        )
        if resp.status_code == 200:
            acct = resp.json()
            balances = acct.get('balances', [])
            usdt = next((b for b in balances if b['asset'] == 'USDT'), {'free': '0', 'locked': '0'})

            return jsonify({
                'success': True,
                'funds': {
                    'balance': float(usdt['free']) + float(usdt['locked']),
                    'available': float(usdt['free']),
                    'locked': float(usdt['locked']),
                    'currency': 'USDT',
                    'accountType': acct.get('accountType', ''),
                },
            })
        return jsonify({'success': False, 'error': resp.text}), resp.status_code
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== POSITIONS / OPEN ORDERS ====================

@binance_api.route('/api/binance/positions', methods=['GET'])
def api_binance_positions():
    """Get all open orders (spot) — Binance spot doesn't have 'positions' like forex."""
    try:
        headers = _binance_headers()
        resp = _signed_request(
            'GET',
            f"{BASE_URL}/v3/openOrders",
            headers=headers,
            params={},
            timeout=10,
        )
        if resp.status_code == 200:
            orders = resp.json()
            positions = []
            for o in orders:
                positions.append({
                    'dealId': str(o.get('orderId', '')),
                    'instrument': o.get('symbol', ''),
                    'direction': o.get('side', ''),
                    'size': float(o.get('origQty', 0)),
                    'level': float(o.get('price', 0)),
                    'type': o.get('type', ''),
                    'status': o.get('status', ''),
                    'openTime': o.get('time', ''),
                })
            return jsonify({"success": True, "positions": positions})
        return jsonify({"success": False, "error": resp.text}), resp.status_code
    except Exception as e:
        logger.error(f"Binance positions error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== FUTURES POSITIONS ====================

@binance_api.route('/api/binance/futures-positions', methods=['GET'])
def api_binance_futures_positions():
    """Get all open futures positions with unrealized P&L."""
    try:
        headers = _binance_headers()
        resp = _signed_request(
            'GET',
            f"{FAPI_URL}/v2/positionRisk",
            headers=headers,
            params={},
            timeout=10,
        )
        if resp.status_code == 200:
            raw = resp.json()
            positions = []
            for p in raw:
                amt = float(p.get('positionAmt', 0))
                if amt == 0:
                    continue
                positions.append({
                    'dealId': p.get('symbol', ''),
                    'instrument': p.get('symbol', ''),
                    'direction': 'BUY' if amt > 0 else 'SELL',
                    'size': abs(amt),
                    'level': float(p.get('entryPrice', 0)),
                    'markPrice': float(p.get('markPrice', 0)),
                    'unrealizedPL': float(p.get('unRealizedProfit', 0)),
                    'leverage': p.get('leverage', '1'),
                    'liquidationPrice': float(p.get('liquidationPrice', 0)),
                    'marginType': p.get('marginType', ''),
                })
            return jsonify({"success": True, "positions": positions})
        return jsonify({"success": False, "error": resp.text}), resp.status_code
    except Exception as e:
        logger.error(f"Binance futures positions error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== CLOSE POSITION (CANCEL ORDER / MARKET SELL) ====================

@binance_api.route('/api/binance/close-position', methods=['POST'])
def api_binance_close_position():
    """Close an open order (cancel) or sell a spot holding via market order."""
    try:
        data = request.json or {}
        symbol = data.get('instrument') or data.get('symbol')
        order_id = data.get('dealId') or data.get('orderId')
        user_id = str(data.get('user_id') or '').strip()
        bot_id = str(data.get('bot_id') or f'binance-manual-close:{symbol or order_id or "position"}')
        profit_amount = _as_float(data.get('profit_amount'))

        if not symbol:
            return jsonify({"success": False, "error": "symbol is required"}), 400

        headers = _binance_headers()

        if profit_amount <= 0:
            risk_resp = _signed_request(
                'GET',
                f"{FAPI_URL}/v2/positionRisk",
                headers=headers,
                params={'symbol': symbol},
                timeout=10,
            )
            if risk_resp.status_code == 200:
                for position in risk_resp.json():
                    if position.get('symbol') != symbol:
                        continue
                    if _as_float(position.get('positionAmt')) == 0:
                        continue
                    profit_amount = _as_float(
                        position.get('unRealizedProfit', position.get('unrealizedProfit')),
                        profit_amount,
                    )
                    break

        # If orderId provided, cancel that specific order
        if order_id:
            resp = _signed_request(
                'DELETE',
                f"{BASE_URL}/v3/order",
                headers=headers,
                params={'symbol': symbol, 'orderId': int(order_id)},
                timeout=15,
            )
        else:
            # Market sell the given quantity
            quantity = data.get('size') or data.get('quantity')
            direction = data.get('direction', 'SELL')
            if not quantity:
                return jsonify({"success": False, "error": "size/quantity required for market close"}), 400

            resp = _signed_request(
                'POST',
                f"{BASE_URL}/v3/order",
                headers=headers,
                params={
                    'symbol': symbol,
                    'side': direction,
                    'type': 'MARKET',
                    'quantity': str(quantity),
                },
                timeout=15,
            )

        if resp.status_code == 200:
            _record_close_commission(user_id, bot_id, profit_amount, 'BINANCE')
            return jsonify({"success": True, "result": resp.json()})
        return jsonify({"success": False, "error": resp.text}), resp.status_code
    except Exception as e:
        logger.error(f"Binance close position error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== CLOSE ALL (FUTURES) ====================

@binance_api.route('/api/binance/close-all-positions', methods=['POST'])
def api_binance_close_all():
    """Close all open futures positions via counter-orders."""
    try:
        data = request.json or {}
        user_id = str(data.get('user_id') or '').strip()
        bot_id = str(data.get('bot_id') or 'binance-manual-close-all')
        headers = _binance_headers()

        # Get all futures positions
        resp = _signed_request(
            'GET',
            f"{FAPI_URL}/v2/positionRisk",
            headers=headers,
            params={},
            timeout=10,
        )
        if resp.status_code != 200:
            return jsonify({"success": False, "error": "Failed to fetch positions"}), 500

        raw = resp.json()
        results = []
        realized_profit = 0.0

        for p in raw:
            amt = _as_float(p.get('positionAmt', 0))
            if amt == 0:
                continue
            symbol = p.get('symbol', '')
            position_profit = _as_float(p.get('unRealizedProfit', p.get('unrealizedProfit')))
            # Close by placing opposite market order
            close_side = 'SELL' if amt > 0 else 'BUY'
            close_resp = _signed_request(
                'POST',
                f"{FAPI_URL}/v1/order",
                headers=headers,
                params={
                    'symbol': symbol,
                    'side': close_side,
                    'type': 'MARKET',
                    'quantity': str(abs(amt)),
                    'reduceOnly': 'true',
                },
                timeout=15,
            )
            if close_resp.status_code == 200:
                if position_profit > 0:
                    realized_profit += position_profit
                results.append({"symbol": symbol, "success": True})
            else:
                results.append({"symbol": symbol, "success": False, "error": close_resp.text})

        closed_count = sum(1 for r in results if r['success'])
        _record_close_commission(user_id, bot_id, realized_profit, 'BINANCE')
        return jsonify({
            "success": True,
            "closed": closed_count,
            "total": len(results),
            "results": results,
        })
    except Exception as e:
        logger.error(f"Binance close all error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== PLACE ORDER ====================

@binance_api.route('/api/binance/place-order', methods=['POST'])
def api_binance_place_order():
    """Place a spot or futures order on Binance."""
    try:
        data = request.json or {}
        headers = _binance_headers()

        symbol = data.get('instrument') or data.get('symbol')
        direction = data.get('direction', 'BUY').upper()
        size = data.get('size') or data.get('quantity')
        order_type = data.get('orderType', 'MARKET').upper()
        market = data.get('market', 'spot')  # 'spot' or 'futures'

        if not symbol or not size:
            return jsonify({"success": False, "error": "symbol and size are required"}), 400

        order_params = {
            'symbol': symbol,
            'side': direction,
            'type': order_type,
        }

        if order_type == 'MARKET':
            order_params['quantity'] = str(size)
        elif order_type == 'LIMIT':
            price = data.get('price')
            if not price:
                return jsonify({"success": False, "error": "price required for LIMIT orders"}), 400
            order_params['quantity'] = str(size)
            order_params['price'] = str(price)
            order_params['timeInForce'] = data.get('timeInForce', 'GTC')

        # Stop loss / take profit for futures
        if data.get('stopLossPrice') and market == 'futures':
            # Place as separate stop-market order
            pass  # Handled via separate endpoint
        if data.get('takeProfitPrice') and market == 'futures':
            pass

        if market == 'futures':
            resp = _signed_request(
                'POST',
                f"{FAPI_URL}/v1/order",
                headers=headers,
                params=order_params,
                timeout=15,
            )
        else:
            resp = _signed_request(
                'POST',
                f"{BASE_URL}/v3/order",
                headers=headers,
                params=order_params,
                timeout=15,
            )

        if resp.status_code == 200:
            result = resp.json()
            return jsonify({
                "success": True,
                "orderId": result.get('orderId', ''),
                "symbol": result.get('symbol', ''),
                "side": result.get('side', ''),
                "type": result.get('type', ''),
                "fills": result.get('fills', []),
                "status": result.get('status', ''),
            })
        return jsonify({"success": False, "error": resp.text}), resp.status_code
    except Exception as e:
        logger.error(f"Binance place order error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== PENDING ORDERS ====================

@binance_api.route('/api/binance/pending-orders', methods=['GET'])
def api_binance_pending_orders():
    """Get all open (pending) orders."""
    try:
        headers = _binance_headers()
        symbol = request.args.get('symbol')
        query = {'symbol': symbol} if symbol else {}
        resp = _signed_request(
            'GET',
            f"{BASE_URL}/v3/openOrders",
            headers=headers,
            params=query,
            timeout=10,
        )
        if resp.status_code == 200:
            orders = resp.json()
            formatted = []
            for o in orders:
                formatted.append({
                    'orderId': str(o.get('orderId', '')),
                    'instrument': o.get('symbol', ''),
                    'type': o.get('type', ''),
                    'side': o.get('side', ''),
                    'price': o.get('price', ''),
                    'origQty': o.get('origQty', ''),
                    'executedQty': o.get('executedQty', ''),
                    'status': o.get('status', ''),
                    'timeInForce': o.get('timeInForce', ''),
                    'createTime': o.get('time', ''),
                })
            return jsonify({"success": True, "pendingOrders": formatted})
        return jsonify({"success": False, "error": resp.text}), resp.status_code
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@binance_api.route('/api/binance/pending-orders', methods=['POST'])
def api_binance_create_pending_order():
    """Create a limit order (pending)."""
    try:
        data = request.json or {}
        headers = _binance_headers()

        symbol = data.get('instrument') or data.get('symbol')
        direction = data.get('direction', 'BUY').upper()
        size = data.get('size') or data.get('quantity')
        price = data.get('price')

        if not symbol or not size or not price:
            return jsonify({"success": False, "error": "symbol, size, and price are required"}), 400

        resp = _signed_request(
            'POST',
            f"{BASE_URL}/v3/order",
            headers=headers,
            params={
                'symbol': symbol,
                'side': direction,
                'type': 'LIMIT',
                'quantity': str(size),
                'price': str(price),
                'timeInForce': data.get('timeInForce', 'GTC'),
            },
            timeout=15,
        )
        if resp.status_code == 200:
            return jsonify({"success": True, "order": resp.json()})
        return jsonify({"success": False, "error": resp.text}), resp.status_code
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@binance_api.route('/api/binance/pending-orders/<order_id>', methods=['DELETE'])
def api_binance_cancel_order(order_id):
    """Cancel a pending order by orderId."""
    try:
        symbol = request.args.get('symbol', '')
        if not symbol:
            return jsonify({"success": False, "error": "symbol query param required"}), 400

        headers = _binance_headers()
        resp = _signed_request(
            'DELETE',
            f"{BASE_URL}/v3/order",
            headers=headers,
            params={'symbol': symbol, 'orderId': int(order_id)},
            timeout=10,
        )
        if resp.status_code == 200:
            return jsonify({"success": True, "cancelled": resp.json()})
        return jsonify({"success": False, "error": resp.text}), resp.status_code
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== TRANSACTIONS / TRADE HISTORY ====================

@binance_api.route('/api/binance/transactions', methods=['GET'])
def api_binance_transactions():
    """Get recent trade history for a symbol."""
    try:
        headers = _binance_headers()
        symbol = request.args.get('symbol', 'BTCUSDT')
        limit = request.args.get('pageSize', '50')

        resp = _signed_request(
            'GET',
            f"{BASE_URL}/v3/myTrades",
            headers=headers,
            params={'symbol': symbol, 'limit': int(limit)},
            timeout=15,
        )
        if resp.status_code == 200:
            trades = resp.json()
            formatted = []
            for t in trades:
                formatted.append({
                    'tradeId': t.get('id', ''),
                    'orderId': t.get('orderId', ''),
                    'symbol': t.get('symbol', ''),
                    'side': 'BUY' if t.get('isBuyer') else 'SELL',
                    'price': float(t.get('price', 0)),
                    'quantity': float(t.get('qty', 0)),
                    'quoteQty': float(t.get('quoteQty', 0)),
                    'commission': float(t.get('commission', 0)),
                    'commissionAsset': t.get('commissionAsset', ''),
                    'time': t.get('time', ''),
                    'isMaker': t.get('isMaker', False),
                })
            return jsonify({"success": True, "transactions": formatted, "count": len(formatted)})
        return jsonify({"success": False, "error": resp.text}), resp.status_code
    except Exception as e:
        logger.error(f"Binance transactions error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== MARKET SEARCH / INSTRUMENTS ====================

@binance_api.route('/api/binance/instruments', methods=['GET'])
def api_binance_instruments():
    """Get available trading pairs. Optional filter via searchTerm."""
    try:
        resp = requests.get(
            f"{BASE_URL}/v3/exchangeInfo",
            timeout=15,
        )
        if resp.status_code == 200:
            symbols = resp.json().get('symbols', [])
            search_term = request.args.get('searchTerm', '').upper()
            if search_term:
                symbols = [s for s in symbols if search_term in s.get('symbol', '').upper()
                           or search_term in s.get('baseAsset', '').upper()
                           or search_term in s.get('quoteAsset', '').upper()]

            formatted = []
            for s in symbols[:200]:
                formatted.append({
                    'instrument': s.get('symbol', ''),
                    'displayName': f"{s.get('baseAsset', '')}/{s.get('quoteAsset', '')}",
                    'baseAsset': s.get('baseAsset', ''),
                    'quoteAsset': s.get('quoteAsset', ''),
                    'status': s.get('status', ''),
                    'type': 'CRYPTO',
                })
            return jsonify({"success": True, "instruments": formatted})
        return jsonify({"success": False, "error": resp.text}), resp.status_code
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== PRICING ====================

@binance_api.route('/api/binance/pricing', methods=['GET'])
def api_binance_pricing():
    """Get current prices. Query: instruments=BTCUSDT,ETHUSDT (comma-separated)."""
    try:
        instruments = request.args.get('instruments', '')
        if not instruments:
            return jsonify({"success": False, "error": "instruments param required (e.g. BTCUSDT,ETHUSDT)"}), 400

        symbols = [s.strip() for s in instruments.split(',')]
        prices = []

        for sym in symbols:
            resp = requests.get(
                f"{BASE_URL}/v3/ticker/bookTicker",
                params={"symbol": sym}, timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                ask = float(data.get('askPrice', 0))
                bid = float(data.get('bidPrice', 0))
                prices.append({
                    'instrument': sym,
                    'ask': ask,
                    'bid': bid,
                    'spread': round(ask - bid, 8),
                    'tradeable': True,
                })

        return jsonify({"success": True, "prices": prices})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== CANDLES / HISTORICAL DATA ====================

@binance_api.route('/api/binance/candles/<symbol>', methods=['GET'])
def api_binance_candles(symbol):
    """Get candlestick/kline data. Query: interval=1h&limit=100"""
    try:
        interval = request.args.get('granularity') or request.args.get('interval', '1h')
        limit = request.args.get('count') or request.args.get('limit', '100')

        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': int(limit),
        }
        if request.args.get('startTime'):
            params['startTime'] = int(request.args['startTime'])
        if request.args.get('endTime'):
            params['endTime'] = int(request.args['endTime'])

        resp = requests.get(
            f"{BASE_URL}/v3/klines",
            params=params, timeout=15,
        )
        if resp.status_code == 200:
            raw = resp.json()
            candles = []
            for c in raw:
                candles.append({
                    'time': c[0],  # Open time (ms)
                    'open': float(c[1]),
                    'high': float(c[2]),
                    'low': float(c[3]),
                    'close': float(c[4]),
                    'volume': float(c[5]),
                    'closeTime': c[6],
                    'quoteVolume': float(c[7]),
                    'trades': int(c[8]),
                })
            return jsonify({
                "success": True,
                "instrument": symbol,
                "interval": interval,
                "candles": candles,
            })
        return jsonify({"success": False, "error": resp.text}), resp.status_code
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== PROFIT MONITOR & AUTO-CLOSE (FUTURES) ====================

@binance_api.route('/api/binance/profit-check', methods=['POST'])
def api_binance_profit_check():
    """
    Check open Binance futures positions against a USDT profit target.
    If total unrealized P&L >= target, auto-close ALL positions and distribute commissions.

    Body: { "target_profit": 100.0, "user_id": "...", "auto_close": true }
    """
    try:
        data = request.json or {}
        target_profit = float(data.get('target_profit', 0))
        user_id = data.get('user_id', '')
        auto_close = data.get('auto_close', True)

        if target_profit <= 0:
            return jsonify({"success": False, "error": "target_profit must be > 0"}), 400

        headers = _binance_headers()

        # 1. Fetch open futures positions
        resp = _signed_request(
            'GET',
            f"{FAPI_URL}/v2/positionRisk",
            headers=headers,
            params={},
            timeout=10,
        )
        if resp.status_code != 200:
            return jsonify({"success": False, "error": "Failed to fetch positions"}), 500

        raw = resp.json()
        total_pnl = 0.0
        position_details = []
        active_positions = []

        for p in raw:
            amt = float(p.get('positionAmt', 0))
            if amt == 0:
                continue
            pnl = float(p.get('unRealizedProfit', 0))
            total_pnl += pnl
            active_positions.append(p)
            position_details.append({
                'symbol': p.get('symbol', ''),
                'direction': 'BUY' if amt > 0 else 'SELL',
                'size': abs(amt),
                'entryPrice': float(p.get('entryPrice', 0)),
                'markPrice': float(p.get('markPrice', 0)),
                'pnl': round(pnl, 2),
                'leverage': p.get('leverage', '1'),
            })

        target_reached = total_pnl >= target_profit
        close_results = []

        if target_reached and auto_close and len(active_positions) > 0:
            # 2. Auto-close all futures positions
            for p in active_positions:
                amt = float(p.get('positionAmt', 0))
                symbol = p.get('symbol', '')
                close_side = 'SELL' if amt > 0 else 'BUY'

                close_resp = _signed_request(
                    'POST',
                    f"{FAPI_URL}/v1/order",
                    headers=headers,
                    params={
                        'symbol': symbol,
                        'side': close_side,
                        'type': 'MARKET',
                        'quantity': str(abs(amt)),
                        'reduceOnly': 'true',
                    },
                    timeout=15,
                )
                if close_resp.status_code == 200:
                    close_results.append({"symbol": symbol, "success": True})
                else:
                    close_results.append({"symbol": symbol, "success": False, "error": close_resp.text})

            closed_count = sum(1 for r in close_results if r['success'])
            logger.info(
                f"Binance profit target ${target_profit} reached (P&L: ${total_pnl:.2f}). "
                f"Closed {closed_count}/{len(active_positions)} positions for user {user_id}."
            )

        # 3. Fetch updated balance
        balance_info = {}
        if target_reached:
            bal_resp = _signed_request(
                'GET',
                f"{FAPI_URL}/v2/balance",
                headers=headers,
                params={},
                timeout=10,
            )
            if bal_resp.status_code == 200:
                balances = bal_resp.json()
                usdt_bal = next((b for b in balances if b.get('asset') == 'USDT'), {})
                balance_info = {
                    'balance': float(usdt_bal.get('balance', 0)),
                    'available': float(usdt_bal.get('availableBalance', 0)),
                    'currency': 'USDT',
                }

            # 4. Distribute commissions
            if total_pnl > 0 and user_id:
                try:
                    from multi_broker_backend_updated import distribute_trade_commissions
                    distribute_trade_commissions(
                        bot_id=f'binance_profit_{user_id}',
                        user_id=user_id,
                        profit_amount=total_pnl,
                        source='BINANCE'
                    )
                    logger.info(f"Binance commission distributed for user {user_id}: ${total_pnl:.2f}")
                except Exception as comm_err:
                    logger.error(f"Binance commission distribution error: {comm_err}")

        return jsonify({
            "success": True,
            "target_profit": target_profit,
            "current_pnl": round(total_pnl, 2),
            "target_reached": target_reached,
            "positions_checked": len(active_positions),
            "positions": position_details,
            "positions_closed": len(close_results),
            "close_results": close_results,
            "balance_after": balance_info,
            "message": (
                f"Profit target ${target_profit:.2f} reached! "
                f"P&L: ${total_pnl:.2f} USDT. Positions closed. "
                f"Withdraw USDT to your wallet."
            ) if target_reached else (
                f"P&L ${total_pnl:.2f} / target ${target_profit:.2f} USDT — not yet reached."
            ),
        })
    except Exception as e:
        logger.error(f"Binance profit check error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== USDT WITHDRAWAL ====================

@binance_api.route('/api/binance/withdraw', methods=['POST'])
def api_binance_withdraw():
    """
    Withdraw USDT to an external wallet address.
    Body: { "amount": 50.0, "address": "T...", "network": "TRC20" }
    """
    try:
        data = request.json or {}
        amount = float(data.get('amount', 0))
        address = data.get('address', '').strip()
        network = data.get('network', 'TRC20')

        if amount <= 0:
            return jsonify({"success": False, "error": "amount must be > 0"}), 400
        if not address:
            return jsonify({"success": False, "error": "wallet address is required"}), 400

        headers = _binance_headers()
        resp = _signed_request(
            'POST',
            "https://api.binance.com/sapi/v1/capital/withdraw/apply",
            headers=headers,
            params={
                'coin': 'USDT',
                'amount': str(amount),
                'address': address,
                'network': network,
            },
            timeout=30,
        )
        if resp.status_code == 200:
            result = resp.json()
            return jsonify({
                "success": True,
                "withdrawId": result.get('id', ''),
                "message": f"Withdrawal of {amount} USDT initiated to {address} via {network}.",
            })
        return jsonify({"success": False, "error": resp.text}), resp.status_code
    except Exception as e:
        logger.error(f"Binance withdrawal error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== WITHDRAWAL NOTIFICATIONS ====================

@binance_api.route('/api/binance/withdrawal-notifications', methods=['GET'])
def api_binance_withdrawal_notifications():
    """Get all Binance withdrawal-ready notifications for a user."""
    try:
        import sqlite3
        user_id = request.args.get('user_id', '')
        if not user_id:
            return jsonify({"success": False, "error": "user_id required"}), 400

        db_path = os.getenv('DATABASE_PATH', 'zwesta_trading.db')
        conn = sqlite3.connect(db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM broker_withdrawal_notifications
            WHERE user_id = ? AND broker = 'BINANCE'
            ORDER BY created_at DESC
            LIMIT 50
        ''', (user_id,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return jsonify({"success": True, "notifications": rows})
    except Exception as e:
        logger.error(f"Binance withdrawal notifications error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@binance_api.route('/api/binance/withdrawal-notifications', methods=['POST'])
def api_binance_create_withdrawal_notification():
    """Create a withdrawal notification after profits are realized."""
    try:
        import sqlite3, uuid
        data = request.json or {}
        user_id = data.get('user_id', '')
        realized_profit = float(data.get('realized_profit', 0))
        positions_closed = int(data.get('positions_closed', 0))
        balance_available = float(data.get('balance_available', 0))
        wallet_address = data.get('wallet_address', '')

        if not user_id:
            return jsonify({"success": False, "error": "user_id required"}), 400

        db_path = os.getenv('DATABASE_PATH', 'zwesta_trading.db')
        conn = sqlite3.connect(db_path, timeout=10)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS broker_withdrawal_notifications (
                notification_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                broker TEXT NOT NULL DEFAULT 'BINANCE',
                realized_profit REAL DEFAULT 0,
                positions_closed INTEGER DEFAULT 0,
                balance_available REAL DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                completed_at TEXT
            )
        ''')

        notif_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()

        cursor.execute('''
            INSERT INTO broker_withdrawal_notifications
            (notification_id, user_id, broker, realized_profit, positions_closed,
             balance_available, status, created_at)
            VALUES (?, ?, 'BINANCE', ?, ?, ?, 'pending', ?)
        ''', (notif_id, user_id, realized_profit, positions_closed,
              balance_available, created_at))

        conn.commit()
        conn.close()
        return jsonify({
            "success": True,
            "notification_id": notif_id,
            "message": "Withdrawal notification created. Withdraw USDT to your wallet.",
        })
    except Exception as e:
        logger.error(f"Binance withdrawal notification error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

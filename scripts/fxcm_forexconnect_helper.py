#!/usr/bin/env python3

import json
import sys
from typing import Any, Dict, List, Optional

from forexconnect import fxcorepy, ForexConnect


def _input_payload() -> Dict[str, Any]:
    raw = sys.stdin.read().strip()
    return json.loads(raw) if raw else {}


def _server_url(credentials: Dict[str, Any]) -> str:
    server = str(credentials.get('server', '') or '').strip()
    if server.lower().startswith(('http://', 'https://')):
        return server
    return 'https://www.fxcorporate.com/Hosts.jsp'


def _connection_name(credentials: Dict[str, Any]) -> str:
    explicit = str(credentials.get('connection', '') or '').strip()
    if explicit:
        return explicit
    return 'Real' if bool(credentials.get('is_live', False)) else 'Demo'


def _normalized_symbol(instrument: str) -> str:
    return (instrument or '').replace('/', '').upper()


def _offer_subscription_status(offer) -> str:
    return str(getattr(offer, 'subscription_status', '') or '').upper()


def _offer_is_tradeable(offer) -> bool:
    return _offer_subscription_status(offer) == 'T' and bool(str(getattr(offer, 'offer_id', '') or '').strip())


def _offer_summary(offer) -> Dict[str, Any]:
    return {
        'instrument': str(getattr(offer, 'instrument', '') or ''),
        'subscription_status': _offer_subscription_status(offer),
        'offer_id': str(getattr(offer, 'offer_id', '') or ''),
        'tradeable': _offer_is_tradeable(offer),
    }


def _account_row_to_dict(account_row) -> Dict[str, Any]:
    balance = float(getattr(account_row, 'balance', 0) or 0)
    equity = float(getattr(account_row, 'equity', balance) or balance)
    usable_margin = float(getattr(account_row, 'usable_margin', 0) or 0)
    used_margin = float(getattr(account_row, 'usd_mr', getattr(account_row, 'mr', 0)) or 0)
    profit = float(getattr(account_row, 'gross_pl', 0) or 0)
    return {
        'account_id': str(getattr(account_row, 'account_id', '') or ''),
        'accountNumber': str(getattr(account_row, 'account_id', '') or ''),
        'balance': balance,
        'equity': equity,
        'margin_free': usable_margin,
        'marginFree': usable_margin,
        'margin': used_margin,
        'profit': profit,
        'currency': 'USD',
        'broker': 'FXCM',
        'dataSource': 'forexconnect-helper',
    }


def _get_account_row(fx: ForexConnect, credentials: Dict[str, Any]):
    accounts_table = fx.table_manager.get_table(ForexConnect.ACCOUNTS)
    account_id = str(credentials.get('account_number', '') or '').strip()
    account_row = None
    fallback_account_row = None
    if accounts_table is not None:
        for row in accounts_table:
            row_account_id = str(getattr(row, 'account_id', '') or '')
            if fallback_account_row is None:
                fallback_account_row = row
            if row_account_id == account_id or not account_id:
                account_row = row
                break
    if account_row is None and fallback_account_row is not None:
        account_row = fallback_account_row
    if account_row is None:
        raise RuntimeError('No FXCM account available for the supplied credentials')
    return account_row


def _login(credentials: Dict[str, Any]) -> ForexConnect:
    username = credentials.get('username')
    password = credentials.get('password')
    if not username or not password:
        raise RuntimeError('Missing FXCM username or password')

    fx = ForexConnect()
    fx.login(
        username,
        password,
        _server_url(credentials),
        _connection_name(credentials),
        credentials.get('session_id'),
        credentials.get('pin'),
        None,
    )
    return fx


def _find_offer_details(fx: ForexConnect, symbol: str) -> Dict[str, Any]:
    requested = _normalized_symbol(symbol)
    offers_table = fx.get_table(ForexConnect.OFFERS)
    if offers_table is None:
        return {
            'requested': requested,
            'tradeable_offer': None,
            'matching_offers': [],
        }

    matching_offers: List[Dict[str, Any]] = []
    for offer in offers_table:
        instrument = str(getattr(offer, 'instrument', '') or '')
        if _normalized_symbol(instrument) != requested:
            continue
        offer_payload = _offer_summary(offer)
        matching_offers.append(offer_payload)
        if _offer_is_tradeable(offer):
            return {
                'requested': requested,
                'tradeable_offer': offer,
                'matching_offers': matching_offers,
            }
    return {
        'requested': requested,
        'tradeable_offer': None,
        'matching_offers': matching_offers,
    }


def _find_offer(fx: ForexConnect, symbol: str):
    return _find_offer_details(fx, symbol).get('tradeable_offer')


def _debug_symbol_payload(fx: ForexConnect, credentials: Dict[str, Any], extra: Dict[str, Any]) -> Dict[str, Any]:
    symbol = str(extra.get('symbol', '') or '')
    if not symbol:
        raise RuntimeError('Missing symbol for debug_symbol')

    details = _find_offer_details(fx, symbol)
    account = _get_account_row(fx, credentials)
    return {
        'success': True,
        'symbol': symbol,
        'requested': details.get('requested'),
        'matching_offers': details.get('matching_offers') or [],
        'account_id': str(getattr(account, 'account_id', '') or credentials.get('account_number', '')),
        'dataSource': 'forexconnect-helper',
    }


def _prices_payload(fx: ForexConnect) -> Dict[str, Any]:
    """Return current bid/ask prices for all tradeable symbols."""
    offers_table = fx.get_table(ForexConnect.OFFERS)
    prices: Dict[str, Dict] = {}
    if offers_table is not None:
        for offer in offers_table:
            if not _offer_is_tradeable(offer):
                continue
            instrument = str(getattr(offer, 'instrument', '') or '').strip()
            if not instrument:
                continue
            bid = float(getattr(offer, 'bid', 0) or 0)
            ask = float(getattr(offer, 'ask', 0) or 0)
            if bid > 0 and ask > 0:
                prices[instrument] = {'bid': bid, 'ask': ask, 'price': (bid + ask) / 2}
    return {'success': True, 'prices': prices, 'dataSource': 'forexconnect-helper'}


def _tradable_symbols_payload(fx: ForexConnect, credentials: Dict[str, Any]) -> Dict[str, Any]:
    account = _get_account_row(fx, credentials)
    offers_table = fx.get_table(ForexConnect.OFFERS)
    symbols: List[str] = []
    if offers_table is not None:
        for offer in offers_table:
            if not _offer_is_tradeable(offer):
                continue
            instrument = str(getattr(offer, 'instrument', '') or '').strip()
            if instrument and instrument not in symbols:
                symbols.append(instrument)

    return {
        'success': True,
        'account_id': str(getattr(account, 'account_id', '') or credentials.get('account_number', '')),
        'symbols': symbols,
        'dataSource': 'forexconnect-helper',
    }


def _get_trades_table(fx: ForexConnect):
    return fx.table_manager.get_table(ForexConnect.TRADES) or []


def _get_closed_trades_table(fx: ForexConnect):
    return fx.table_manager.get_table(ForexConnect.CLOSED_TRADES) or []


def _find_trade(fx: ForexConnect, position_id: str):
    wanted = str(position_id or '').strip()
    for trade in _get_trades_table(fx):
        if str(getattr(trade, 'trade_id', '') or '') == wanted:
            return trade
    return None


def _resolve_amount(fx: ForexConnect, volume: float, instrument: str, account) -> int:
    requested_volume = max(float(volume or 0), 0.0)
    if requested_volume <= 0:
        return 1

    estimated_units = requested_volume * 100000.0
    try:
        trading_settings_provider = fx.login_rules.trading_settings_provider
        base_unit_size = int(trading_settings_provider.get_base_unit_size(instrument, account))
    except Exception:
        base_unit_size = 0

    if base_unit_size > 0:
        estimated_units = max(base_unit_size, round(estimated_units / base_unit_size) * base_unit_size)
    return max(int(round(estimated_units)), 1)


def _positions_payload(fx: ForexConnect, credentials: Dict[str, Any]) -> List[Dict[str, Any]]:
    account_id = str(credentials.get('account_number', '') or '')
    positions = []
    for pos in _get_trades_table(fx):
        row_account_id = str(getattr(pos, 'account_id', '') or '')
        if account_id and row_account_id != account_id:
            continue
        buy_sell = str(getattr(pos, 'buy_sell', '') or '').upper()
        positions.append({
            'deal_id': str(getattr(pos, 'trade_id', '') or ''),
            'symbol': _normalized_symbol(getattr(pos, 'instrument', '')),
            'type': 'BUY' if buy_sell.startswith('B') else 'SELL',
            'size': abs(float(getattr(pos, 'amount', 0) or 0)),
            'level': float(getattr(pos, 'open_rate', 0) or 0),
            'profit_loss': float(getattr(pos, 'gross_pl', 0) or 0),
            'broker': 'FXCM',
        })
    return positions


def _trades_payload(fx: ForexConnect, credentials: Dict[str, Any]) -> List[Dict[str, Any]]:
    account_id = str(credentials.get('account_number', '') or '')
    trades = []
    for trade in _get_closed_trades_table(fx):
        row_account_id = str(getattr(trade, 'account_id', '') or '')
        if account_id and row_account_id != account_id:
            continue
        buy_sell = str(getattr(trade, 'buy_sell', '') or '').upper()
        trades.append({
            'ticket': str(getattr(trade, 'trade_id', '') or ''),
            'symbol': _normalized_symbol(getattr(trade, 'instrument', '')),
            'type': 'BUY' if buy_sell.startswith('B') else 'SELL',
            'volume': abs(float(getattr(trade, 'amount', 0) or 0)),
            'entryPrice': float(getattr(trade, 'open_rate', 0) or 0),
            'exitPrice': float(getattr(trade, 'close_rate', 0) or 0),
            'profit': float(getattr(trade, 'gross_pl', 0) or 0),
            'time': str(getattr(trade, 'close_time', '') or getattr(trade, 'trade_close_time', '') or ''),
            'time_open': str(getattr(trade, 'open_time', '') or ''),
            'time_close': str(getattr(trade, 'close_time', '') or getattr(trade, 'trade_close_time', '') or ''),
            'broker': 'FXCM',
        })
    return trades


def _try_subscribe_offer(fx: ForexConnect, offer_id: str) -> bool:
    """Attempt to change an offer's subscription status to Trading ('T').
    Returns True if the request was accepted, False if unsupported / failed."""
    try:
        request = fx.create_order_request(
            order_type='ChangeSubscriptionStatus',
            OFFER_ID=offer_id,
            SUBSCRIPTION_STATUS='T',
        )
        fx.send_request(request)
        return True
    except Exception:
        pass
    try:
        # Alternative: via IO2GRequestFactory if exposed
        factory = getattr(fx, 'request_factory', None) or getattr(fx, '_request_factory', None)
        if factory is not None:
            req = factory.createChangeOfferSubscriptionRequest(offer_id, 'T')
            fx.send_request(req)
            return True
    except Exception:
        pass
    return False


def _place_order(fx: ForexConnect, credentials: Dict[str, Any], extra: Dict[str, Any]) -> Dict[str, Any]:
    account = _get_account_row(fx, credentials)
    symbol = str(extra.get('symbol', '') or '')
    offer_details = _find_offer_details(fx, symbol)
    offer = offer_details.get('tradeable_offer')

    # If not tradeable but present, try to subscribe it first
    if not offer:
        matching_offers = offer_details.get('matching_offers') or []
        for mo in matching_offers:
            status = str(mo.get('subscription_status', '') or '').upper()
            if status in ('D', 'V'):
                offer_id = str(mo.get('offer_id', '') or '')
                if offer_id and _try_subscribe_offer(fx, offer_id):
                    # Re-check after subscribing
                    offer_details = _find_offer_details(fx, symbol)
                    offer = offer_details.get('tradeable_offer')
                break

    if not offer:
        matching_offers = offer_details.get('matching_offers') or []
        if matching_offers:
            raise RuntimeError(
                'Instrument is not available for trading. '
                f'symbol={symbol} requested={offer_details.get("requested")} matching_offers={matching_offers}'
            )
        raise RuntimeError(
            'Instrument is not available for trading. '
            f'symbol={symbol} requested={offer_details.get("requested")} matching_offers=[]'
        )

    order_type = str(extra.get('order_type', '') or '').upper()
    buy_sell = fxcorepy.Constants.BUY if order_type == 'BUY' else fxcorepy.Constants.SELL
    instrument = str(getattr(offer, 'instrument', symbol) or symbol)
    amount = _resolve_amount(fx, float(extra.get('volume', 0) or 0), instrument, account)
    request = fx.create_order_request(
        order_type=fxcorepy.Constants.Orders.TRUE_MARKET_OPEN,
        ACCOUNT_ID=str(getattr(account, 'account_id', '') or credentials.get('account_number', '')),
        BUY_SELL=buy_sell,
        AMOUNT=amount,
        OFFER_ID=str(getattr(offer, 'offer_id', '') or ''),
    )
    try:
        response = fx.send_request(request)
    except Exception as exc:
        raise RuntimeError(
            f"Instrument is not available for trading. symbol={symbol} instrument={instrument} "
            f"offer_id={getattr(offer, 'offer_id', '')} subscription={_offer_subscription_status(offer)} amount={amount} error={exc}"
        ) from exc
    return {
        'success': True,
        'orderId': str(getattr(response, 'order_id', '') or getattr(request, 'request_id', '') or ''),
        'deal_id': '',
        'tradeId': '',
        'symbol': _normalized_symbol(instrument),
        'type': order_type,
        'amount': amount,
        'broker': 'FXCM',
        'dataSource': 'forexconnect-helper',
    }


def _close_position(fx: ForexConnect, credentials: Dict[str, Any], extra: Dict[str, Any]) -> Dict[str, Any]:
    position_id = str(extra.get('position_id', '') or '')
    trade = _find_trade(fx, position_id)
    if not trade:
        raise RuntimeError(f'FXCM trade not found: {position_id}')

    instrument = str(getattr(trade, 'instrument', '') or '')
    offer = _find_offer(fx, instrument)
    if not offer:
        raise RuntimeError(f'FXCM offer not found for trade instrument: {instrument or position_id}')

    buy_sell = str(getattr(trade, 'buy_sell', '') or '').upper()
    close_side = fxcorepy.Constants.SELL if buy_sell == fxcorepy.Constants.BUY else fxcorepy.Constants.BUY
    request = fx.create_order_request(
        order_type=fxcorepy.Constants.Orders.TRUE_MARKET_CLOSE,
        OFFER_ID=str(getattr(offer, 'offer_id', '') or ''),
        ACCOUNT_ID=str(getattr(trade, 'account_id', '') or credentials.get('account_number', '')),
        BUY_SELL=close_side,
        AMOUNT=max(int(getattr(trade, 'amount', 0) or 0), 1),
        TRADE_ID=str(getattr(trade, 'trade_id', '') or position_id),
    )
    response = fx.send_request(request)
    return {
        'success': True,
        'trade_id': str(getattr(trade, 'trade_id', '') or position_id),
        'orderId': str(getattr(response, 'order_id', '') or getattr(request, 'request_id', '') or ''),
        'broker': 'FXCM',
        'dataSource': 'forexconnect-helper',
    }


def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else ''
    payload = _input_payload()
    credentials = payload.get('credentials') or {}
    extra = payload.get('extra') or {}

    if not action:
        print(json.dumps({'success': False, 'error': 'Missing helper action'}))
        return 1

    fx = None
    try:
        fx = _login(credentials)
        account = _get_account_row(fx, credentials)
        credentials['account_number'] = str(getattr(account, 'account_id', '') or credentials.get('account_number', ''))

        if action == 'login_check':
            result = {'success': True, 'account': _account_row_to_dict(account)}
        elif action == 'get_account_info':
            result = {'success': True, 'account': _account_row_to_dict(account)}
        elif action == 'get_positions':
            result = {'success': True, 'positions': _positions_payload(fx, credentials)}
        elif action == 'get_trades':
            result = {'success': True, 'trades': _trades_payload(fx, credentials)}
        elif action == 'get_prices':
            result = _prices_payload(fx)
        elif action == 'list_symbols':
            result = _tradable_symbols_payload(fx, credentials)
        elif action == 'subscribe_symbol':
            symbol = str(extra.get('symbol', '') or '')
            if not symbol:
                raise RuntimeError('Missing symbol for subscribe_symbol')
            details = _find_offer_details(fx, symbol)
            offer = details.get('tradeable_offer')
            if offer:
                result = {'success': True, 'already_tradeable': True, 'symbol': symbol}
            else:
                matching = details.get('matching_offers') or []
                subscribed = False
                for mo in matching:
                    offer_id = str(mo.get('offer_id', '') or '')
                    if offer_id:
                        subscribed = _try_subscribe_offer(fx, offer_id)
                        if subscribed:
                            break
                result = {'success': subscribed, 'symbol': symbol, 'matching_offers': matching,
                          'error': None if subscribed else 'Could not change subscription status via API'}
        elif action == 'place_order':
            result = _place_order(fx, credentials, extra)
        elif action == 'debug_symbol':
            result = _debug_symbol_payload(fx, credentials, extra)
        elif action == 'close_position':
            result = _close_position(fx, credentials, extra)
        else:
            result = {'success': False, 'error': f'Unsupported helper action: {action}'}
            print(json.dumps(result))
            return 1

        print(json.dumps(result))
        return 0 if result.get('success') else 1
    except Exception as exc:
        print(json.dumps({'success': False, 'error': str(exc)}))
        return 1
    finally:
        if fx is not None:
            try:
                fx.logout()
            except Exception:
                pass


if __name__ == '__main__':
    raise SystemExit(main())
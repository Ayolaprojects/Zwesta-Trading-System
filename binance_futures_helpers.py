"""
Binance Futures Helper Functions

These functions support the Futures trading features:
- SHORT position opening/closing
- Leverage management
- Position mode management  
- Liquidation price calculation
"""

def prepare_futures_order_params(
    order_type: str,
    symbol: str,
    quantity: float,
    position_mode: str = 'one_way',
    reduce_only: bool = False,
) -> dict:
    """
    Prepare order parameters for Binance Futures.
    
    Args:
        order_type: 'BUY' or 'SELL'
        symbol: Binance futures symbol (e.g., 'BTCUSDT')
        quantity: Position size
        position_mode: 'one_way' or 'hedge'
        reduce_only: True to close position, False to open
        
    Returns:
        Order parameters dict
    """
    params = {
        'symbol': symbol,
        'side': order_type.upper(),
        'type': 'MARKET',
        'quantity': str(quantity),
    }
    
    # For one-way mode, track whether we're opening or closing
    if position_mode == 'one_way':
        params['reduceOnly'] = 'true' if reduce_only else 'false'
    
    return params


def calculate_futures_position_size(
    account_equity: float,
    risk_per_trade: float,
    leverage: float = 1.0,
    max_leverage_cap: float = 5.0,
) -> float:
    """
    Calculate position size for Futures accounting for leverage.
    
    Example:
        equity=10000, risk=2%, leverage=5x → can risk 2% of 50000 (10000 * 5)
        
    Args:
        account_equity: Current account equity
        risk_per_trade: Risk percentage (e.g., 2.0 for 2%)
        leverage: Leverage multiplier (1-125)
        max_leverage_cap: Cap to prevent excessive leverage
        
    Returns:
        Position size in base asset value (USDT equivalent)
    """
    effective_leverage = min(float(leverage), float(max_leverage_cap))
    risk_amount = (account_equity * risk_per_trade) / 100.0
    # With leverage, we can risk on a position sized leverage * risk_amount
    return risk_amount * effective_leverage


def calculate_liquidation_price(
    entry_price: float,
    position_type: str,  # 'BUY' (long) or 'SELL' (short)
    leverage: float,
    maintenance_margin_rate: float = 0.05,  # 5% for most symbols
) -> float:
    """
    Calculate estimated liquidation price for Futures position.
    
    Formula:
        LONG:  liquidation = entry * (1 - 1/leverage + maintenance_margin)
        SHORT: liquidation = entry * (1 + 1/leverage - maintenance_margin)
        
    Args:
        entry_price: Entry price
        position_type: 'BUY' for long, 'SELL' for short
        leverage: Leverage multiplier
        maintenance_margin_rate: Maintenance margin ratio
        
    Returns:
        Liquidation price
    """
    if leverage <= 0:
        return 0.0
    
    if position_type.upper() == 'BUY':
        # Long liquidation - price must stay above this
        liq_price = entry_price * (1 - (1 / leverage) + maintenance_margin_rate)
    else:
        # Short liquidation - price must stay below this
        liq_price = entry_price * (1 + (1 / leverage) - maintenance_margin_rate)
    
    return max(0.0, liq_price)


def evaluate_position_closing_signal_futures(
    position: dict,
    current_price: float,
    signal_eval: dict,
    position_type_target: str = 'BUY',  # What position type to close
) -> bool:
    """
    Determine if a Futures position should be closed based on signal.
    
    For futures, we track both the position type (BUY/SELL) and 
    the desired close signal.
    
    Args:
        position: Open position dict
        current_price: Current market price
        signal_eval: Signal evaluation result
        position_type_target: Position type to close ('BUY' or 'SELL')
        
    Returns:
        True if position should be closed
    """
    pos_type = position.get('type', 'BUY').upper()
    
    # Only close if position type matches
    if pos_type != position_type_target.upper():
        return False
    
    # Check signal
    signal = signal_eval.get('signal', '').upper()
    profit = position.get('profit', 0.0)
    
    # Close LONG on SELL signal or if at take-profit
    if pos_type == 'BUY':
        if 'SELL' in signal or profit >= position.get('takeProfitPrice', float('inf')):
            return True
    
    # Close SHORT on BUY signal or if at take-profit
    elif pos_type == 'SELL':
        if 'BUY' in signal or profit >= position.get('takeProfitPrice', float('inf')):
            return True
    
    return False


def get_binance_futures_position_risk(
    position_dict: dict,
    market_price: float,
) -> dict:
    """
    Calculate risk metrics for Futures position.
    
    Returns:
        dict with unrealized_pnl, pnl_percent, liquidation_price, etc.
    """
    entry_price = position_dict.get('entryPrice', 0.0)
    size = position_dict.get('volume', 0.0)
    position_type = position_dict.get('type', 'BUY').upper()
    leverage = position_dict.get('leverage', 1.0)
    
    if not entry_price or not size:
        return {
            'unrealized_pnl': 0.0,
            'pnl_percent': 0.0,
            'liquidation_price': 0.0,
            'margin_ratio': 0.0,
        }
    
    # Calculate unrealized PnL
    if position_type == 'BUY':
        unrealized_pnl = size * (market_price - entry_price)
    else:  # SELL (short)
        unrealized_pnl = size * (entry_price - market_price)
    
    # PnL as percentage of margin used
    margin_used = (size * entry_price) / leverage
    pnl_percent = (unrealized_pnl / margin_used * 100) if margin_used > 0 else 0.0
    
    # Liquidation price
    liq_price = calculate_liquidation_price(
        entry_price,
        position_type,
        leverage,
        maintenance_margin_rate=0.05,
    )
    
    return {
        'unrealized_pnl': unrealized_pnl,
        'pnl_percent': pnl_percent,
        'liquidation_price': liq_price,
        'margin_ratio': abs(market_price - entry_price) / entry_price if entry_price > 0 else 0.0,
    }

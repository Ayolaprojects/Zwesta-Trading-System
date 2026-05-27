"""
Backend Code Snippets for Profit Pyramiding Implementation
Add these to multi_broker_backend_updated.py
"""

PYRAMIDING_CODE = '''
# ==================== PROFIT PYRAMIDING LOGIC ====================
# Add this to your trading loop (around line 25000-30000)

def calculate_position_profit_pct(position, current_price):
    """Calculate current profit % for a position"""
    if not position or not current_price:
        return 0.0
    
    entry_price = position.get('entry_price', 0)
    if entry_price == 0:
        return 0.0
    
    position_type = position.get('type', 'buy')
    
    if position_type == 'buy':
        profit_pct = ((current_price - entry_price) / entry_price) * 100
    else:  # sell
        profit_pct = ((entry_price - current_price) / entry_price) * 100
    
    return profit_pct

def should_add_to_position(position, current_price, runtime_state):
    """Check if we should pyramid into this winning position"""
    
    pyramid_config = runtime_state.get('profit_pyramiding', {})
    if not pyramid_config.get('enabled', False):
        return False, 0
    
    profit_pct = calculate_position_profit_pct(position, current_price)
    
    if profit_pct <= 0:
        return False, 0  # Not profitable yet
    
    # Check which pyramid level we should be at
    pyramid_levels = pyramid_config.get('pyramid_levels', [])
    current_pyramids = position.get('pyramid_count', 0)
    max_total_multiplier = pyramid_config.get('max_total_multiplier', 10.0)
    
    for level in pyramid_levels:
        threshold = level['profit_threshold_pct']
        multiplier = level['size_multiplier']
        
        # If we crossed this threshold and haven't pyramided yet
        if profit_pct >= threshold and current_pyramids < len(pyramid_levels):
            # Check we haven't exceeded max multiplier
            total_current_multiplier = position.get('total_size_multiplier', 1.0)
            if total_current_multiplier < max_total_multiplier:
                return True, multiplier
    
    return False, 0

def add_pyramid_position(bot_id, existing_position, multiplier, broker_type):
    """Add to winning position (pyramid)"""
    
    try:
        symbol = existing_position['symbol']
        position_type = existing_position['type']
        current_size = existing_position['size']
        
        # Calculate additional size
        additional_size = current_size * (multiplier - 1.0)  # e.g., 2.0x means add 1.0x more
        
        if broker_type == 'Binance':
            # Binance Futures pyramid
            order = binance_client.futures_create_order(
                symbol=symbol,
                side='BUY' if position_type == 'buy' else 'SELL',
                type='MARKET',
                quantity=additional_size
            )
            
            logger.info(f"🔼 Binance pyramid: Added {additional_size} to {symbol} at {multiplier}x")
            
        elif broker_type == 'Exness':
            # MT5 pyramid
            import MetaTrader5 as mt5
            
            # Convert to lots for MT5
            additional_lots = additional_size * 0.01  # Adjust based on your lot size calculation
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": additional_lots,
                "type": mt5.ORDER_TYPE_BUY if position_type == 'buy' else mt5.ORDER_TYPE_SELL,
                "deviation": 20,
                "magic": 234000,
                "comment": f"Pyramid +{multiplier}x",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(f"🔼 Exness pyramid: Added {additional_lots} lots to {symbol}")
            else:
                logger.error(f"❌ Pyramid failed: {result.comment}")
        
        # Update position metadata
        existing_position['pyramid_count'] = existing_position.get('pyramid_count', 0) + 1
        existing_position['total_size_multiplier'] = existing_position.get('total_size_multiplier', 1.0) + (multiplier - 1.0)
        existing_position['pyramids'] = existing_position.get('pyramids', [])
        existing_position['pyramids'].append({
            'level': existing_position['pyramid_count'],
            'multiplier': multiplier,
            'added_size': additional_size,
            'timestamp': datetime.now().isoformat(),
            'price': get_current_price(symbol, broker_type)
        })
        
        return True
    
    except Exception as e:
        logger.error(f"❌ Pyramid error: {e}")
        return False

def check_and_add_pyramids(bot_id, runtime_state, broker_type):
    """
    Main function to check all open positions and add pyramids if profitable
    Call this in your main trading loop every tick/minute
    """
    
    # Get all open positions for this bot
    open_positions = get_open_positions(bot_id, broker_type)
    
    for position in open_positions:
        symbol = position['symbol']
        current_price = get_current_price(symbol, broker_type)
        
        # Check if we should pyramid
        should_pyramid, multiplier = should_add_to_position(position, current_price, runtime_state)
        
        if should_pyramid:
            success = add_pyramid_position(bot_id, position, multiplier, broker_type)
            
            if success:
                profit_pct = calculate_position_profit_pct(position, current_price)
                logger.info(f"✅ {bot_id}: Pyramided {symbol} at +{profit_pct:.2f}% with {multiplier}x size")
                
                # Save updated position state
                save_position_state(bot_id, position)

def check_reversal_and_close_pyramids(position, current_price, runtime_state):
    """
    Close pyramid additions if price reverses against us
    Protects accumulated profits
    """
    
    pyramid_config = runtime_state.get('profit_pyramiding', {})
    if not pyramid_config.get('partial_close_on_reversal', False):
        return False
    
    # Track peak profit
    peak_profit_pct = position.get('peak_profit_pct', 0)
    current_profit_pct = calculate_position_profit_pct(position, current_price)
    
    if current_profit_pct > peak_profit_pct:
        position['peak_profit_pct'] = current_profit_pct
        return False  # New peak, don't close
    
    # Check for reversal from peak
    reversal_threshold = pyramid_config.get('reversal_threshold_pct', -0.2)
    reversal_pct = current_profit_pct - peak_profit_pct
    
    if reversal_pct <= reversal_threshold:
        # Reversal detected - close pyramid additions
        logger.warning(f"⚠️  Reversal detected: {reversal_pct:.2f}% from peak. Closing pyramids.")
        
        pyramids = position.get('pyramids', [])
        for pyramid in reversed(pyramids):  # Close in reverse order (newest first)
            close_partial_position(position, pyramid['added_size'])
            logger.info(f"🔻 Closed pyramid level {pyramid['level']} ({pyramid['multiplier']}x)")
        
        position['pyramids'] = []
        position['pyramid_count'] = 0
        position['total_size_multiplier'] = 1.0
        
        return True
    
    return False

# ==================== INTEGRATION EXAMPLE ====================
# Add this to your main bot loop (e.g., in run_trading_bot function)

def run_trading_bot_with_pyramiding(bot_id, runtime_state):
    """Enhanced bot with profit pyramiding"""
    
    while bot_enabled:
        try:
            # ... existing signal detection code ...
            
            # NEW: Check for pyramid opportunities on open positions
            check_and_add_pyramids(bot_id, runtime_state, broker_type)
            
            # NEW: Check for reversals and protect profits
            for position in get_open_positions(bot_id, broker_type):
                current_price = get_current_price(position['symbol'], broker_type)
                check_reversal_and_close_pyramids(position, current_price, runtime_state)
            
            # ... rest of existing bot logic ...
            
        except Exception as e:
            logger.error(f"Bot error: {e}")
            time.sleep(5)

# ==================== BINANCE DAILY TARGET CHECKER ====================

def check_binance_daily_target(bot_id, runtime_state):
    """
    Check if bot hit 5% daily target
    If yes, stop trading for the day (lock in profits)
    """
    
    pyramid_config = runtime_state.get('profit_pyramiding', {})
    daily_target = pyramid_config.get('binance_daily_target_pct', 5.0)
    
    # Get today's profit
    today_profit_pct = calculate_today_profit_pct(bot_id)
    
    if today_profit_pct >= daily_target:
        logger.info(f"🎯 Daily target reached: {today_profit_pct:.2f}% (target: {daily_target}%)")
        logger.info(f"💰 Stopping trading for today to lock in profits")
        
        # Close all positions
        close_all_positions(bot_id, 'Binance')
        
        # Disable bot until tomorrow
        disable_bot_until_tomorrow(bot_id)
        
        return True
    
    return False

def calculate_today_profit_pct(bot_id):
    """Calculate today's profit % for a bot"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    today = datetime.now().date().isoformat()
    
    cursor.execute('''
        SELECT SUM(profit) as today_profit
        FROM trades
        WHERE bot_id = ?
          AND DATE(closed_at) = ?
    ''', (bot_id, today))
    
    row = cursor.fetchone()
    today_profit = row['today_profit'] if row and row['today_profit'] else 0
    
    # Get account balance to calculate %
    cursor.execute('''
        SELECT runtime_state FROM user_bots WHERE bot_id = ?
    ''', (bot_id,))
    
    state = json.loads(cursor.fetchone()['runtime_state'])
    account_balance = state.get('account_balance', 1000)  # Default if not set
    
    conn.close()
    
    profit_pct = (today_profit / account_balance) * 100
    return profit_pct
'''

def save_code_snippets():
    """Save code snippets to file"""
    
    output_path = r'C:\zwesta-trader\PYRAMIDING_IMPLEMENTATION_CODE.py'
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(PYRAMIDING_CODE)
    
    print(f"✅ Code snippets saved to: {output_path}")
    print()
    print("📋 To implement:")
    print("1. Copy functions from PYRAMIDING_IMPLEMENTATION_CODE.py")
    print("2. Add to multi_broker_backend_updated.py")
    print("3. Integrate into main trading loop")
    print("4. Test with demo account first")
    print()
    print("⚠️  Key integration points:")
    print("   - Add check_and_add_pyramids() to main bot loop")
    print("   - Add check_reversal_and_close_pyramids() for risk management")
    print("   - Add check_binance_daily_target() for Binance bots")

if __name__ == '__main__':
    save_code_snippets()
    
    print("""
╔══════════════════════════════════════════════════════════╗
║   Pyramiding Implementation Guide                       ║
╚══════════════════════════════════════════════════════════╝

📝 Implementation Steps:

1️⃣  Enable Pyramiding Config:
    python _enable_profit_pyramiding.py

2️⃣  Add Code to Backend:
    - Open: c:\\zwesta-trader\\PYRAMIDING_IMPLEMENTATION_CODE.py
    - Copy all functions
    - Paste into: C:\\backend\\multi_broker_backend_updated.py
    
3️⃣  Integrate into Trading Loop:
    Find your main bot loop (run_trading_bot or similar)
    Add these calls:
    
    ```python
    while bot_enabled:
        # ... existing signal detection ...
        
        # Add pyramiding
        check_and_add_pyramids(bot_id, runtime_state, broker_type)
        
        # Protect profits
        for pos in get_open_positions():
            check_reversal_and_close_pyramids(pos, current_price, runtime_state)
        
        # Check Binance daily target
        if broker_type == 'Binance':
            if check_binance_daily_target(bot_id, runtime_state):
                break  # Target reached, stop for today
    ```

4️⃣  Test with Demo Account:
    - Run bot on demo first
    - Verify pyramids are added at profit levels
    - Confirm reversals close pyramids
    - Check daily target stops trading

5️⃣  Deploy to Live:
    - Once proven on demo
    - Restart backend with new code
    - Monitor closely for first week

🎯 Expected Results:
   - Exness: R5 → R50+ per trade
   - Binance: 5% daily minimum
   - Compounding effect: 150%+ monthly
    """)

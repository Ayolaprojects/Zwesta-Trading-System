# Binance Futures Support Implementation Guide

## Status: Multi-Stage Deployment
- **Stage 1 (DONE)**: Core configuration and position tracking structure
- **Stage 2 (IN PROGRESS)**: Order placement and closing for shorts
- **Stage 3 (PENDING)**: Leverage and position mode management
- **Stage 4 (PENDING)**: Live testing and monitoring

## Architecture Overview

### Key Components

#### 1. **Market Type Configuration**
```python
# In broker_credentials:
{
    'market': 'futures' or 'spot',  # Default: 'spot'
    'leverage': 1-125,               # Default: 1 (no leverage)
    'position_mode': 'hedge' or 'one_way',  # Default: 'one_way'
    'margin_type': 'cross' or 'isolated',   # Default: 'cross'
}
```

#### 2. **Position Tracking for Futures**
Futures positions support both LONG and SHORT:
```python
{
    'ticket': 'FUTURES-BTC-BOT-ABC123',
    'symbol': 'BTCUSDT',
    'type': 'BUY',      # LONG position
    'volume': 0.5,      # Size in base asset
    'entryPrice': 42000,
    'currentPrice': 42500,
    'profit': 250,      # Unrealized PnL
    'position_mode': 'one_way',
    'leverage': 5,
    'margin_type': 'cross',
    'liquidation_price': 30000,  # NEW for futures
    'mark_price': 42450,         # NEW for futures
}
```

#### 3. **Order Routing Changes**
- **SPOT**: Only BUY allowed (creates inventory) + SELL (reduces inventory)
- **FUTURES**: BUY (opens LONG) + SELL (opens SHORT or closes LONG)

#### 4. **Seed-Buy Compatibility**
Seed-buy works with both SPOT and FUTURES:
- **SPOT**: Small BUY creates inventory, SELL later
- **FUTURES**: Small BUY opens tiny LONG, SELL later closes it

## Configuration Updates

### Bot Configuration (New Fields)
```python
'binanceMarket': 'spot',              # or 'futures'
'binanceLeverage': 1,                 # 1-125 for futures
'binancePositionMode': 'one_way',     # 'hedge' or 'one_way'
'binanceMarginType': 'cross',         # 'cross' or 'isolated'
'maxLeveragePerPosition': 5,           # Cap on risk per trade
```

### PERSISTED_BOT_STATE_FIELDS Updates
```python
PERSISTED_BOT_STATE_FIELDS = {
    # ... existing fields ...
    'binanceMarket', 'binanceLeverage', 'binancePositionMode', 
    'binanceMarginType', 'maxLeveragePerPosition',
}
```

## Implementation Details

### Phase 1: Core Order Handling

**For SELL orders on Futures:**
```python
if self.market == 'futures':
    # SELL can mean:
    # 1. Close existing LONG by selling
    # 2. Open new SHORT by selling
    # Use 'reduceOnly' flag to distinguish
    
    if position_exists_for_symbol:
        params['reduceOnly'] = 'true'  # Close existing
    else:
        params['reduceOnly'] = 'false' # Open SHORT
```

### Phase 2: Position Closing Logic

**For Futures Shorts:**
```python
def close_futures_short(symbol, position_size):
    # Close SHORT by BUY (opposite of open)
    order = {
        'symbol': symbol,
        'side': 'BUY',
        'type': 'MARKET',
        'quantity': position_size,
        'reduceOnly': 'true',
    }
```

### Phase 3: PnL Calculation Updates

**Futures PnL**:
- Unrealized: Mark price vs entry price
- Realized: From closed positions
- Includes funding fees, leverage multiplier
- Support both LONG and SHORT profit scenarios

## Testing Checklist

- [ ] Create bot with `binanceMarket='futures'`
- [ ] Place LONG order (BUY)
- [ ] Place SHORT order (SELL)
- [ ] Close LONG position (SELL with reduceOnly)
- [ ] Close SHORT position (BUY with reduceOnly)
- [ ] Test profit/loss calculations for both
- [ ] Verify leverage impact on position sizing
- [ ] Test liquidation protection
- [ ] Monitor funding fee accrual

## API Endpoints Used

**Futures**:
- `POST /fapi/v1/order` - Place order
- `DELETE /fapi/v1/openOrders` - Cancel orders
- `GET /fapi/v2/positionRisk` - Get positions
- `POST /fapi/v1/leverage` - Set leverage
- `POST /fapi/v1/marginType` - Set margin type
- `POST /fapi/v1/positionSide/dual` - Set position mode

**Spot**:
- `POST /api/v3/order` - Place order
- `GET /api/v3/account` - Get positions
- `DELETE /api/v3/openOrders` - Cancel orders

## Deployment Steps

1. Update credentials to include `market` field
2. Add bot configuration fields for market type/leverage
3. Update position tracker for SHORT support
4. Enhance order placement logic
5. Update PnL calculations
6. Deploy to sandbox first
7. Test with small live trades
8. Monitor liquidation protection
9. Production rollout

## Migration Path (Existing Bots)

- Existing bots remain on SPOT (default)
- New bots can specify market type
- Mixed portfolios supported (some SPOT, some FUTURES)
- No breaking changes to existing SPOT bot logic

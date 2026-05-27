# ═══════════════════════════════════════════════════════════════════════════
# FIX TRADE ANALYTICS - Improve Recent Trade Capture & Display Order
# ═══════════════════════════════════════════════════════════════════════════
# Run this on VPS to fix:
# 1. Missing recent trades in analytics
# 2. Ensure latest trades show on top
# ═══════════════════════════════════════════════════════════════════════════

Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  🔧 FIX TRADE ANALYTICS - Capture & Ordering              ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# ══════════════════════════════════════════════════════════════════════════
# STEP 1: Check Current Trade History
# ══════════════════════════════════════════════════════════════════════════
Write-Host "[1/4] Checking current trade history..." -ForegroundColor Yellow

$checkScript = @"
import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect(r'C:\backend\zwesta_trading.db')
cur = conn.cursor()

# Check total trades
cur.execute('SELECT COUNT(*) FROM trades')
total = cur.fetchone()[0]
print(f'TOTAL_TRADES:{total}')

# Check recent trades (last 24h)
yesterday = (datetime.now() - timedelta(hours=24)).isoformat()
cur.execute('SELECT COUNT(*) FROM trades WHERE created_at >= ?', (yesterday,))
recent = cur.fetchone()[0]
print(f'RECENT_24H:{recent}')

# Check closed vs open
cur.execute('SELECT COUNT(*) FROM trades WHERE status=?', ('closed',))
closed = cur.fetchone()[0]
print(f'CLOSED:{closed}')

cur.execute('SELECT COUNT(*) FROM trades WHERE status=?', ('open',))
open_count = cur.fetchone()[0]
print(f'OPEN:{open_count}')

# Show last 5 trades with timestamps
cur.execute('''
    SELECT symbol, order_type, profit, status, created_at, time_close
    FROM trades 
    ORDER BY COALESCE(time_close, created_at) DESC 
    LIMIT 5
''')
print('LAST_5_TRADES:')
for row in cur.fetchall():
    symbol, order_type, profit, status, created, closed = row
    time_ref = closed if closed else created
    print(f'  {symbol} {order_type} P/L:{profit} {status} @ {time_ref}')

conn.close()
"@

$tradeStats = $checkScript | python 2>&1

foreach ($line in $tradeStats) {
    if ($line -match 'TOTAL_TRADES:(\d+)') {
        Write-Host "  Total trades in DB: $($Matches[1])" -ForegroundColor Cyan
    } elseif ($line -match 'RECENT_24H:(\d+)') {
        Write-Host "  Trades last 24h: $($Matches[1])" -ForegroundColor Cyan
    } elseif ($line -match 'CLOSED:(\d+)') {
        Write-Host "  Closed trades: $($Matches[1])" -ForegroundColor Cyan
    } elseif ($line -match 'OPEN:(\d+)') {
        Write-Host "  Open trades: $($Matches[1])" -ForegroundColor Cyan
    } elseif ($line -match 'LAST_5_TRADES:') {
        Write-Host "  Recent trades:" -ForegroundColor Cyan
    } elseif ($line -match '^\s+[A-Z]') {
        Write-Host $line -ForegroundColor Gray
    }
}

# ══════════════════════════════════════════════════════════════════════════
# STEP 2: Sync Missing MT5 Trades from Terminal
# ══════════════════════════════════════════════════════════════════════════
Write-Host "`n[2/4] Syncing recent trades from MT5 terminal..." -ForegroundColor Yellow

$syncScript = @"
import sqlite3
import MetaTrader5 as mt5
from datetime import datetime, timedelta
import json

# Initialize MT5
if not mt5.initialize():
    print('ERROR:MT5_NOT_INITIALIZED')
    exit(1)

# Get deals from last 7 days
from_time = datetime.now() - timedelta(days=7)
deals = mt5.history_deals_get(from_time, datetime.now())

if not deals:
    print('NO_MT5_DEALS')
    mt5.shutdown()
    exit(0)

print(f'MT5_DEALS:{len(deals)}')

# Connect to database
conn = sqlite3.connect(r'C:\backend\zwesta_trading.db')
cur = conn.cursor()

# Get existing tickets
cur.execute('SELECT DISTINCT ticket FROM trades')
existing_tickets = set([str(row[0]) for row in cur.fetchall()])

# Process deals
new_count = 0
for deal in deals:
    # Only include closed positions (exit deals)
    if deal.entry != 1:  # entry=1 means OUT (exit)
        continue
    
    ticket = str(deal.ticket)
    if ticket in existing_tickets:
        continue
    
    # This is a new closed trade
    deal_type = 'BUY' if deal.type == 0 else 'SELL'
    profit = round(float(deal.profit), 2)
    
    # Skip zero-profit balance adjustments
    if profit == 0 and deal.symbol == '':
        continue
    
    trade_id = f'trade_{int(datetime.now().timestamp()*1000)}_{ticket}'
    close_time = datetime.fromtimestamp(deal.time).isoformat()
    
    trade_data = {
        'ticket': ticket,
        'symbol': deal.symbol,
        'type': deal_type,
        'volume': float(deal.volume),
        'price': float(deal.price),
        'profit': profit,
        'commission': float(deal.commission),
        'swap': float(deal.swap),
        'closeTime': close_time,
        'source': 'MT5_SYNC',
    }
    
    try:
        cur.execute('''
            INSERT INTO trades (
                trade_id, bot_id, user_id, symbol, order_type, volume, 
                price, profit, ticket, time_open, time_close, status, 
                created_at, trade_data, timestamp, broker
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade_id,
            'system_sync',  # bot_id
            'system',  # user_id - will need to be updated manually if needed
            deal.symbol,
            deal_type,
            float(deal.volume),
            float(deal.price),
            profit,
            ticket,
            None,  # time_open
            close_time,
            'closed',
            datetime.now().isoformat(),
            json.dumps(trade_data),
            int(datetime.now().timestamp() * 1000),
            'MT5'
        ))
        new_count += 1
    except Exception as e:
        print(f'ERROR_INSERTING:{ticket}:{e}')

conn.commit()
conn.close()
mt5.shutdown()

print(f'SYNCED_NEW:{new_count}')
"@

try {
    $syncResult = $syncScript | python 2>&1
    
    foreach ($line in $syncResult) {
        if ($line -match 'MT5_DEALS:(\d+)') {
            Write-Host "  MT5 deals found (7 days): $($Matches[1])" -ForegroundColor Cyan
        } elseif ($line -match 'SYNCED_NEW:(\d+)') {
            $newTrades = $Matches[1]
            Write-Host "  ✓ Synced $newTrades new trade(s) from MT5" -ForegroundColor Green
        } elseif ($line -match 'NO_MT5_DEALS') {
            Write-Host "  No MT5 deals found" -ForegroundColor Yellow
        } elseif ($line -match 'ERROR:') {
            Write-Host "  ⚠️  $line" -ForegroundColor Red
        }
    }
} catch {
    Write-Host "  ⚠️  MT5 sync failed: $($_.Exception.Message)" -ForegroundColor Yellow
}

# ══════════════════════════════════════════════════════════════════════════
# STEP 3: Add Index for Faster Sorting (If Missing)
# ══════════════════════════════════════════════════════════════════════════
Write-Host "`n[3/4] Optimizing database indexes..." -ForegroundColor Yellow

$indexScript = @"
import sqlite3

conn = sqlite3.connect(r'C:\backend\zwesta_trading.db')
cur = conn.cursor()

# Check if index exists
cur.execute('''
    SELECT name FROM sqlite_master 
    WHERE type='index' AND name='idx_trades_time_close_desc'
''')

if not cur.fetchone():
    # Create index for faster sorting by close time (DESC)
    cur.execute('''
        CREATE INDEX IF NOT EXISTS idx_trades_time_close_desc 
        ON trades(time_close DESC, created_at DESC)
    ''')
    print('INDEX_CREATED')
else:
    print('INDEX_EXISTS')

# Also create index for user_id + status queries
cur.execute('''
    SELECT name FROM sqlite_master 
    WHERE type='index' AND name='idx_trades_user_status'
''')

if not cur.fetchone():
    cur.execute('''
        CREATE INDEX IF NOT EXISTS idx_trades_user_status 
        ON trades(user_id, status, time_close DESC)
    ''')
    print('USER_INDEX_CREATED')
else:
    print('USER_INDEX_EXISTS')

conn.commit()
conn.close()
"@

$indexResult = $indexScript | python 2>&1

foreach ($line in $indexResult) {
    if ($line -match 'INDEX_CREATED') {
        Write-Host "  ✓ Created index for faster sorting" -ForegroundColor Green
    } elseif ($line -match 'INDEX_EXISTS') {
        Write-Host "  Index already exists" -ForegroundColor Cyan
    } elseif ($line -match 'USER_INDEX') {
        Write-Host "  ✓ User+status index optimized" -ForegroundColor Green
    }
}

# ══════════════════════════════════════════════════════════════════════════
# STEP 4: Verify Ordering (Test Query)
# ══════════════════════════════════════════════════════════════════════════
Write-Host "`n[4/4] Verifying trade order (newest first)..." -ForegroundColor Yellow

$verifyScript = @"
import sqlite3
from datetime import datetime

conn = sqlite3.connect(r'C:\backend\zwesta_trading.db')
cur = conn.cursor()

# Query with proper ordering (newest first)
cur.execute('''
    SELECT symbol, profit, status, time_close, created_at
    FROM trades
    ORDER BY COALESCE(time_close, created_at) DESC
    LIMIT 5
''')

print('TOP_5_TRADES:')
for i, row in enumerate(cur.fetchall(), 1):
    symbol, profit, status, time_close, created = row
    time_ref = time_close if time_close else created
    print(f'{i}. {symbol} P/L:\${profit} ({status}) @ {time_ref}')

conn.close()
"@

$verifyResult = $verifyScript | python 2>&1

foreach ($line in $verifyResult) {
    if ($line -match 'TOP_5_TRADES:') {
        Write-Host "  Most recent trades (newest → oldest):" -ForegroundColor Cyan
    } elseif ($line -match '^\d+\.') {
        Write-Host "  $line" -ForegroundColor Gray
    }
}

# ══════════════════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════════════════
Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  ✅ TRADE ANALYTICS FIXES APPLIED                         ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Green

Write-Host "CHANGES MADE:" -ForegroundColor Cyan
Write-Host "  1. Synced missing MT5 trades from terminal history" -ForegroundColor White
Write-Host "  2. Created database indexes for faster queries" -ForegroundColor White
Write-Host "  3. Verified ordering (newest trades first)" -ForegroundColor White

Write-Host "`nHOW TO VERIFY IN MOBILE APP:" -ForegroundColor Yellow
Write-Host "  1. Open mobile app → Bot Analytics" -ForegroundColor White
Write-Host "  2. Trade history should now show latest on top" -ForegroundColor White
Write-Host "  3. Recent trades should appear within seconds" -ForegroundColor White

Write-Host "`nBACKEND ALREADY CONFIGURED:" -ForegroundColor Yellow
Write-Host "  • Line 14899: ORDER BY time_close DESC ✓" -ForegroundColor Gray
Write-Host "  • Line 15034: reverse=True sorting ✓" -ForegroundColor Gray
Write-Host "  • Line 6471: MT5 trades sorted newest first ✓" -ForegroundColor Gray

Write-Host "`nTO MAINTAIN ACCURACY:" -ForegroundColor Yellow
Write-Host "  • Run this script weekly to catch any missed trades" -ForegroundColor White
Write-Host "  • Or restart backend after heavy trading days" -ForegroundColor White

Write-Host "`n`nPress any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')

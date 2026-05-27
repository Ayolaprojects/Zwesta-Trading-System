# ═══════════════════════════════════════════════════════════════════════════
# FIX "NO BOTS APPEARING" ISSUE - Comprehensive Diagnostic & Repair
# ═══════════════════════════════════════════════════════════════════════════
# Run this script when your mobile app shows empty bot list
# Works for both LOCAL and VPS deployments
# ═══════════════════════════════════════════════════════════════════════════

param(
    [string]$Mode = "local",  # "local" or "vps"
    [string]$VpsIp = "148.113.5.39"
)

$ErrorActionPreference = "Continue"

Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  🔍 FIX 'NO BOTS APPEARING' - Diagnostic Tool             ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Determine paths based on mode
if ($Mode -eq "vps") {
    $DbPath = "C:\backend\zwesta_trading.db"
    $ApiUrl = "http://$VpsIp:9000"
    Write-Host "Mode: VPS ($VpsIp)" -ForegroundColor Yellow
} else {
    $DbPath = "C:\backend\zwesta_trading.db"
    $ApiUrl = "http://localhost:9000"
    Write-Host "Mode: LOCAL" -ForegroundColor Yellow
}

Write-Host "Database: $DbPath" -ForegroundColor Gray
Write-Host "API URL: $ApiUrl`n" -ForegroundColor Gray

# ══════════════════════════════════════════════════════════════════════════
# STEP 1: Check Database Exists and Has Bots
# ══════════════════════════════════════════════════════════════════════════
Write-Host "[1/6] Checking database..." -ForegroundColor Yellow

if (!(Test-Path $DbPath)) {
    Write-Host "  ❌ ERROR: Database not found at $DbPath" -ForegroundColor Red
    Write-Host "     Solution: Copy database from local to VPS or create new one" -ForegroundColor Yellow
    exit 1
}

$dbSize = (Get-Item $DbPath).Length / 1KB
Write-Host "  ✓ Database found: $([math]::Round($dbSize, 2)) KB" -ForegroundColor Green

# Query database for bots
$checkBotsScript = @"
import sqlite3, json
conn = sqlite3.connect(r'$DbPath')
cur = conn.cursor()

# Check total bots
cur.execute('SELECT COUNT(*) FROM user_bots')
total = cur.fetchone()[0]
print(f'TOTAL_BOTS:{total}')

# Check enabled bots
cur.execute('SELECT COUNT(*) FROM user_bots WHERE enabled=1')
enabled = cur.fetchone()[0]
print(f'ENABLED_BOTS:{enabled}')

# List users
cur.execute('SELECT DISTINCT user_id FROM user_bots')
users = [row[0] for row in cur.fetchall()]
print(f'UNIQUE_USERS:{len(users)}')

# Show first 3 bots with user_id
cur.execute('SELECT bot_id, name, user_id, enabled FROM user_bots LIMIT 3')
for bot_id, name, user_id, enabled in cur.fetchall():
    status = 'ENABLED' if enabled else 'DISABLED'
    print(f'BOT:{bot_id}|{name}|{user_id[:8]}...|{status}')

conn.close()
"@

$dbInfo = $checkBotsScript | python 2>&1

foreach ($line in $dbInfo) {
    if ($line -match 'TOTAL_BOTS:(\d+)') {
        $totalBots = $Matches[1]
        Write-Host "  Total bots in DB: $totalBots" -ForegroundColor Cyan
    } elseif ($line -match 'ENABLED_BOTS:(\d+)') {
        $enabledBots = $Matches[1]
        Write-Host "  Enabled bots: $enabledBots" -ForegroundColor Cyan
    } elseif ($line -match 'UNIQUE_USERS:(\d+)') {
        $uniqueUsers = $Matches[1]
        Write-Host "  Users with bots: $uniqueUsers" -ForegroundColor Cyan
    } elseif ($line -match 'BOT:(.+)') {
        if ($script:firstBot -ne $true) {
            Write-Host "  Sample bots:" -ForegroundColor Gray
            $script:firstBot = $true
        }
        $parts = $Matches[1] -split '\|'
        Write-Host "    • $($parts[1]) (User: $($parts[2]), $($parts[3]))" -ForegroundColor Gray
    }
}

if ($totalBots -eq 0) {
    Write-Host "`n  ⚠️  NO BOTS IN DATABASE!" -ForegroundColor Red
    Write-Host "     Root cause: Database is empty" -ForegroundColor Yellow
    Write-Host "     Solution: Create a new bot via mobile app or API" -ForegroundColor Yellow
    Write-Host "`n     To create test bot, run: python _create_test_bot.py`n" -ForegroundColor Cyan
    exit 0
}

# ══════════════════════════════════════════════════════════════════════════
# STEP 2: Check Backend is Running
# ══════════════════════════════════════════════════════════════════════════
Write-Host "`n[2/6] Checking backend status..." -ForegroundColor Yellow

try {
    $health = Invoke-RestMethod -Uri "$ApiUrl/api/health" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "  ✓ Backend is ONLINE" -ForegroundColor Green
    Write-Host "    Status: $($health.status)" -ForegroundColor Cyan
    if ($health.database) {
        Write-Host "    Database: $($health.database)" -ForegroundColor Cyan
    }
} catch {
    Write-Host "  ❌ Backend NOT responding at $ApiUrl" -ForegroundColor Red
    Write-Host "     Root cause: Backend not running or wrong IP" -ForegroundColor Yellow
    Write-Host "     Solution:" -ForegroundColor Yellow
    if ($Mode -eq "vps") {
        Write-Host "       1. RDP to VPS: mstsc /v:$VpsIp" -ForegroundColor White
        Write-Host "       2. Start backend: python 'C:\zwesta-trader\Zwesta Flutter App\multi_broker_backend_updated.py'" -ForegroundColor White
    } else {
        Write-Host "       cd 'C:\zwesta-trader\Zwesta Flutter App'" -ForegroundColor White
        Write-Host "       python multi_broker_backend_updated.py" -ForegroundColor White
    }
    exit 1
}

# ══════════════════════════════════════════════════════════════════════════
# STEP 3: Get Active Sessions and User IDs
# ══════════════════════════════════════════════════════════════════════════
Write-Host "`n[3/6] Checking user sessions..." -ForegroundColor Yellow

$sessionScript = @"
import sqlite3
from datetime import datetime
conn = sqlite3.connect(r'$DbPath')
cur = conn.cursor()

cur.execute('''
    SELECT user_id, token, expires_at, is_active 
    FROM user_sessions 
    WHERE is_active = 1 
    ORDER BY created_at DESC 
    LIMIT 5
''')

active_sessions = 0
for user_id, token, expires_at, is_active in cur.fetchall():
    active_sessions += 1
    token_short = token[:16] if token else 'None'
    print(f'SESSION:{user_id}|{token_short}...|{expires_at}')

if active_sessions == 0:
    print('NO_ACTIVE_SESSIONS')

conn.close()
"@

$sessions = $sessionScript | python 2>&1
$hasActiveSessions = $false

foreach ($line in $sessions) {
    if ($line -match 'SESSION:(.+)') {
        if (-not $hasActiveSessions) {
            Write-Host "  Active sessions found:" -ForegroundColor Cyan
            $hasActiveSessions = $true
        }
        $parts = $line -replace 'SESSION:', '' -split '\|'
        Write-Host "    • User: $($parts[0])" -ForegroundColor Gray
        Write-Host "      Token: $($parts[1])" -ForegroundColor Gray
        Write-Host "      Expires: $($parts[2])" -ForegroundColor Gray
    } elseif ($line -match 'NO_ACTIVE_SESSIONS') {
        Write-Host "  ⚠️  NO ACTIVE SESSIONS" -ForegroundColor Yellow
        Write-Host "     Root cause: User not logged in or session expired" -ForegroundColor Yellow
        Write-Host "     Solution: Login again via mobile app" -ForegroundColor Yellow
    }
}

# ══════════════════════════════════════════════════════════════════════════
# STEP 4: Test API Bot Listing
# ══════════════════════════════════════════════════════════════════════════
Write-Host "`n[4/6] Testing API bot listing..." -ForegroundColor Yellow

# Get a valid session token from database
$getTokenScript = @"
import sqlite3
conn = sqlite3.connect(r'$DbPath')
cur = conn.cursor()
cur.execute('SELECT user_id, token FROM user_sessions WHERE is_active=1 LIMIT 1')
row = cur.fetchone()
if row:
    print(f'{row[0]}|{row[1]}')
conn.close()
"@

$tokenInfo = $getTokenScript | python 2>&1
if ($tokenInfo -match '(.+)\|(.+)') {
    $testUserId = $Matches[1]
    $testToken = $Matches[2]
    
    Write-Host "  Testing with user: $testUserId" -ForegroundColor Gray
    
    try {
        $headers = @{
            'X-Session-Token' = $testToken
            'Content-Type' = 'application/json'
        }
        
        $response = Invoke-RestMethod -Uri "$ApiUrl/api/user/$testUserId/bots" -Headers $headers -TimeoutSec 10 -ErrorAction Stop
        
        if ($response.success) {
            $botCount = $response.bots.Count
            Write-Host "  ✓ API returned $botCount bot(s)" -ForegroundColor Green
            
            if ($botCount -eq 0) {
                Write-Host "`n  ⚠️  API RETURNS EMPTY LIST" -ForegroundColor Red
                Write-Host "     Root cause: Bots exist in DB but don't belong to logged-in user" -ForegroundColor Yellow
                Write-Host "     This is a USER_ID MISMATCH issue" -ForegroundColor Yellow
            } else {
                Write-Host "  Sample bots from API:" -ForegroundColor Cyan
                foreach ($bot in $response.bots | Select-Object -First 3) {
                    Write-Host "    • $($bot.name) ($($bot.bot_id))" -ForegroundColor Gray
                }
            }
        } else {
            Write-Host "  ❌ API error: $($response.error)" -ForegroundColor Red
        }
    } catch {
        Write-Host "  ❌ API call failed: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "  ⚠️  No active sessions to test with" -ForegroundColor Yellow
}

# ══════════════════════════════════════════════════════════════════════════
# STEP 5: Check for User ID Mismatch
# ══════════════════════════════════════════════════════════════════════════
Write-Host "`n[5/6] Checking for user_id mismatch..." -ForegroundColor Yellow

$mismatchScript = @"
import sqlite3
conn = sqlite3.connect(r'$DbPath')
cur = conn.cursor()

# Get users with active sessions
cur.execute('SELECT DISTINCT user_id FROM user_sessions WHERE is_active=1')
session_users = set([row[0] for row in cur.fetchall()])

# Get users with bots
cur.execute('SELECT DISTINCT user_id FROM user_bots')
bot_users = set([row[0] for row in cur.fetchall()])

# Find mismatches
if session_users and bot_users:
    no_bots = session_users - bot_users
    no_sessions = bot_users - session_users
    
    if no_bots:
        for user in no_bots:
            print(f'LOGGED_IN_NO_BOTS:{user}')
    
    if no_sessions:
        for user in no_sessions:
            print(f'HAS_BOTS_NOT_LOGGED_IN:{user}')
    
    if not no_bots and not no_sessions:
        print('USER_IDS_MATCH')

conn.close()
"@

$mismatch = $mismatchScript | python 2>&1

foreach ($line in $mismatch) {
    if ($line -match 'LOGGED_IN_NO_BOTS:(.+)') {
        Write-Host "  ⚠️  User $($Matches[1]) is logged in but has NO BOTS" -ForegroundColor Yellow
        Write-Host "     Solution: Create a bot for this user" -ForegroundColor Cyan
    } elseif ($line -match 'HAS_BOTS_NOT_LOGGED_IN:(.+)') {
        Write-Host "  ⚠️  User $($Matches[1]) has BOTS but NOT LOGGED IN" -ForegroundColor Yellow
        Write-Host "     Solution: Login as this user in mobile app" -ForegroundColor Cyan
    } elseif ($line -match 'USER_IDS_MATCH') {
        Write-Host "  ✓ User IDs are correctly matched" -ForegroundColor Green
    }
}

# ══════════════════════════════════════════════════════════════════════════
# STEP 6: Provide Solutions
# ══════════════════════════════════════════════════════════════════════════
Write-Host "`n[6/6] Solutions & Recommendations" -ForegroundColor Yellow

Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  🔧 COMMON FIXES FOR 'NO BOTS APPEARING'                  ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Green

Write-Host "1. SESSION EXPIRED:" -ForegroundColor Cyan
Write-Host "   • Open mobile app → Logout → Login again" -ForegroundColor White
Write-Host "   • This generates new session token`n" -ForegroundColor White

Write-Host "2. WRONG API URL:" -ForegroundColor Cyan
Write-Host "   • Mobile app should connect to: $ApiUrl" -ForegroundColor White
Write-Host "   • Check Flutter EnvironmentConfig.apiUrl setting`n" -ForegroundColor White

Write-Host "3. USER_ID MISMATCH:" -ForegroundColor Cyan
Write-Host "   • Bots belong to different user than logged in" -ForegroundColor White
Write-Host "   • Create new bot while logged in as current user`n" -ForegroundColor White

Write-Host "4. BACKEND NOT RUNNING:" -ForegroundColor Cyan
if ($Mode -eq "vps") {
    Write-Host "   • RDP to VPS: mstsc /v:$VpsIp" -ForegroundColor White
    Write-Host "   • Run: python 'C:\zwesta-trader\Zwesta Flutter App\multi_broker_backend_updated.py'`n" -ForegroundColor White
} else {
    Write-Host "   • cd 'C:\zwesta-trader\Zwesta Flutter App'" -ForegroundColor White
    Write-Host "   • python multi_broker_backend_updated.py`n" -ForegroundColor White
}

Write-Host "5. EMPTY DATABASE:" -ForegroundColor Cyan
Write-Host "   • Create test bot: python _create_test_bot.py" -ForegroundColor White
Write-Host "   • Or create via mobile app UI`n" -ForegroundColor White

Write-Host "`nQuick test - Create bot via API:" -ForegroundColor Yellow
Write-Host @"
  curl -X POST $ApiUrl/api/bot/create \
    -H 'X-Session-Token: YOUR_TOKEN' \
    -H 'Content-Type: application/json' \
    -d '{"name":"Test Bot","strategy":"trend_following","symbols":["BTCUSDT"]}'
"@ -ForegroundColor Gray

Write-Host "`n`nPress any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')

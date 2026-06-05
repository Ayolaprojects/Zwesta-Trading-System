# NEW USER & BOT CREATION WORKFLOW GUIDE

## ✓ SYSTEM STATUS (as of June 5, 2026)
- **8 active bots** running and trading
- **0 disabled bots** (cleanup complete)
- **7 users** in system
- **Binance**: 5 active credentials
- **Exness**: 3 active credentials
- **28 trades** successfully executed

---

## WORKFLOW 1: NEW USER REGISTRATION

### Step 1: User Registers
**Endpoint**: `POST /api/user/register`

```json
{
  "email": "newtrader@example.com",
  "name": "New Trader",
  "password": "securepassword123",
  "referral_code": "optional_referrer_code"  // optional
}
```

**Response**:
```json
{
  "success": true,
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "newtrader@example.com",
  "session_token": "token_abc123xyz"
}
```

**Database**: User created in `users` table with:
- `user_id`: UUID generated
- `email`: unique constraint
- `referral_code`: auto-generated
- `created_at`: timestamp

**✓ VALIDATION**:
- Email must be unique
- Password requirements enforced
- Session token issued for subsequent requests

---

## WORKFLOW 2: ADD BROKER CREDENTIALS (BINANCE)

### Step 2a: User Adds Binance Credentials
**Endpoint**: `POST /api/broker/test-connection`

```json
{
  "broker": "Binance",
  "account_number": "API_KEY_HERE",
  "password": "API_SECRET_HERE",
  "is_live": false,
  "server": "futures"  // or "spot"
}
```

**Process**:
1. Test connection to Binance API
2. Fetch account balance
3. Verify API permissions
4. Store credential in `broker_credentials` table

**Database entry**:
```sql
INSERT INTO broker_credentials (
  credential_id, user_id, broker_name, account_number, 
  password, is_live, is_active, created_at
) VALUES (
  'cred_uuid', 'user_id', 'Binance', 'api_key',
  'api_secret_encrypted', false, true, NOW()
)
```

**✓ VALIDATION**:
- Binance API key/secret format
- Actual connection test
- Account permissions check
- Balance retrieval

---

## WORKFLOW 3: ADD BROKER CREDENTIALS (EXNESS)

### Step 2b: User Adds Exness Credentials
**Endpoint**: `POST /api/broker/exness/login`

```json
{
  "broker": "Exness",
  "account_number": "11111111",  // MT5 account number
  "password": "your_mt5_password",
  "is_live": false,
  "server": "Exness-Demo"  // or "Exness-Real"
}
```

**Process**:
1. Connect to MT5 terminal
2. Test login credentials
3. Fetch account info
4. Verify account type (Demo/Live)
5. Store credential in `broker_credentials` table

**Database entry**: Same as Binance

**✓ VALIDATION**:
- MT5 account number format (8 digits)
- Password correctness
- Server connectivity (Demo/Live)
- Account balance accessible

---

## WORKFLOW 4: CREATE BOT (BINANCE)

### Step 3a: Create Binance Bot
**Endpoint**: `POST /api/bot/create` or `POST /api/bot/quick-create`

#### Option A: Quick Create (Preset Symbols)
```json
{
  "credentialId": "cred_uuid_from_binance",
  "preset": "top_edge"  // or "balanced"
}
```

**Auto-selected symbols**:
- `top_edge`: BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, ADAUSDT, DOGEUSDT
- `balanced`: Mix of high-cap and mid-cap pairs

#### Option B: Custom Create
```json
{
  "credentialId": "cred_uuid",
  "symbols": ["BTCUSDT", "ETHUSDT", "BCHUSDT"],
  "strategy": "Trend Following",
  "baseAmount": 100.0,
  "riskLevel": "medium"
}
```

**Process**:
1. Validate credential belongs to user
2. Validate broker is Binance
3. Validate symbols available on Binance
4. Create bot record with generated `bot_id`
5. Initialize runtime state
6. Start trading thread
7. Begin placing orders

**Database entry**:
```sql
INSERT INTO user_bots (
  bot_id, user_id, name, strategy, status, enabled,
  broker_account_id, symbols, created_at, runtime_state
) VALUES (
  'bot_1780614250152', 'user_id', 'Bot - Trend Following',
  'Trend Following', 'active', true, 'Binance_API_KEY',
  'BTCUSDT,ETHUSDT,...', NOW(), '{...runtime_state_json...}'
)
```

**Response**:
```json
{
  "success": true,
  "bot_id": "bot_1780614250152",
  "status": "active",
  "tradesStarted": 2,
  "pairs": ["BTCUSDT", "ETHUSDT", "BCHUSDT"]
}
```

**✓ VALIDATION**:
- Credential exists and belongs to user
- Broker is Binance
- Symbols valid on Binance
- API key has trading permission
- Account has sufficient balance
- Position size within risk limits

---

## WORKFLOW 5: CREATE BOT (EXNESS)

### Step 3b: Create Exness Bot
**Endpoint**: `POST /api/bot/create`

```json
{
  "credentialId": "cred_uuid_from_exness",
  "symbols": ["XAUUSDm", "GBPUSDm", "AUDUSDm"],
  "strategy": "Trend Following",
  "baseAmount": 100.0,
  "leverage": 1.0
}
```

**Process**:
1. Validate credential belongs to user
2. Validate broker is Exness (MT5)
3. Validate symbols available on Exness
4. Create bot record
5. Initialize MT5 connection
6. Start trading thread
7. Begin placing orders

**Database entry**: Same structure as Binance

**✓ VALIDATION**:
- Credential exists and belongs to user
- Broker is Exness
- Symbols valid on Exness (e.g., XAUUSDm, GBPUSDm)
- MT5 login works
- Account has sufficient balance
- Leverage within account limits

---

## COMPLETE WORKFLOW CHECKLIST

### For New Users:
- [ ] User registration (email + password)
- [ ] Session token issued
- [ ] Receive login confirmation

### For Binance Users:
- [ ] User adds Binance API key + secret
- [ ] Connection test passes
- [ ] Credential stored in database
- [ ] User can create Binance bots
- [ ] Bot auto-starts trading
- [ ] Trades recorded in database

### For Exness Users:
- [ ] User adds Exness MT5 account
- [ ] MT5 connection test passes
- [ ] Credential stored in database
- [ ] User can create Exness bots
- [ ] Bot auto-starts trading
- [ ] Trades recorded in database

### Bot Creation (Both Brokers):
- [ ] Bot created with unique `bot_id`
- [ ] Bot linked to user + credential
- [ ] Bot status = "active"
- [ ] Bot enabled = true
- [ ] Trading thread started
- [ ] First orders placed within 1 minute
- [ ] Trades recorded in database
- [ ] User can view open positions

---

## TROUBLESHOOTING

### User Can't Register
**Check**: 
- Email uniqueness in `users` table
- Password validation rules
- Database connection

### Credential Test Fails
**Binance**:
- API key format
- API secret matches key
- Permissions: "Spot Trading" enabled
- IP whitelist configured

**Exness**:
- Account number format (8 digits)
- MT5 password correct
- Demo/Live server selection
- MT5 terminal running on server

### Bot Won't Start Trading
**Check**:
- Bot status = "active"
- Bot enabled = true
- Credential is_active = true
- Account has balance
- Symbols valid for broker
- Trading thread logs

### No Trades Appearing
**Check**:
- Bot process running (check logs)
- Market is open
- Sufficient volume on symbol
- Risk filters not blocking orders
- Trades table not full

---

## SYSTEM MAINTENANCE

### Regular Checks:
```bash
# Verify bot system
python _verify_bot_creation_system.py

# Verify user registration
python _verify_user_registration.py

# Cleanup disabled bots
python _auto_cleanup_disabled_bots.py

# Diagnostic on specific bot
python _diagnose_postgres_bots.py
```

### Database Backups:
```bash
# Daily backup recommendation
pg_dump zwesta_trading > backup_$(date +%Y%m%d).sql
```

---

## SUCCESS METRICS

✓ **New users can**:
- Register successfully
- Add Binance credentials
- Add Exness credentials
- Create bots immediately
- See trades within 1 minute
- Earn commissions

✓ **System is healthy when**:
- 0 stopped bots
- All enabled bots trading
- New users completing full workflow
- Trades recorded within 1 second
- No credential errors

---

## NEXT STEPS

1. **Test with new user registration**
2. **Guide users through Binance setup**
3. **Guide users through Exness setup**
4. **Create bots and verify trading**
5. **Monitor trade execution**
6. **Check user feedback**

All systems ready! 🚀

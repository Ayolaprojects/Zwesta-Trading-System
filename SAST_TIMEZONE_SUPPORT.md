# South Africa Timezone (SAST) Support Added

## Summary

All bot status responses now include **South African Standard Time (SAST)** versions of cooldown/pause times.

## What Changed

### 1. Backend API Enhancement
- Added `_convert_utc_to_sast()` helper function
- Bot status endpoint now returns both UTC and SAST times:
  - `drawdownPauseUntil` (UTC) + `drawdownPauseUntilSAST` (SAST)
  - `profitLockCooldownUntil` (UTC) + `profitLockCooldownUntilSAST` (SAST)

### 2. Standalone Converter Tool
- Created `_convert_times_to_sast.py` to check bot times locally

## How to Use on VPS

### Option 1: Check via API
When you call `/api/bot/status`, you'll now see:
```json
{
  "botId": "bot_123",
  "drawdownPauseUntil": "2026-05-27T14:30:00",
  "drawdownPauseUntilSAST": "2026-05-27 16:30:00 SAST",  // ← NEW! Your time
  "profitLockCooldownUntil": "2026-05-27T15:00:00",
  "profitLockCooldownUntilSAST": "2026-05-27 17:00:00 SAST"  // ← NEW! Your time
}
```

### Option 2: Run Local Converter on VPS
```powershell
cd C:\backend
python _convert_times_to_sast.py
```

This shows:
- Current time in UTC and SAST
- All bot cooldown/pause times in SAST
- How many hours remaining until unpause

## Example Output

```
⏰ CURRENT TIME
================================================================================
UTC:  2026-05-27 12:00:00 UTC
SAST: 2026-05-27 14:00:00 SAST (South Africa)

🕐 BOT COOLDOWN & PAUSE TIMES (South African Time - SAST)
================================================================================

🤖 bot_1779663832148... (Exness Bot 1)
   Status: ✅ ENABLED |
   ⏸️  PAUSED UNTIL: 2026-05-27 16:30:00 SAST
      ⏱️  Still paused for: 2.5 hours
   
🤖 bot_1779676762137... (Exness Bot 2)
   Status: ✅ ENABLED |
   💰 Profit Lock Cooldown Until: 2026-05-27 17:15:00 SAST
```

## Time Conversion Reference

**South Africa Time Zone:**
- **SAST** = UTC + 2 hours
- No daylight saving time

**Examples:**
- 12:00 UTC = 14:00 SAST (2pm South Africa)
- 18:00 UTC = 20:00 SAST (8pm South Africa)
- 06:00 UTC = 08:00 SAST (8am South Africa)

## Files Modified

1. `_vps_deploy_bundle/multi_broker_backend_updated.py`
   - Added `_convert_utc_to_sast()` function
   - Enhanced `/api/bot/status` endpoint

2. `Zwesta Flutter App/multi_broker_backend_updated.py`
   - Same changes (backend copy)

3. `_convert_times_to_sast.py` (NEW)
   - Standalone tool to check times locally

4. `_optimize_bots_vps.py`
   - Already configured with 30x-50x position sizing
   - Ready to deploy with timezone support

## Next Steps

Deploy updated backend to VPS, then you'll see SAST times automatically in all bot status responses! 🇿🇦

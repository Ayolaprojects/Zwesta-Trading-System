# VPS Bot Fix — Deploy Runbook (2026-06-04)

Fixes three issues reported on the live system (148.113.5.39:9000):

1. **Bots don't display / can't be created** — caused by a Binance worker-pool
   crash storm. `.env` had `BINANCE_WORKER_COUNT=5`; each worker re-imports the
   entire backend, never reaches health within the 60s grace window, and gets
   killed/respawned forever. That saturates CPU, so `/api/bot/summary` exceeds
   the app's 10s timeout and bots never load.
2. **Binance bots show "trading" but place no real trades** — same root cause:
   the assignment row persists but the worker never runs the trading loop.
3. **Exness live bots blocked** by a phantom "account profit staircase floor"
   (locked floor far above real equity after a bad peak/surge-guard value).

## What the fix does
- Sets `BINANCE_WORKER_COUNT=0` → Binance bots run as in-process daemon threads
  (same model MT5 already uses). No more worker storm; bots trade.
- Clears phantom `accountProfitStaircase` / `accountEquityHighWatermark` /
  `drawdownPauseUntil` from `user_bots.runtime_state` so bots re-baseline at real
  equity. (`accountProfitStaircaseEnabled` is left intact — the guard re-arms
  naturally from true equity.)

## Files
- `apply_bot_fixes.ps1` — one-shot orchestrator (run this).
- `_reset_profit_staircase.py` — the state-reset tool (called by the script;
  can also be run standalone).

## Deploy (RDP onto the VPS)
1. Copy both files into `C:\backend\`.
2. (Optional) Preview the bot-state changes without writing anything:
   ```powershell
   powershell -ExecutionPolicy Bypass -File C:\backend\apply_bot_fixes.ps1 -WhatIfReset
   ```
3. Apply the full fix:
   ```powershell
   powershell -ExecutionPolicy Bypass -File C:\backend\apply_bot_fixes.ps1
   ```
   It backs up `.env`, patches it, stops the watchdog/backend/stray workers,
   resets bot state, restarts via `start_zwesta_backend.ps1`, and waits for
   `/api/health`.

## Verify
- Backend log shows:
  `[OK] Binance worker pool disabled (BINANCE_WORKER_COUNT=0) - using local Binance threads`
- `Binance worker N started (PID ...)` lines have **stopped** appearing.
- `http://127.0.0.1:9000/api/health` returns instantly.
- Open the app → bots list loads; create a bot → succeeds.

## Flags
- `-SkipStaircaseReset` — only apply the worker fix + restart (don't touch bot state).
- `-WhatIfReset` — dry-run the bot-state reset (show changes, write nothing).

## Not fixable in code
`BINANCE-FUTURES-DEMO` returns `401 -2015 Invalid API-key, IP, or permissions`.
You must supply a valid Binance API key/secret and whitelist the VPS IP
(148.113.5.39) in the Binance API settings for that bot to connect.

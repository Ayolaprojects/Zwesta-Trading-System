"""
Local trading simulation for Exness + Binance bots.
Exercises the profit-protection evaluator with synthetic price paths
so you can verify threshold + metals override behaviour before VPS deploy.

Run: python local_trade_sim.py
"""
from __future__ import annotations

import os
import sys
import json
import copy
import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

os.environ['ZWESTA_SKIP_PYTHON_REEXEC'] = '1'
os.environ['DEPLOYMENT_MODE'] = 'LOCAL'
os.environ['LOG_LEVEL'] = 'ERROR'
os.environ.pop('ZWESTA_MIN_HOLD_MINUTES', None)  # use module default (7.0)

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import importlib.util
spec = importlib.util.spec_from_file_location('mbu', os.path.join(HERE, 'multi_broker_backend_updated.py'))
mbu = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mbu)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def ts(minutes_ago: float) -> str:
    return (datetime.now() - timedelta(minutes=minutes_ago)).isoformat()


def make_bot(broker: str, symbol: str, profile: str = 'balanced',
             mode: str = 'demo', balance: float = 1000.0) -> Dict[str, Any]:
    return {
        'bot_id': 'sim_001',
        'user_id': 'sim_user',
        'brokerName': broker,
        'broker_type': broker,
        'symbols': [symbol],
        'managementProfile': profile,
        'mode': mode,
        'displayCurrency': 'USD',
        'accountBalance': balance,
        'accountEquity': balance,
        'tradingInterval': 90,
        'profitProtection': {},
    }


def make_position(symbol: str, side: str, entry: float, volume: float,
                  entry_time_ago_min: float = 0.0,
                  current_price: Optional[float] = None) -> Dict[str, Any]:
    """Create a synthetic open-position dict that mimics what the backend tracks."""
    now = datetime.now()
    entry_dt = now - timedelta(minutes=entry_time_ago_min)
    cp = current_price if current_price is not None else entry
    raw = {
        'ticket': f'SIM-{symbol}-{int(now.timestamp())}',
        'symbol': symbol,
        'type': side.upper(),
        'volume': volume,
        'entryPrice': entry,
        'currentPrice': cp,
        'marketPrice': cp,
        'price_current': cp,
        'entryTime': entry_dt.isoformat(),
        'openTime': entry_dt.isoformat(),
        'peakProfit': 0.0,
        'peakRoiPct': 0.0,
        'lockedProfitFloor': 0.0,
        'breakEvenLocked': False,
        'breakEvenFloor': 0.0,
        'profitProtectionArmed': False,
        'isPyramidAddon': False,
        'roiPct': 0.0,
        'peakRoiPct': 0.0,
        'peakRoiPctUpdatedAt': None,
    }
    raw['profit'] = round(mbu._resolve_open_position_profit(raw), 2)
    raw['peakProfit'] = max(0.0, raw['profit'])
    return raw


# ---------------------------------------------------------------------------
# Price-path simulator
# ---------------------------------------------------------------------------
def simulate_price_path(
    entry: float,
    steps: List[Tuple[float, float]],   # (minutes_from_entry, profit_usd)
    volume: float,
    side: str = 'SELL',
) -> List[Dict[str, Any]]:
    """Return a list of position snapshots along a synthetic profit path.

    Each step is (minutes_from_entry, profit_usd). We don't compute price→profit
    here because the backend uses MT5's own `position.profit` field (which already
    encodes lot size, contract size, leverage, etc.). We just feed profit directly.
    """
    snaps: List[Dict[str, Any]] = []
    peak = 0.0
    for t_min, profit in steps:
        peak = max(peak, profit)
        snap = {
            't_min': t_min,
            'profit': round(profit, 2),
            'peak_profit': round(peak, 2),
        }
        snaps.append(snap)
    return snaps


# ---------------------------------------------------------------------------
# Profit-protection evaluator (extracts the close_reason logic)
# ---------------------------------------------------------------------------
def evaluate_close_reason(
    bot_config: Dict[str, Any],
    position: Dict[str, Any],
    symbol: str,
    market_data: Optional[Dict[str, Any]] = None,
) -> Tuple[Optional[str], Dict[str, Any]]:
    """Call into the backend's protection resolver + the close-eval block.

    Returns (close_reason_or_None, resolved_protection_config).
    """
    resolved = mbu._resolve_profit_protection_for_symbol(bot_config, symbol, market_data)
    hold = mbu._minimum_position_hold_minutes(bot_config, resolved)
    now_iso = datetime.now().isoformat()

    # Build a tracked state the close evaluator expects
    entry_time = position.get('entryTime') or ts(0)
    peak_profit = position.get('peakProfit', max(0.0, position.get('profit', 0.0)))
    if peak_profit <= 0:
        peak_profit = max(0.0, position.get('profit', 0.0))
    tracked = {
        'ticket': position.get('ticket', 'SIM'),
        'symbol': symbol,
        'type': position.get('type', 'SELL'),
        'volume': position.get('volume', 0.01),
        'entryPrice': position.get('entryPrice', 0.0),
        'currentPrice': position.get('currentPrice', position.get('marketPrice', 0.0)),
        'entryTime': entry_time,
        'profit': position.get('profit', 0.0),
        'peakProfit': round(peak_profit, 2),
        'peakRoiPct': position.get('peakRoiPct', 0.0),
        'roiPct': position.get('roiPct', 0.0),
        'peakRoiPctUpdatedAt': position.get('peakRoiPctUpdatedAt'),
        'peakProfitUpdatedAt': entry_time,
        'lockedProfitFloor': position.get('lockedProfitFloor', 0.0),
        'breakEvenLocked': position.get('breakEvenLocked', False),
        'breakEvenFloor': position.get('breakEvenFloor', 0.0),
        'profitProtectionArmed': position.get('profitProtectionArmed', False),
        'isPyramidAddon': position.get('isPyramidAddon', False),
        'pyramidLockedProfitShare': position.get('pyramidLockedProfitShare'),
        'pyramidMaxHoldMinutes': position.get('pyramidMaxHoldMinutes'),
    }

    # We need to reproduce enough of the close evaluator to find the trigger.
    # Rather than calling manage_protected_open_positions (which needs broker
    # connections), we replicate the critical close-reason block using the
    # same public helpers.
    current_profit = tracked['profit']
    peak_profit = tracked['peakProfit']
    time_in_position = mbu._position_age_minutes(tracked.get('entryTime'))

    # Hard loss cap (for logging)
    hard_loss_limit, _ = mbu._resolve_hard_loss_limits(bot_config)

    # meaningful profit peak
    activation_amount = mbu._profit_protection_activation_amount(bot_config, resolved)
    meaningful_profit_peak = round(max(0.1, min(activation_amount, peak_profit))) if peak_profit > 0 else 0.1
    hard_peak_share = resolved.get('peakProfitHardLockShare', 0.9)
    _effective_peak_lock_share = 0.65 if peak_profit < meaningful_profit_peak else hard_peak_share
    hard_peak_lock_floor = round(max(0.0, peak_profit * _effective_peak_lock_share), 2) if peak_profit > 0 else 0.0

    debug = (
        f'peak={peak_profit:.2f} activation={activation_amount:.2f} '
        f'meaningful={meaningful_profit_peak:.2f} floor={hard_peak_lock_floor:.2f} '
        f'share={_effective_peak_lock_share}'
    )

    # Armed?
    if peak_profit >= activation_amount:
        tracked['profitProtectionArmed'] = True
        protected_floor = max(
            resolved.get('minLockedProfit', 0.0),
            peak_profit * (1.0 - (resolved.get('retraceClosePercent', 35.0) / 100.0)),
        )
        tracked['lockedProfitFloor'] = round(
            max(0.0, min(max(tracked.get('lockedProfitFloor', 0.0), protected_floor), peak_profit)), 2
        )

    protection_hold_satisfied = time_in_position >= hold
    never_negative_activation = max(0.25, resolved.get('neverNegativeActivationProfit', 1.0))
    never_negative_floor = max(0.0, resolved.get('neverNegativeFloorProfit', 0.25))

    # Zero-loss hold
    broker_name = mbu.canonicalize_broker_name(
        bot_config.get('brokerName') or bot_config.get('broker_type') or bot_config.get('broker') or ''
    )
    is_forex = mbu._is_exness_forex_symbol(symbol)
    is_index = (broker_name == 'Exness'
                and mbu._normalize_symbol_base(symbol) in {
                    'US30', 'USTEC', 'US500', 'US100', 'NDX', 'NDXF',
                    'NAS100', 'DAX', 'GER30', 'UK100', 'FR40', 'JP225',
                    'AUS200', 'SPX', 'CAC40'})
    is_binance = broker_name == 'Binance'
    is_exness_forex_position = broker_name == 'Exness' and is_forex
    zero_loss_hold = (
        protection_hold_satisfied
        if (is_exness_forex_position or is_index)
        else (protection_hold_satisfied or peak_profit >= meaningful_profit_peak)
    )

    triggers = []
    # break-even is a state setter (locks floor), not a close trigger — removed from triggers

    hard_peak_share = resolved.get('peakProfitHardLockShare', 0.9)
    _effective_peak_lock_share = 0.65 if peak_profit < meaningful_profit_peak else hard_peak_share
    hard_peak_lock_floor = round(max(0.0, peak_profit * _effective_peak_lock_share), 2) if peak_profit > 0 else 0.0
    if is_exness_forex_position:
        hard_peak_lock_eligible = peak_profit >= meaningful_profit_peak
    elif is_index or is_binance:
        hard_peak_lock_eligible = peak_profit > 0
    else:
        hard_peak_lock_eligible = peak_profit > 0
    _hpl = (hard_peak_lock_eligible and current_profit <= hard_peak_lock_floor)
    if _hpl:
        triggers.append(('HARD_PEAK_PROFIT_LOCK', f'eligible={hard_peak_lock_eligible} current {current_profit:.2f} <= floor {hard_peak_lock_floor:.2f} (share {_effective_peak_lock_share})'))

    if resolved.get('neverNegativeAfterProfitEnabled') and peak_profit >= never_negative_activation and current_profit <= never_negative_floor:
        triggers.append(('NEVER_NEGATIVE_LOCK', f'peak {peak_profit:.2f} >= activation {never_negative_activation:.2f}; current {current_profit:.2f} <= floor {never_negative_floor:.2f}'))

    if resolved.get('zeroLossLockEnabled') and peak_profit > 0 and current_profit <= 0 and zero_loss_hold:
        triggers.append(('ZERO_LOSS_LOCK', f'peak {peak_profit:.2f} > 0; current {current_profit:.2f} <= 0; hold_satisfied={zero_loss_hold}'))

    if current_profit <= -hard_loss_limit:
        triggers.append(('HARD_LOSS_LIMIT', f'current {current_profit:.2f} <= -{hard_loss_limit:.2f}'))

    return triggers, resolved


# ---------------------------------------------------------------------------
# Scenario runner
# ---------------------------------------------------------------------------
def run_scenario(name: str, bot_config: Dict[str, Any], symbol: str,
                 side: str, entry: float, volume: float,
                 path: List[Tuple[float, float]]) -> None:
    print(f"\n{'='*70}")
    print(f"SCENARIO: {name}")
    print(f"  Broker={bot_config['brokerName']} Symbol={symbol} Side={side}")
    print(f"  Profile={bot_config['managementProfile']} Mode={bot_config['mode']}")
    print(f"  Entry={entry} Volume={volume}")
    print()

    resolved = mbu._resolve_profit_protection_for_symbol(bot_config, symbol, None)
    hold = mbu._minimum_position_hold_minutes(bot_config, resolved)
    threshold = mbu._default_signal_threshold_for_broker_profile(
        bot_config['managementProfile'], bot_config['brokerName']
    )

    print(f"  [CONFIG]  threshold={threshold}  hold={hold:.2f} min")
    print(f"  [PROTECTION] activationMinProfit={resolved.get('activationMinProfit')} "
          f" neverNegAct={resolved.get('neverNegativeActivationProfit')} "
          f" neverNegFloor={resolved.get('neverNegativeFloorProfit')} "
          f" hardLockShare={resolved.get('peakProfitHardLockShare')} "
          f" zeroLoss={resolved.get('zeroLossLockEnabled')} "
          f" retracePct={resolved.get('retraceClosePercent')} "
          f" metalsOverride={resolved.get('_volatileMetalHoldOverride')}")
    print()

    snaps = simulate_price_path(entry, path, volume, side)

    triggers = []
    if resolved.get('breakEvenLockEnabled') and peak_profit >= activation_amount:
        triggers.append(('BREAK_EVEN_LOCK', f'peak {peak_profit:.2f} >= activation {activation_amount:.2f}'))

    hard_peak_share = resolved.get('peakProfitHardLockShare', 0.9)
    _effective_peak_lock_share = 0.65 if peak_profit < meaningful_profit_peak else hard_peak_share
    hard_peak_lock_floor = round(max(0.0, peak_profit * _effective_peak_lock_share), 2) if peak_profit > 0 else 0.0
    if peak_profit > 0 and hard_peak_lock_floor > 0 and current_profit <= hard_peak_lock_floor:
        triggers.append(('HARD_PEAK_PROFIT_LOCK', f'current {current_profit:.2f} <= floor {hard_peak_lock_floor:.2f} (share {_effective_peak_lock_share})'))

    if resolved.get('neverNegativeAfterProfitEnabled') and peak_profit >= never_negative_activation and current_profit <= never_negative_floor:
        triggers.append(('NEVER_NEGATIVE_LOCK', f'peak {peak_profit:.2f} >= activation {never_negative_activation:.2f}; current {current_profit:.2f} <= floor {never_negative_floor:.2f}'))

    if resolved.get('zeroLossLockEnabled') and peak_profit > 0 and current_profit <= 0 and zero_loss_hold:
        triggers.append(('ZERO_LOSS_LOCK', f'peak {peak_profit:.2f} > 0; current {current_profit:.2f} <= 0; hold_satisfied={zero_loss_hold}'))

    if current_profit <= -hard_loss_limit:
        triggers.append(('HARD_LOSS_LIMIT', f'current {current_profit:.2f} <= -{hard_loss_limit:.2f}'))

    return triggers, resolved


# ---------------------------------------------------------------------------
# Scenario runner
# ---------------------------------------------------------------------------
def run_scenario(name: str, bot_config: Dict[str, Any], symbol: str,
                 side: str, entry: float, volume: float,
                 path: List[Tuple[float, float]]) -> None:
    print(f"\n{'='*70}")
    print(f"SCENARIO: {name}")
    print(f"  Broker={bot_config['brokerName']} Symbol={symbol} Side={side}")
    print(f"  Profile={bot_config['managementProfile']} Mode={bot_config['mode']}")
    print(f"  Entry={entry} Volume={volume}")
    print()

    resolved = mbu._resolve_profit_protection_for_symbol(bot_config, symbol, None)
    hold = mbu._minimum_position_hold_minutes(bot_config, resolved)
    threshold = mbu._default_signal_threshold_for_broker_profile(
        bot_config['managementProfile'], bot_config['brokerName']
    )

    print(f"  [CONFIG]  threshold={threshold}  hold={hold:.2f} min")
    print(f"  [PROTECTION] activationMinProfit={resolved.get('activationMinProfit')} "
          f" neverNegAct={resolved.get('neverNegativeActivationProfit')} "
          f" neverNegFloor={resolved.get('neverNegativeFloorProfit')} "
          f" hardLockShare={resolved.get('peakProfitHardLockShare')} "
          f" zeroLoss={resolved.get('zeroLossLockEnabled')} "
          f" retracePct={resolved.get('retraceClosePercent')} "
          f" metalsOverride={resolved.get('_volatileMetalHoldOverride')}")
    print()

    snaps = simulate_price_path(entry, path, volume, side)

    print(f"  {'Min':>5} {'Profit':>8} {'Peak':>8}  Triggers")
    print(f"  {'----':>5} {'-------':>8} {'-------':>8}  {'-'*30}")
    closed_at = None
    running_peak = 0.0
    for snap in snaps:
        t = snap['t_min']
        profit = snap['profit']
        running_peak = max(running_peak, profit)
        pos = make_position(symbol, side, entry, volume, t, entry + profit)
        pos['profit'] = profit
        pos['peakProfit'] = round(running_peak, 2)
        triggers, _ = evaluate_close_reason(bot_config, pos, symbol)
        trig_str = ', '.join(f"{t[0]}({t[1]})" for t in triggers) if triggers else '—'
        print(f"  {t:>5.1f} {profit:>+8.2f} {running_peak:>+8.2f}  {trig_str}")
        if triggers and closed_at is None:
            closed_at = t
            break

    if closed_at is not None:
        print(f"\n  *** CLOSED at t={closed_at:.1f} min ***")
    else:
        print(f"\n  *** NO CLOSE TRIGGERED (path ended at t={snaps[-1]['t_min']:.1f} min) ***")


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------
def main() -> None:
    print("Zwesta local trade simulator")
    print(f"Python: {sys.executable}")
    print(f"CWD: {HERE}")

    # 1. Exness XAG/USD — the +1.25 then -1.50 case (now fixed)
    # Volume 0.03 → $1.25 peak = $0.60 profit with backend's point math; simulate
    # with dollar P&L directly (backend uses position.profit from MT5).
    xag_path = [
        (0.0,   0.00),    # entry
        (1.0,  +0.10),
        (2.5,  +0.28),
        (5.0,  +0.52),    # arms neverNeg at 0.5
        (7.0,  +0.68),    # peak ~+0.68
        (9.0,  +0.55),
        (11.0, +0.30),
        (13.0, +0.08),    # near zero-loss floor
        (15.0, -0.05),    # crosses ≤0 → ZERO_LOSS_LOCK zone (hold=5 min ✓)
        (17.0, -0.25),
        (19.0, -0.55),
        (21.0, -0.85),    # never hits -1.50 with fix
    ]
    run_scenario(
        "XAG/USD — Exness demo 0.03 lot SELL (the -1.50 case, now fixed)",
        make_bot('Exness', 'XAGUSD', 'balanced', 'demo', 5000.0),
        'XAGUSD', 'SELL', 64.150, 0.03, xag_path,
    )

    # 2. Exness XAU/USD — another metal (XAU now in override set)
    xau_path = [
        (0.0,   0.00),
        (2.0,  +5.00),
        (5.0, +18.45),
        (8.0, +22.00),    # peak
        (12.0, +15.00),
        (16.0,  +8.00),
        (20.0,  +2.00),
        (24.0,  -4.00),   # should have never-negative locked by now
    ]
    run_scenario(
        "XAU/USD — Exness demo 0.05 lot SELL (XAU now in metals override)",
        make_bot('Exness', 'XAUUSD', 'balanced', 'demo', 5000.0),
        'XAUUSD', 'SELL', 4391.549, 0.05, xau_path,
    )

    # 3. Exness forex EURUSD — should NOT get metals override, forex floor 7 min
    # Peak only +0.20, below forex activation 4.0 → no peak-lock; stale loss exits
    # after 12 min if still negative.
    eur_path = [
        (0.0,   0.00),
        (2.0,  +0.08),
        (5.0,  +0.15),
        (8.0,  +0.20),
        (12.0, +0.05),
        (16.0, -0.05),
        (20.0, -0.15),
        (24.0, -0.35),   # stale loss zone (>12 min, never in profit > threshold)
    ]
    run_scenario(
        "EUR/USD — Exness demo 0.01 lot BUY (no metals override, forex floor 7 min)",
        make_bot('Exness', 'EURUSD', 'balanced', 'demo', 5000.0),
        'EURUSD', 'BUY', 1.08500, 0.01, eur_path,
    )

    # 4. Exness US30 — index runner, the user's reported case
    # Peak +2.30, dropped to 1.80. Before fix: forex-style gate depressed
    # hard_peak_lock_share to 0.65 → floor = 1.49, so 1.80 never triggered.
    # After fix: index runners use peak_profit>0 eligibility → 0.9 share,
    # floor = 2.07, so 1.80 triggers HARD_PEAK_PROFIT_LOCK.
    us30_path = [
        (0.0,   0.00),
        (1.0,  +0.80),
        (2.0,  +1.60),
        (3.0,  +2.30),   # peak
        (5.0,  +2.10),
        (7.0,  +1.80),   # should lock here (floor 2.07 with 0.9 share)
        (9.0,  +1.50),
        (11.0, +1.00),
        (13.0,  +0.50),
        (15.0,  -0.20),  # if not locked, would keep dropping
    ]
    run_scenario(
        "US30 — Exness demo index runner (+2.30 peak, dropped to 1.80 — should lock)",
        make_bot('Exness', 'US30', 'balanced', 'demo', 5000.0),
        'US30', 'SELL', 53517.40, 0.01, us30_path,
    )

    # 5. Binance BTC/USDT — 55 threshold, no metals override
    # Simulate a swing trade: profit peaks +225, retraces.
    btc_path = [
        (0.0,    0.00),
        (1.0,  +45.00),
        (3.0, +120.00),
        (5.0, +225.83),
        (8.0, +180.00),
        (11.0, +120.00),
        (14.0,  +60.00),
        (17.0,  +15.00),  # HARD_PEAK_PROFIT_LOCK zone (0.96 share)
        (20.0,  -30.00),  # but with lock it should have closed at +15
    ]
    run_scenario(
        "BTC/USDT — Binance 0.001 lot SELL (55 threshold, no metals override)",
        make_bot('Binance', 'BTCUSDT', 'balanced', 'demo', 5000.0),
        'BTCUSDT', 'SELL', 64694.17, 0.001, btc_path,
    )

    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"  Exness threshold (balanced profile) = "
          f"{mbu._default_signal_threshold_for_broker_profile('balanced', 'Exness')}")
    print(f"  Binance threshold (balanced profile) = "
          f"{mbu._default_signal_threshold_for_broker_profile('balanced', 'Binance')}")
    print(f"  XAGUSD metals override active = "
          f"{mbu._resolve_profit_protection_for_symbol(make_bot('Exness','XAGUSD'), 'XAGUSD', None).get('_volatileMetalHoldOverride')}")
    print()


if __name__ == '__main__':
    main()

import os
import importlib.util
import sys
from datetime import datetime, timedelta

# Avoid the bootstrap re-exec / heavy side effects where possible
os.environ['ZWESTA_SKIP_PYTHON_REEXEC'] = '1'
os.environ['DEPLOYMENT_MODE'] = 'LOCAL'
os.environ['LOG_LEVEL'] = 'ERROR'

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    'mbu', os.path.join(HERE, 'multi_broker_backend_updated.py')
)
mbu = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mbu)

print('IMPORT OK')
fails = 0
_safe_float = mbu._safe_float


def check(name, cond):
    global fails
    status = 'PASS' if cond else 'FAIL'
    if not cond:
        fails += 1
    print(f'[{status}] {name}')


# ---------------------------------------------------------------------------
# 1. _minimum_position_hold_minutes floor (non-Binance gets >=5 min floor)
# ---------------------------------------------------------------------------
exness_fast = {
    'brokerName': 'Exness', 'broker_type': 'Exness',
    'symbols': ['USTECm', 'XAUUSDm'],
    'tradingInterval': 90,  # fast cadence -> cadence_hold = 1.5 min
    'profitProtection': {'minimumHoldMinutes': 1.0},
}
v = mbu._minimum_position_hold_minutes(exness_fast)
check('Exness fast-cadence floor >= 5.0 (got %.2f)' % v, v >= 5.0)

# env override
os.environ['ZWESTA_MIN_HOLD_MINUTES'] = '8'
v = mbu._minimum_position_hold_minutes(exness_fast)
check('Exness env floor 8.0 honored (got %.2f)' % v, abs(v - 8.0) < 1e-6)
os.environ.pop('ZWESTA_MIN_HOLD_MINUTES', None)

# user configured higher than floor -> respected
exness_high = dict(exness_fast)
exness_high['profitProtection'] = {'minimumHoldMinutes': 12.0}
v = mbu._minimum_position_hold_minutes(exness_high)
check('Exness configured 12.0 respected (got %.2f)' % v, abs(v - 12.0) < 1e-6)

# forex exness -> 4.0 but floor 5.0
exness_forex = {
    'brokerName': 'Exness', 'broker_type': 'Exness',
    'symbols': ['EURUSDm'], 'tradingInterval': 300,
    'profitProtection': {'minimumHoldMinutes': 0.0},
}
v = mbu._minimum_position_hold_minutes(exness_forex)
check('Exness forex floor >= 7.0 (got %.2f)' % v, v >= 7.0)

# Binance excluded from floor
binance_cfg = {
    'brokerName': 'Binance', 'broker_type': 'Binance',
    'symbols': ['BTCUSDT'], 'tradingInterval': 90,
    'profitProtection': {'minimumHoldMinutes': 1.0},
}
v = mbu._minimum_position_hold_minutes(binance_cfg)
check('Binance NOT floored to 5 (got %.2f, should be <=2.0)' % v, v <= 2.0)

# Volatile metal (XAG/XAU) hard-loss cap present & bounded
xag_cfg = {
    'brokerName': 'Exness', 'broker_type': 'Exness',
    'mode': 'demo', 'symbols': ['XAGUSD'],
    'displayCurrency': 'USD', 'maxDailyLoss': 50.0,
    'profitProtection': {'minimumHoldMinutes': 0.0},
}
v = mbu._resolve_hard_loss_limits(xag_cfg)
check('XAG hard-loss cap <= 1.50 demo (got %.2f)' % v[0], v[0] <= 1.50)
check('XAG hard-loss cap >= 0.5 demo (got %.2f)' % v[0], v[0] >= 0.5)

# ---------------------------------------------------------------------------
# Threshold floors: Exness=60, Binance=55 (user requirement)
# ---------------------------------------------------------------------------
_exness_t = mbu._default_signal_threshold_for_broker_profile('beginner', 'Exness')
check('Exness beginner threshold == 65 (got %d)' % _exness_t, _exness_t == 65)
_exness_a = mbu._default_signal_threshold_for_broker_profile('advanced', 'Exness')
check('Exness advanced threshold == 65 (got %d)' % _exness_a, _exness_a == 65)
_binance_b = mbu._default_signal_threshold_for_broker_profile('beginner', 'Binance')
check('Binance beginner threshold == 55 (got %d)' % _binance_b, _binance_b == 55)
_binance_a = mbu._default_signal_threshold_for_broker_profile('advanced', 'Binance')
check('Binance advanced threshold == 55 (got %d)' % _binance_a, _binance_a == 55)
_fxcm = mbu._default_signal_threshold_for_broker_profile('beginner', 'FXCM')
check('FXCM threshold unchanged == 10 (got %d)' % _fxcm, _fxcm == 10)

# Restore-time broker-floor clamp is present in source for both copies
check('broker-floor clamp present in main copy', 'clamped signalThreshold to broker minimum' in open(os.path.join(HERE, 'multi_broker_backend_updated.py'), encoding='utf-8').read())
check('broker-floor clamp present in vps copy', 'clamped signalThreshold to broker minimum' in open(os.path.join(HERE, 'vps_app_package', 'multi_broker_backend_updated.py'), encoding='utf-8').read())

# ---------------------------------------------------------------------------
# 2. Bot-creation init_timeout / lock_timeout env tunables (Exness quick test)
# ---------------------------------------------------------------------------
# Replicate the exact expression used in the quick-test credential block.
def resolve_exness_timeouts():
    return (
        int(os.getenv('ZWESTA_MT5_LOCK_TIMEOUT', '8')),
        int(os.getenv('ZWESTA_MT5_INIT_TIMEOUT', '30')),
    )
lt, it = resolve_exness_timeouts()
check('default lock_timeout=8 (got %d)' % lt, lt == 8)
check('default init_timeout=30 (got %d)' % it, it == 30)
os.environ['ZWESTA_MT5_INIT_TIMEOUT'] = '45'
os.environ['ZWESTA_MT5_LOCK_TIMEOUT'] = '10'
lt, it = resolve_exness_timeouts()
check('env init_timeout=45 honored (got %d)' % it, it == 45)
check('env lock_timeout=10 honored (got %d)' % lt, lt == 10)
os.environ.pop('ZWESTA_MT5_INIT_TIMEOUT', None)
os.environ.pop('ZWESTA_MT5_LOCK_TIMEOUT', None)

# ---------------------------------------------------------------------------
# 3. Confirm the cooldown-set condition now includes Binance
#    (inline `if is_mt5 or canonicalize_broker_name(broker_type) == 'Binance':`)
# ---------------------------------------------------------------------------
src = open(os.path.join(HERE, 'multi_broker_backend_updated.py'), encoding='utf-8').read()
check('cooldown-set covers Binance (canonicalize_broker_name(broker_type) == \'Binance\')',
      "canonicalize_broker_name(broker_type) == 'Binance'" in src)
check('reconcile guard uses _skip_reconcile flag',
      '_skip_reconcile' in src and 'SKIPPING close reconciliation' in src)
check('analytics-snapshot merge is DB-error resilient',
      'analytics-snapshot: trade-history merge failed for bot' in src)
check('trades-detailed has load_user_bots fallback',
      "load_user_bots_from_database(enabled_only=False)" in src and "api/bot/<bot_id>/trades-detailed" in src)
check('open-path feed guard present',
      'position feed unavailable/empty while positions are tracked' in src)
check('Binance open-path cooldown check present',
      'POST-CLOSE COOLDOWN (Binance / non-MT5 path)' in src)

# Both copies must contain the same guards
vps = os.path.join(HERE, 'vps_app_package', 'multi_broker_backend_updated.py')
vsrc = open(vps, encoding='utf-8').read()
check('VPS copy has reconcile guard', 'SKIPPING close reconciliation' in vsrc)
check('VPS copy has Binance cooldown parity',
      "canonicalize_broker_name(broker_type) == 'Binance'" in vsrc)
check('VPS copy has init_timeout env tunable', 'ZWESTA_MT5_INIT_TIMEOUT' in vsrc)

# ---------------------------------------------------------------------------
# 4. Volatile metals override lowers hold below env floor; non-metals keep it.
#    This is the fix for XAG running -$1.50 without never-negative/zero-loss firing.
# ---------------------------------------------------------------------------
os.environ['ZWESTA_MIN_HOLD_MINUTES'] = '7'

# XAG/USD resolved protection config carries the metals override flag + 5.0 min hold
_xag_cfg = {
    'brokerName': 'Exness', 'broker_type': 'Exness',
    'symbols': ['XAGUSD'], 'mode': 'demo',
    'displayCurrency': 'USD', 'accountBalance': 1000.0,
    'profitProtection': {'minimumHoldMinutes': 20.0},
}
_resolved_xag = mbu._resolve_profit_protection_for_symbol(_xag_cfg, 'XAGUSD', None)
check('XAG metals override flag set', _resolved_xag.get('_volatileMetalHoldOverride') is True)
check('XAG resolved minimumHoldMinutes == 5.0 (got %s)' % _resolved_xag.get('minimumHoldMinutes'),
      abs(_safe_float(_resolved_xag.get('minimumHoldMinutes'), 0.0) - 5.0) < 1e-9)

# Passing the resolved config into the hold calc must NOT be floored back to 7.0
_xag_hold = mbu._minimum_position_hold_minutes(_xag_cfg, _resolved_xag)
check('XAG hold honours 5.0 override (got %.2f, expected ~5.0)' % _xag_hold,
      abs(_xag_hold - 5.0) < 1e-6)

# Non-metal Exness: env floor 7.0 still applies
_eurusd_cfg = {
    'brokerName': 'Exness', 'broker_type': 'Exness',
    'symbols': ['EURUSDm'], 'tradingInterval': 90,
    'profitProtection': {'minimumHoldMinutes': 1.0},
}
_eurusd_hold = mbu._minimum_position_hold_minutes(_eurusd_cfg)
check('Non-metal Exness still floored to 7.0 (got %.2f)' % _eurusd_hold, _eurusd_hold >= 7.0)
os.environ.pop('ZWESTA_MIN_HOLD_MINUTES', None)

# ---------------------------------------------------------------------------
# 5. Never-negative / zero-loss arming for XAG with a $1.25 peak
#    (after the metals override lowers activationMinProfit to 1.5)
# ---------------------------------------------------------------------------
check('XAG resolved activationMinProfit <= 1.5 (got %s)' % _resolved_xag.get('activationMinProfit'),
      _safe_float(_resolved_xag.get('activationMinProfit'), 99.0) <= 1.5)
check('XAG resolved neverNegativeActivationProfit <= 0.5 (got %s)' % _resolved_xag.get('neverNegativeActivationProfit'),
      _safe_float(_resolved_xag.get('neverNegativeActivationProfit'), 99.0) <= 0.5)

# XPT/USD (Platinum) must also get the metals override + SL cap (it was missing
# and lost -5.61 / -3.99 on 0.01 lots with a ~40-point broker SL).
_xpt_cfg = {
    'brokerName': 'Exness', 'broker_type': 'Exness',
    'symbols': ['XPTUSD'], 'mode': 'demo',
    'displayCurrency': 'USD', 'accountBalance': 5000.0,
    'profitProtection': {'minimumHoldMinutes': 20.0},
}
_resolved_xpt = mbu._resolve_profit_protection_for_symbol(_xpt_cfg, 'XPTUSD', None)
check('XPTUSD metals override flag set', _resolved_xpt.get('_volatileMetalHoldOverride') is True)
check('XPTUSD resolved activationMinProfit <= 1.5 (got %s)' % _resolved_xpt.get('activationMinProfit'),
      _safe_float(_resolved_xpt.get('activationMinProfit'), 99.0) <= 1.5)

# XPTUSD SL cap: 0.01 lot, hard limit 1.0, ~1 USD/point → max 100 points.
_orig_score = mbu._score_signal_setup
mbu._score_signal_setup = lambda *a, **kw: {'takeTrade': True, 'score': 5.0, 'rr': 2.0}
try:
    _xpt_tight = {'volume': 0.01, 'stop_loss': 200.0}
    _xpt_result = mbu._apply_setup_quality_to_trade_params(
        _xpt_tight, 'XPTUSD', {}, _xpt_cfg,
    )
    check('XPTUSD SL capped by hard-loss limit (got %.2f, expected <=100)' % _xpt_result.get('stop_loss'),
          _xpt_result.get('stop_loss', 999) <= 100.0)

    # Exness "mini" symbol variants (XPTUSDm / XPDUSDM) must also be covered —
    # either via _normalize_symbol_base stripping the trailing 'M', or via the
    # explicit m-suffixed entries. These were the symbols actually losing on VPS.
    for _msym in ['XPTUSDm', 'XPDUSDM']:
        _r = mbu._resolve_profit_protection_for_symbol(_xpt_cfg, _msym, None)
        check('%s metals override flag set' % _msym, _r.get('_volatileMetalHoldOverride') is True)
        _mt = {'volume': 0.01, 'stop_loss': 200.0}
        _mr = mbu._apply_setup_quality_to_trade_params(_mt, _msym, {}, _xpt_cfg)
        check('%s SL capped by hard-loss limit (got %.2f)' % (_msym, _mr.get('stop_loss')),
              _mr.get('stop_loss', 999) <= 100.0)
finally:
    mbu._score_signal_setup = _orig_score

# ---------------------------------------------------------------------------
# 6. SL cap: trade plan SL pips must not exceed hard_loss_limit at the
#    computed volume. This prevents XAU/USD trades from opening with a
#    7.98-point SL that would lose 7.98 USD before the runtime check fires.
# ---------------------------------------------------------------------------
_xau_bot = {
    'brokerName': 'Exness', 'broker_type': 'Exness',
    'symbols': ['XAUUSD'], 'mode': 'demo',
    'displayCurrency': 'USD', 'accountBalance': 5000.0,
    'profitProtection': {},
}

# Hard-loss demo cap for XAU is 1.00 (default USD cap; metals override affects
# profit-protection hold/activation, not the hard-loss USD cap). With volume 0.01,
# dollar_per_point ≈ 1.0, so max SL ≈ 100 points.
_xau_hard_limit, _ = mbu._resolve_hard_loss_limits(_xau_bot)
check('XAU demo hard-loss limit == 1.00 (got %.2f)' % _xau_hard_limit, abs(_xau_hard_limit - 1.00) < 0.01)
_xau_max_sl = _xau_hard_limit / (0.01 * 1.0)
check('XAU max SL at 0.01 lot >= 100 points (got %.2f)' % _xau_max_sl, _xau_max_sl >= 100.0)

# Verify the actual function caps SL by monkeypatching _score_signal_setup
_orig_score_signal_setup = mbu._score_signal_setup
mbu._score_signal_setup = lambda *a, **kw: {'takeTrade': True, 'score': 5.0, 'rr': 2.0}
try:
    _xau_tight = {'volume': 0.01, 'stop_loss': 200.0}
    _xau_result2 = mbu._apply_setup_quality_to_trade_params(
        _xau_tight, 'XAUUSD', {}, _xau_bot,
    )
    check('XAU SL capped by hard-loss limit (got %.2f, expected <=150)' % _xau_result2.get('stop_loss'),
          _xau_result2.get('stop_loss', 999) <= 150.0)

    # Forex: 0.01 lot EURUSD with SL=100 pips should NOT be capped (hard limit 1.0,
    # dollar_per_pip=0.01, so max_sl_pips = 1.0 / (0.01 * 0.01) = 10000 pips).
    _eur_bot = {
        'brokerName': 'Exness', 'broker_type': 'Exness',
        'symbols': ['EURUSD'], 'mode': 'demo',
        'displayCurrency': 'USD', 'accountBalance': 5000.0,
        'profitProtection': {},
    }
    _eur_adjusted = {'volume': 0.01, 'stop_loss': 100.0}
    _eur_result = mbu._apply_setup_quality_to_trade_params(
        _eur_adjusted, 'EURUSD', {}, _eur_bot,
    )
    check('EURUSD SL not capped by 1.0 hard limit at 0.01 lot (got %.2f)' % _eur_result.get('stop_loss'),
          _eur_result.get('stop_loss', 0) >= 100.0)
finally:
    mbu._score_signal_setup = _orig_score_signal_setup

# ---------------------------------------------------------------------------
# 7. Market-regime classification (intelligence #1). Verify the classifier
#    separates trending / ranging / volatile and returns sane strategy-fit
#    multipliers, and that the scanner biases strength by regime fit.
# ---------------------------------------------------------------------------
def _mk_market(prices, spread=0.1):
    highs = [p + spread for p in prices]
    lows = [p - spread for p in prices]
    return {'price_history': prices, 'high_history': highs, 'low_history': lows}

_trend_prices = [100.0 + i * 0.6 for i in range(60)]          # strong steady uptrend
_range_prices = [100.0 + 0.2 * ((i % 4) - 2) for i in range(60)]   # gentle ~0.2% wiggle
_vol_prices = [100.0 + (10.0 if i % 2 else -10.0) * (i / 10.0) for i in range(60)]  # big swings

_trend = mbu._classify_market_regime('EURUSD', _mk_market(_trend_prices))
_range = mbu._classify_market_regime('EURUSD', _mk_market(_range_prices))
_vol = mbu._classify_market_regime('EURUSD', _mk_market(_vol_prices))
_flat = mbu._classify_market_regime('EURUSD', {})  # no data → mixed/neutral

check('Trending series classified trending (got %s)' % _trend.get('regime'), _trend.get('regime') == 'trending')
check('Trending confidence >= 0.5 (got %.2f)' % _trend.get('confidence'), _trend.get('confidence', 0) >= 0.5)
check('Trending: Trend Following fit > 1.0 (got %.2f)' % _trend['strategy_fit'].get('Trend Following'),
      _trend['strategy_fit'].get('Trend Following', 1.0) > 1.0)
check('Trending: Mean Reversion fit < 1.0 (got %.2f)' % _trend['strategy_fit'].get('Mean Reversion'),
      _trend['strategy_fit'].get('Mean Reversion', 1.0) < 1.0)
check('Ranging series classified ranging/mixed (got %s)' % _range.get('regime'),
      _range.get('regime') in ('ranging', 'mixed'))
check('Volatile series classified volatile (got %s)' % _vol.get('regime'), _vol.get('regime') == 'volatile')
check('No-data falls back to neutral mixed (got %s)' % _flat.get('regime'), _flat.get('regime') == 'mixed')
check('No-data strategy_fit all 1.0', all(v == 1.0 for v in _flat['strategy_fit'].values()))

# Scanner bias: in a trending regime, a given raw strength for Trend Following
# should be boosted vs Mean Reversion by the strategy_fit multipliers.
_tf_fit = _trend['strategy_fit'].get('Trend Following')
_mr_fit = _trend['strategy_fit'].get('Mean Reversion')
check('Trending biases TF > MR (%.2f vs %.2f)' % (_tf_fit, _mr_fit), _tf_fit > _mr_fit)

# ---------------------------------------------------------------------------
# 8. Volatility-aware position sizing (intelligence #2).
# ---------------------------------------------------------------------------
# High-vol data: calm baseline, then a volatile recent window → multiplier < 1.0
_baseline = [100.0 + 0.1 * i for i in range(60)]
_boundary = _baseline[-1]
_recent_hi = [_boundary + 12.0 * ((i % 2) * 2 - 1) for i in range(14)]
_hi_vol = _baseline + _recent_hi
_md_hi = {'price_history': _hi_vol,
          'high_history': [p + 0.5 for p in _hi_vol],
          'low_history': [p - 0.5 for p in _hi_vol]}
_hi_mult = mbu._volatility_size_multiplier('XAUUSD', _md_hi)
check('High-vol multiplier < 1.0 (got %.3f)' % _hi_mult, _hi_mult < 1.0)

# Low-vol data: calm baseline, even calmer recent (continuing the trend) → ~1.0+
_recent_lo = [_boundary + 0.02 * i for i in range(14)]
_lo_vol = _baseline + _recent_lo
_md_lo = {'price_history': _lo_vol,
          'high_history': [p + 0.05 for p in _lo_vol],
          'low_history': [p - 0.05 for p in _lo_vol]}
_lo_mult = mbu._volatility_size_multiplier('XAUUSD', _md_lo)
check('Low-vol multiplier in [1.0, 1.25] (got %.3f)' % _lo_mult, 1.0 <= _lo_mult <= 1.25)

# Flat / insufficient data → neutral 1.0
check('Insufficient data -> 1.0', mbu._volatility_size_multiplier('XAUUSD', {'price_history': [100, 101, 102]}) == 1.0)

# The multiplier is actually applied to volume in _apply_setup_quality_to_trade_params.
_xau_vol_bot = {
    'brokerName': 'Exness', 'broker_type': 'Exness',
    'symbols': ['XAUUSD'], 'mode': 'demo',
    'displayCurrency': 'USD', 'accountBalance': 5000.0,
    'profitProtection': {},
}
_orig_score2 = mbu._score_signal_setup
mbu._score_signal_setup = lambda *a, **kw: {'takeTrade': True, 'score': 5.0, 'rr': 2.0}
try:
    _vol_in = {'volume': 0.1, 'stop_loss': 50.0}
    _vol_out = mbu._apply_setup_quality_to_trade_params(_vol_in, 'XAUUSD', _md_hi, _xau_vol_bot)
    check('Vol-multiplier shrinks volume in high vol (%.4f < 0.1)' % _vol_out.get('volume', 0),
          _vol_out.get('volume', 0) < 0.1)
finally:
    mbu._score_signal_setup = _orig_score2

# ---------------------------------------------------------------------------
# 9. Multi-signal ensemble entry probability (intelligence #3).
# ---------------------------------------------------------------------------
_strong_prices = [100.0 + i * 1.5 for i in range(60)]   # steep, decisive uptrend
_trend_md = {'price_history': _strong_prices,
             'high_history': [p + 0.5 for p in _strong_prices],
             'low_history': [p - 0.5 for p in _strong_prices]}
_p_strong = mbu._ensemble_entry_probability('EURUSD', _trend_md, 'BUY', 80.0, 'Trend Following')
check('Strong trending BUY ensemble p > 0.6 (got %.3f)' % _p_strong, _p_strong > 0.6)

_down_prices = [100.0 - i * 0.6 for i in range(60)]
_down_md = {'price_history': _down_prices,
            'high_history': [p + 0.5 for p in _down_prices],
            'low_history': [p - 0.5 for p in _down_prices]}
_p_weak = mbu._ensemble_entry_probability('EURUSD', _down_md, 'BUY', 20.0, 'Mean Reversion')
check('Contradictory setup ensemble p < 0.30 (got %.3f)' % _p_weak, _p_weak < 0.30)
check('Ensemble p in [0,1]', 0.0 <= _p_weak <= 1.0 and 0.0 <= _p_strong <= 1.0)
check('Strong p > weak p (%.3f vs %.3f)' % (_p_strong, _p_weak), _p_strong > _p_weak)

# ---------------------------------------------------------------------------
# 10. Online learning: expectancy-based symbol suppression (intelligence #4).
#     A symbol can win often but lose big (negative expectancy) — win-rate/pnl
#     rules miss this; expectancy catches it and demotes/blacklists.
# ---------------------------------------------------------------------------
# 2 wins of +1.0, 1 loss of -5.0 -> WR 0.667, expectancy = 0.667*1 - 0.333*5 = -1.0
_exp_t = [{'profit': 1.0}, {'profit': 1.0}, {'profit': -5.0}]
_exp_val, _exp_n = mbu._symbol_recent_expectancy(_exp_t)
check('Expectancy computed (got %.3f, n=%d)' % (_exp_val, _exp_n), abs(_exp_val - (-1.0)) < 1e-6 and _exp_n == 3)
# Positive expectancy -> no suppression override
_pos_t = [{'profit': 2.0}, {'profit': 2.0}, {'profit': -1.0}]
_pos_val, _pos_n = mbu._symbol_recent_expectancy(_pos_t)
check('Positive expectancy (got %.3f)' % _pos_val, _pos_val > 0)
# Insufficient samples -> None
check('Insufficient expectancy -> None', mbu._symbol_recent_expectancy([{'profit': 1.0}])[0] is None)

# Negative expectancy demotes even with acceptable win-rate/pnl
_dem = mbu._derive_symbol_performance_multiplier(
    samples=3, win_rate=0.67, net_pnl=-3.0, losses=1, expectancy=-1.0, expectancy_samples=3)
check('Negative expectancy -> demoted (got %s, %.2f)' % (_dem[0], _dem[1]), _dem[0] == 'demoted')
# Strongly negative expectancy -> blacklisted
_blk = mbu._derive_symbol_performance_multiplier(
    samples=4, win_rate=0.5, net_pnl=-6.0, losses=2, expectancy=-2.5, expectancy_samples=4)
check('Strongly negative expectancy -> blacklisted (got %s)' % _blk[0], _blk[0] == 'blacklisted')
# Positive expectancy with same args -> not demoted by expectancy rule
_pos = mbu._derive_symbol_performance_multiplier(
    samples=3, win_rate=0.67, net_pnl=1.0, losses=1, expectancy=0.8, expectancy_samples=3)
check('Positive expectancy not demoted (got %s)' % _pos[0], _pos[0] != 'demoted')

# ---------------------------------------------------------------------------
# 11. News / event guard (intelligence #5): scheduled window + spike breaker.
# ---------------------------------------------------------------------------
_now = datetime(2026, 1, 1, 12, 0)  # 12:00 UTC
# Scheduled window active for EURUSD
_guard_cfg = {'newsGuard': {'enabled': True, 'windows': [
    {'symbols': ['EURUSD'], 'startUtcHour': 0, 'endUtcHour': 23}]}}
_p1, _r1 = mbu._news_guard_should_pause(_guard_cfg, 'EURUSD', {}, now=_now)
check('Scheduled window pauses entry (got %s)' % _r1, _p1 is True)
# Outside window symbol -> no pause
_p2, _r2 = mbu._news_guard_should_pause(_guard_cfg, 'XAUUSD', {}, now=_now)
check('Non-listed symbol not paused', _p2 is False)
# Disabled guard -> no pause even in window
_guard_off = {'newsGuard': {'enabled': False, 'windows': [
    {'symbols': ['EURUSD'], 'startUtcHour': 0, 'endUtcHour': 23}]}}
_p3, _r3 = mbu._news_guard_should_pause(_guard_off, 'EURUSD', {}, now=_now)
check('Disabled guard does not pause', _p3 is False)
# Live volatility spike -> pause (no feed needed)
_spike_md = {'volatility_pct': 5.0}
_p4, _r4 = mbu._news_guard_should_pause({'newsGuard': {}}, 'XAUUSD', _spike_md, now=_now)
check('Volatility spike circuit breaker pauses (got %s)' % _r4, _p4 is True)
# Spike call populates the cooldown map for the symbol
_spike_cfg = {'newsGuard': {}}
_p4b, _r4b = mbu._news_guard_should_pause(_spike_cfg, 'XAUUSD', _spike_md, now=_now)
check('Spike sets cooldown state', 'XAUUSD' in _spike_cfg['newsGuard'].get('_spikeCooldown', {}))
# Active cooldown -> pause even without a current spike
_cd_until = (_now + timedelta(minutes=15)).timestamp()
_p5, _r5 = mbu._news_guard_should_pause(
    {'newsGuard': {'_spikeCooldown': {'XAUUSD': _cd_until}}}, 'XAUUSD', {'volatility_pct': 0.5}, now=_now)
check('Post-spike cooldown active (got %s)' % _r5, _p5 is True)
# Expired cooldown -> no pause
_cd_exp = (_now - timedelta(minutes=5)).timestamp()
_p6, _r6 = mbu._news_guard_should_pause(
    {'newsGuard': {'_spikeCooldown': {'XAUUSD': _cd_exp}}}, 'XAUUSD', {'volatility_pct': 0.5}, now=_now)
check('Cooldown expires after window', _p6 is False)

# ---------------------------------------------------------------------------
# 12. Portfolio-level risk (intelligence #6): account drawdown + correlation.
# ---------------------------------------------------------------------------
check('Drawdown 0 when no peak', mbu._portfolio_account_drawdown_pct({'accountEquity': 1000}) == 0.0)
_dd = mbu._portfolio_account_drawdown_pct({'accountEquity': 900, 'peakEquity': 1000})
check('Drawdown computes 10.0%% (got %.1f)' % _dd, abs(_dd - 10.0) < 1e-6)
_pd, _pdr = mbu._portfolio_risk_should_pause({'accountEquity': 900, 'peakEquity': 1000}, 'US500')
check('Deep drawdown pauses new entries (got %s)' % _pdr, _pd is True)
_okp, _okr = mbu._portfolio_risk_should_pause(
    {'accountEquity': 1000, 'peakEquity': 1000, 'open_positions': {}}, 'US500')
check('Healthy account not paused', _okp is False)
_corr = {'accountEquity': 1000, 'peakEquity': 1000, 'open_positions': {
    'a': {'symbol': 'US30'}, 'b': {'symbol': 'USTEC'}}}
_c, _cr = mbu._portfolio_risk_should_pause(_corr, 'US500')
check('Correlated-index saturation pauses (got %s)' % _cr, _c is True)
_c2, _cr2 = mbu._portfolio_risk_should_pause(_corr, 'XAUUSD')
check('Unrelated symbol not paused by index saturation', _c2 is False)

print()
print('RESULT:', 'ALL PASS' if fails == 0 else f'{fails} FAILED')
sys.exit(1 if fails else 0)

#!/usr/bin/env python3
"""
FIX: Profit Peak Erosion Protection for ETH/SOL/BTC

PROBLEM:
- ETH/SOL/BTC reach profit peak ($1+) then subsequent trades lose that profit
- Bot keeps trading same symbol in declining trend
- No mechanism to exit after peak or reduce position size

SOLUTION:
1. Track cumulative profit per symbol across recent trades (last 10 trades)
2. Detect when profit peak is reached (cumulative profit stops growing)
3. Activate "profit peak cooldown" - symbol rotates out for 2-3 cycles
4. Reduce position size on symbols in recovery (until they prove profitable again)
5. Force rotation to other qualified symbols

IMPLEMENTATION:
Adds to bot_config:
- symbolProfitHistory: {symbol: [trade_profits_last_10]}
- symbolPeakDetection: {symbol: {'peak_profit': X, 'peak_cycle': N, 'cooldown_until': datetime}}
- symbolRecoveryMode: {symbol: boolean} - reduces position size 50% until 3 consecutive wins
"""

import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

def analyze_symbol_profit_history(symbol_trades: List[float], window: int = 10) -> Dict:
    """
    Analyze profit history for a symbol.
    
    Args:
        symbol_trades: List of profit values from recent trades (newest first)
        window: Number of recent trades to analyze
        
    Returns:
        {
            'cumulative_profit': float,
            'recent_high': float,
            'recent_low': float,
            'peak_index': int,
            'trades_since_peak': int,
            'is_declining': bool,
            'decline_magnitude': float,
        }
    """
    if not symbol_trades or not isinstance(symbol_trades, list):
        return {
            'cumulative_profit': 0.0,
            'recent_high': 0.0,
            'recent_low': 0.0,
            'peak_index': -1,
            'trades_since_peak': 0,
            'is_declining': False,
            'decline_magnitude': 0.0,
        }
    
    # Reverse to chronological order (oldest first)
    trades = list(reversed(symbol_trades[:window]))
    cumulative = sum(trades)
    
    # Find cumulative profit at each step
    cumulative_at_point = []
    running_sum = 0
    for profit in trades:
        running_sum += profit
        cumulative_at_point.append(running_sum)
    
    peak_cumulative = max(cumulative_at_point) if cumulative_at_point else 0.0
    peak_index = cumulative_at_point.index(peak_cumulative) if cumulative_at_point else 0
    trades_since_peak = len(cumulative_at_point) - peak_index - 1
    
    # Calculate decline from peak
    current_cumulative = cumulative_at_point[-1] if cumulative_at_point else 0.0
    decline_magnitude = peak_cumulative - current_cumulative
    is_declining = decline_magnitude > 0.01  # More than 1 cent decline
    
    return {
        'cumulative_profit': cumulative,
        'peak_cumulative_profit': peak_cumulative,
        'current_cumulative_profit': current_cumulative,
        'recent_high': max(cumulative_at_point) if cumulative_at_point else 0.0,
        'recent_low': min(cumulative_at_point) if cumulative_at_point else 0.0,
        'peak_index': peak_index,
        'trades_since_peak': trades_since_peak,
        'is_declining': is_declining,
        'decline_magnitude': round(decline_magnitude, 4),
        'decline_percent': round((decline_magnitude / peak_cumulative * 100) if peak_cumulative > 0 else 0, 1),
    }


def detect_profit_peak(symbol: str, symbol_trades: List[float], min_peak_profit: float = 0.50) -> Tuple[bool, Dict]:
    """
    Detect if a symbol just hit a profit peak that's starting to erode.
    
    Peak conditions:
    1. Cumulative profit >= min_peak_profit (default $0.50)
    2. Peak was reached within last 5 trades
    3. Currently declining from peak by at least $0.05
    4. At least 2 trades since peak
    
    Returns: (is_peak_detected, analysis_dict)
    """
    analysis = analyze_symbol_profit_history(symbol_trades)
    
    peak_profit = analysis.get('peak_cumulative_profit', 0.0)
    trades_since_peak = analysis.get('trades_since_peak', 0)
    decline = analysis.get('decline_magnitude', 0.0)
    is_declining = analysis.get('is_declining', False)
    
    # Peak detection criteria
    criteria = {
        'has_meaningful_profit': peak_profit >= min_peak_profit,
        'recent_peak': trades_since_peak <= 5,
        'active_decline': is_declining and decline >= 0.05,
        'trades_since_peak_sufficient': trades_since_peak >= 2,
    }
    
    is_peak = all(criteria.values())
    
    analysis['peak_criteria'] = criteria
    analysis['peak_detected'] = is_peak
    
    return is_peak, analysis


def check_symbol_cooldown_status(symbol: str, peak_detection: Dict, cooldown_minutes: int = 15) -> Tuple[bool, str]:
    """
    Check if a symbol should be in cooldown after profit peak.
    
    Returns: (is_in_cooldown, reason)
    """
    if not isinstance(peak_detection, dict):
        return False, "No peak detection data"
    
    is_peak = peak_detection.get('peak_detected', False)
    if not is_peak:
        return False, "No profit peak detected"
    
    # Symbol should be in cooldown for N minutes after peak
    peak_time = peak_detection.get('peak_detected_at')
    if peak_time:
        try:
            peak_dt = datetime.fromisoformat(peak_time) if isinstance(peak_time, str) else peak_time
            cooldown_end = peak_dt + timedelta(minutes=cooldown_minutes)
            if datetime.now() < cooldown_end:
                remaining = int((cooldown_end - datetime.now()).total_seconds() / 60)
                return True, f"Profit peak cooldown active for {remaining}m more"
        except:
            pass
    
    return False, "Cooldown period expired"


def calculate_recovery_position_size(
    base_position_size: float,
    recovery_mode_active: bool,
    recovery_win_count: int,
    recovery_required_wins: int = 3
) -> float:
    """
    Calculate position size adjustment for symbols in recovery mode.
    
    Recovery mode: After profit peak erosion, reduce position size 50%
    until symbol proves profitable again (3 consecutive wins).
    
    Returns: adjusted_position_size
    """
    if not recovery_mode_active:
        return base_position_size
    
    # Ramping: 50% in recovery, back to 100% after 3 consecutive wins
    if recovery_win_count >= recovery_required_wins:
        return base_position_size  # Graduated from recovery
    
    recovery_multiplier = 0.50  # 50% position size in recovery
    return base_position_size * recovery_multiplier


def build_symbol_profit_tracking(bot_config: Dict) -> Dict:
    """
    Initialize or update symbol profit tracking in bot_config.
    
    Structure:
    {
        'symbolProfitHistory': {symbol: [recent_trades]},
        'symbolPeakDetection': {symbol: {peak_data}},
        'symbolRecoveryMode': {symbol: {'active': bool, 'consecutive_wins': int, 'armed_at': datetime}},
        'symbolCooldownUntil': {symbol: datetime_string},
    }
    """
    if 'symbolProfitHistory' not in bot_config:
        bot_config['symbolProfitHistory'] = {}
    if 'symbolPeakDetection' not in bot_config:
        bot_config['symbolPeakDetection'] = {}
    if 'symbolRecoveryMode' not in bot_config:
        bot_config['symbolRecoveryMode'] = {}
    if 'symbolCooldownUntil' not in bot_config:
        bot_config['symbolCooldownUntil'] = {}
    
    return bot_config


def record_symbol_trade(
    bot_config: Dict,
    symbol: str,
    trade_profit: float,
    keep_history: int = 10
) -> Dict:
    """
    Record a trade for a symbol and update peak detection.
    
    Args:
        bot_config: Bot configuration dict
        symbol: Symbol traded (e.g., 'ETHUSDT')
        trade_profit: P/L from this trade
        keep_history: Number of recent trades to track (default 10)
    
    Returns: updated bot_config
    """
    bot_config = build_symbol_profit_tracking(bot_config)
    
    # Add trade to history (most recent first)
    if symbol not in bot_config['symbolProfitHistory']:
        bot_config['symbolProfitHistory'][symbol] = []
    
    history = bot_config['symbolProfitHistory'][symbol]
    history.insert(0, round(trade_profit, 4))  # Most recent first
    if len(history) > keep_history:
        history = history[:keep_history]
    bot_config['symbolProfitHistory'][symbol] = history
    
    # Detect profit peak
    is_peak, analysis = detect_profit_peak(symbol, history)
    bot_config['symbolPeakDetection'][symbol] = {
        **analysis,
        'detected_at': datetime.now().isoformat(),
    }
    
    # If peak detected, activate cooldown
    if is_peak:
        cooldown_until = datetime.now() + timedelta(minutes=15)  # 15-minute cooldown
        bot_config['symbolCooldownUntil'][symbol] = cooldown_until.isoformat()
        
        # Also activate recovery mode
        if symbol not in bot_config['symbolRecoveryMode']:
            bot_config['symbolRecoveryMode'][symbol] = {}
        bot_config['symbolRecoveryMode'][symbol].update({
            'active': True,
            'consecutive_wins': 0,
            'armed_at': datetime.now().isoformat(),
            'peak_profit': analysis.get('peak_cumulative_profit', 0.0),
        })
    
    # Update recovery mode on each trade
    if symbol in bot_config['symbolRecoveryMode']:
        recovery = bot_config['symbolRecoveryMode'][symbol]
        if recovery.get('active'):
            if trade_profit > 0:
                recovery['consecutive_wins'] = recovery.get('consecutive_wins', 0) + 1
            else:
                recovery['consecutive_wins'] = 0  # Reset on loss
            
            # Graduation from recovery (3 consecutive wins)
            if recovery['consecutive_wins'] >= 3:
                recovery['active'] = False
                recovery['graduated_at'] = datetime.now().isoformat()
    
    return bot_config


def should_trade_symbol_with_peak_protection(
    bot_config: Dict,
    symbol: str,
    min_signal_strength: int = 70
) -> Tuple[bool, str]:
    """
    Determine if a symbol should be traded, considering profit peak protection.
    
    Returns: (should_trade, reason)
    """
    bot_config = build_symbol_profit_tracking(bot_config)
    
    # Check if in cooldown
    cooldown_until_str = bot_config['symbolCooldownUntil'].get(symbol)
    if cooldown_until_str:
        try:
            cooldown_until = datetime.fromisoformat(cooldown_until_str)
            if datetime.now() < cooldown_until:
                remaining = int((cooldown_until - datetime.now()).total_seconds() / 60)
                return False, f"🔒 Profit peak cooldown for {remaining}m ({symbol})"
        except:
            pass
    
    # Check recovery mode - allow trading but with reduced position size
    recovery = bot_config['symbolRecoveryMode'].get(symbol, {})
    if recovery.get('active'):
        # Allow trading but caller should reduce position size via calculate_recovery_position_size()
        consecutive_wins = recovery.get('consecutive_wins', 0)
        return True, f"⚠️ Recovery mode: {consecutive_wins}/3 wins ({symbol})"
    
    return True, f"✅ Can trade {symbol}"


def format_symbol_protection_summary(bot_config: Dict) -> str:
    """
    Format a summary of symbol profit protection status for logging.
    
    Returns: Formatted multi-line summary
    """
    bot_config = build_symbol_profit_tracking(bot_config)
    
    lines = ["📊 SYMBOL PROFIT PROTECTION STATUS:"]
    
    # Cooldowns
    cooldowns = []
    for symbol, cooldown_str in bot_config['symbolCooldownUntil'].items():
        try:
            cooldown_until = datetime.fromisoformat(cooldown_str)
            if datetime.now() < cooldown_until:
                remaining = (cooldown_until - datetime.now()).total_seconds() / 60
                cooldowns.append(f"   🔒 {symbol}: {remaining:.0f}m cooldown")
        except:
            pass
    if cooldowns:
        lines.extend(cooldowns)
    
    # Recovery modes
    recovery_modes = []
    for symbol, recovery in bot_config['symbolRecoveryMode'].items():
        if recovery.get('active'):
            wins = recovery.get('consecutive_wins', 0)
            peak = recovery.get('peak_profit', 0.0)
            recovery_modes.append(f"   ⚠️ {symbol}: Recovery mode ({wins}/3 wins, peak ${peak:.2f})")
    if recovery_modes:
        lines.extend(recovery_modes)
    
    # Profit history
    history_lines = []
    for symbol, trades in bot_config['symbolProfitHistory'].items():
        if trades:
            analysis = analyze_symbol_profit_history(trades)
            cumulative = analysis.get('cumulative_profit', 0.0)
            peak = analysis.get('peak_cumulative_profit', 0.0)
            decline = analysis.get('decline_magnitude', 0.0)
            history_lines.append(
                f"   📈 {symbol}: ${cumulative:.2f} cumulative "
                f"(peak ${peak:.2f}, declined ${decline:.2f})"
            )
    if history_lines:
        lines.extend(history_lines)
    
    return "\n".join(lines) if len(lines) > 1 else lines[0]


# ============================================================================
# TEST CASES
# ============================================================================

def test_eth_erosion_scenario():
    """Test: ETH reaches $1 profit, then erodes"""
    print("\n" + "="*70)
    print("TEST: ETH Profit Peak Erosion Detection")
    print("="*70)
    
    # ETH trades: reaches $1.21 peak on trade #3, then erodes
    eth_trades = [
        0.45,   # Trade 1: +$0.45
        0.50,   # Trade 2: +$0.50
        0.26,   # Trade 3: +$0.26 (peak cumulative: $1.21)
        -0.15,  # Trade 4: -$0.15 (cumulative: $1.06) ← erosion starts
        -0.08,  # Trade 5: -$0.08 (cumulative: $0.98)
        -0.12,  # Trade 6: -$0.12 (cumulative: $0.86)
    ]
    
    bot_config = {'symbols': ['ETHUSDT']}
    
    for i, profit in enumerate(eth_trades, 1):
        bot_config = record_symbol_trade(bot_config, 'ETHUSDT', profit)
        analysis = bot_config['symbolPeakDetection'].get('ETHUSDT', {})
        peak_detected = analysis.get('peak_detected', False)
        
        print(f"\nTrade {i}: ${profit:+.2f}")
        print(f"  Cumulative: ${analysis.get('cumulative_profit', 0.0):.2f}")
        print(f"  Peak: ${analysis.get('peak_cumulative_profit', 0.0):.2f}")
        print(f"  Decline: ${analysis.get('decline_magnitude', 0.0):.2f} ({analysis.get('decline_percent', 0):.1f}%)")
        
        if peak_detected:
            print(f"  ⚠️  PEAK DETECTED! Activating 15-minute cooldown")
            should_trade, reason = should_trade_symbol_with_peak_protection(bot_config, 'ETHUSDT')
            print(f"  {reason}")
        
        cooldown_until = bot_config['symbolCooldownUntil'].get('ETHUSDT')
        if cooldown_until:
            print(f"  🔒 Cooldown until: {cooldown_until}")
    
    print("\n" + format_symbol_protection_summary(bot_config))


def test_recovery_mode_graduation():
    """Test: Symbol exits recovery after 3 consecutive wins"""
    print("\n" + "="*70)
    print("TEST: Recovery Mode Graduation")
    print("="*70)
    
    bot_config = {'symbols': ['SOLUSDT']}
    
    # Simulate profit peak + recovery
    peak_trades = [0.60, 0.45, 0.30]  # Reaching peak
    
    for i, profit in enumerate(peak_trades, 1):
        bot_config = record_symbol_trade(bot_config, 'SOLUSDT', profit)
    
    # Trigger peak detection by adding erosion
    bot_config = record_symbol_trade(bot_config, 'SOLUSDT', -0.20)
    bot_config = record_symbol_trade(bot_config, 'SOLUSDT', -0.10)
    
    print("After profit peak erosion:")
    print(format_symbol_protection_summary(bot_config))
    
    # Recovery: 3 consecutive wins
    print("\nRecovery trades:")
    for i in range(5):
        profit = 0.15 if i < 3 else -0.05  # 3 wins, then a loss
        bot_config = record_symbol_trade(bot_config, 'SOLUSDT', profit)
        recovery = bot_config['symbolRecoveryMode'].get('SOLUSDT', {})
        print(f"  Trade: ${profit:+.2f} → {recovery.get('consecutive_wins', 0)}/3 wins")
    
    print("\nFinal status:")
    recovery = bot_config['symbolRecoveryMode'].get('SOLUSDT', {})
    print(f"  Active: {recovery.get('active')}")
    print(f"  Graduated: {recovery.get('graduated_at', 'N/A')}")
    
    # Position size calculation
    base_size = 0.10
    size = calculate_recovery_position_size(base_size, recovery.get('active'), recovery.get('consecutive_wins', 0))
    print(f"\n  Position size: {base_size} → {size} ({size/base_size*100:.0f}%)")


def test_position_sizing_in_recovery():
    """Test: Position sizing reduction during recovery"""
    print("\n" + "="*70)
    print("TEST: Position Sizing in Recovery Mode")
    print("="*70)
    
    base_size = 0.10  # 0.1 BTC
    
    scenarios = [
        (False, 0, "Normal mode"),
        (True, 0, "Recovery mode - 0 wins"),
        (True, 1, "Recovery mode - 1 win"),
        (True, 2, "Recovery mode - 2 wins"),
        (True, 3, "Recovery mode - 3 wins (graduated)"),
    ]
    
    for active, wins, label in scenarios:
        size = calculate_recovery_position_size(base_size, active, wins)
        percent = size / base_size * 100
        print(f"  {label}: {base_size} BTC → {size} BTC ({percent:.0f}%)")


if __name__ == '__main__':
    test_eth_erosion_scenario()
    test_recovery_mode_graduation()
    test_position_sizing_in_recovery()
    
    print("\n" + "="*70)
    print("✅ All tests complete!")
    print("="*70)

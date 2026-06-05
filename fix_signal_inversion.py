#!/usr/bin/env python3
"""
Fix for Exness flash trading / signal inversion
Prevents new bots from trading in wrong direction
"""

import json
from datetime import datetime
import shutil

STATUS_FILE = 'bot_status.json'

SIGNAL_INVERSION_FIXES = {
    # ========================================================================
    # SIGNAL QUALITY GATES
    # ========================================================================
    
    # Reject junk signals (below commission cost)
    'signalThreshold': 75,  # HIGH bar: require 75/100 quality
    
    # Don't accept micro-signals that cause flash trades
    'minimumSignalStrength': 0.75,
    'minimumConfidenceInterval': 0.85,
    
    # ========================================================================
    # POSITION HOLDING & FLASH TRADE PREVENTION
    # ========================================================================
    
    # Minimum time to hold position (prevents flash close)
    'minimumHoldTimeSeconds': 60,  # At least 1 minute
    'minimumHoldTimeMinutes': 2,   # Better: 2 minutes
    
    # Close ONLY on real signals, not noise
    'exitSignalThreshold': 72,  # Same high bar for exit
    
    # Don't trade during high volatility (causes whipsaws)
    'maxAllowedVolatility': ['Very Low', 'Low'],  # Skip Medium+ volatility
    'volatilityCheckMinutes': 5,
    
    # ========================================================================
    # POSITION SIZING & STOP LOSS
    # ========================================================================
    
    # Small positions = small losses if wrong direction
    'tradeAmount': 0.5,  # 0.5 lots only
    'maxLotSize': 0.1,   # Cap per position
    
    # Hard stop loss (cut losses quick if inverted)
    'stopLossPercentage': 1.0,
    'hardStopLossPercentPerTrade': 1.5,  # 1.5% max loss
    
    # ========================================================================
    # ANTI-INVERSION LOGIC
    # ========================================================================
    
    # Validate signals before entering
    'signalValidationEnabled': True,
    'requireMultipleIndicatorConfirmation': True,
    'minimumIndicatorsInAgreement': 2,  # Need 2+ signals aligned
    
    # Detect if signals are backwards
    'detectedSignalInversionCheck': True,
    'checkPreviousDirectionContinuity': True,
    
    # If winning trades go opposite direction, reverse it
    'autoDetectAndCorrectSignalInversion': True,
    
    # ========================================================================
    # POSITION HOLDING (FIX FOR "DOESN'T HOLD")
    # ========================================================================
    
    # HOLD positions through minor pullbacks
    'breakEvenEnabled': True,  # Move SL to breakeven
    'breakEvenTriggerProfit': 0.5,  # After 0.5% profit
    
    # DON'T close on every tiny reversal
    'trailingStopEnabled': False,  # Too aggressive
    'partialCloseEnabled': False,  # Don't close half position
    'fullPositionCloseOnly': True,  # Hold full or close full
    
    # ========================================================================
    # ANTI-FLASH-TRADE LOGIC
    # ========================================================================
    
    # No trading within X seconds of last trade close
    'postCloseCooldownMinutes': 120,  # 2 hour cooldown
    'minTimeBetweenTradesSeconds': 300,  # 5 min minimum
    
    # Rate limiting
    'maxTradesPerHour': 5,  # Only 5 trades per hour max
    'maxTradesPerDay': 15,  # Only 15 per day
    
    # ========================================================================
    # RECOVERY MODE
    # ========================================================================
    
    # After 3 losses, wait longer before next trade
    'lossStreakPauseAfter': 3,
    'lossStreakPauseMinutes': 60,
    
    # After 5 losses, STOP for the day
    'lossStreakHardPauseAfter': 5,
    'lossStreakHardPauseMinutes': 480,  # 8 hours
}

def apply_signal_inversion_fixes():
    """Apply signal inversion prevention to all Exness bots"""
    
    # Backup
    backup = f"{STATUS_FILE}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy(STATUS_FILE, backup)
    print(f"💾 Backed up to: {backup}\n")
    
    # Load bots
    with open(STATUS_FILE, 'r') as f:
        data = json.load(f)
    
    exness_bots = [b for b in data.get('bots', []) if b.get('broker_type') == 'Exness']
    
    print("=" * 70)
    print("APPLYING SIGNAL INVERSION PREVENTION FIXES")
    print("=" * 70)
    print()
    
    for bot in exness_bots:
        bot_id = bot['botId']
        
        # Apply fixes
        for key, value in SIGNAL_INVERSION_FIXES.items():
            bot[key] = value
        
        print(f"✓ {bot_id}")
        print(f"  Signal Threshold: {bot['signalThreshold']} (reject weak signals)")
        print(f"  Min Hold Time: {bot['minimumHoldTimeMinutes']} min (prevent flash close)")
        print(f"  Position Size: {bot['tradeAmount']} lots (small losses if inverted)")
        print(f"  Max Trades/Hour: {bot['maxTradesPerHour']} (limit frequency)")
        print(f"  Post-Close Cooldown: {bot['postCloseCooldownMinutes']} min (wait between trades)")
        print(f"  Signal Validation: ENABLED (check before entering)")
        print()
    
    # Save
    with open(STATUS_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    print("=" * 70)
    print("✅ SIGNAL INVERSION PREVENTION APPLIED")
    print("=" * 70)
    print()
    print("Bots will now:")
    print("  ✓ REJECT weak signals (< 75 quality)")
    print("  ✓ HOLD positions minimum 2 minutes")
    print("  ✓ VALIDATE signals before entering")
    print("  ✓ LIMIT to 5 trades per hour")
    print("  ✓ PAUSE 2 hours after each close")
    print("  ✓ STOP after 5 consecutive losses")
    print()
    print("This prevents:")
    print("  ✗ Flash trading (rapid entry/exit)")
    print("  ✗ Signal inversion (wrong direction)")
    print("  ✗ Over-trading (too many positions)")
    print("  ✗ Heavy losses from junk signals")
    print()

if __name__ == '__main__':
    apply_signal_inversion_fixes()

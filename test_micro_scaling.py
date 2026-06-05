# Test automatic scaling from lowest to highest amounts
test_balances_usd = [
    10, 25, 50, 100, 500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000, 10000000
]

# Currency conversion
usd_to_zar = 18.5

LIVE_CAPITAL_SAFETY_BANDS = [
    {
        'name': 'sovereign_guard',
        'min_zar': 1_000_000_000,
        'dailyLossPct': 0.003,
    },
    {
        'name': 'ultra_institutional_guard',
        'min_zar': 100_000_000,
        'dailyLossPct': 0.004,
    },
    {
        'name': 'enterprise_guard',
        'min_zar': 10_000_000,
        'dailyLossPct': 0.005,
    },
    {
        'name': 'institutional_guard',
        'min_zar': 1_000_000,
        'dailyLossPct': 0.008,
    },
    {
        'name': 'ultra_high_guard',
        'min_zar': 500_000,
        'dailyLossPct': 0.010,
    },
    {
        'name': 'high_guard',
        'min_zar': 200_000,
        'dailyLossPct': 0.0125,
    },
    {
        'name': 'growth_guard',
        'min_zar': 100_000,
        'dailyLossPct': 0.015,
    },
    {
        'name': 'scaled_guard',
        'min_zar': 50_000,
        'dailyLossPct': 0.0175,
    },
    {
        'name': 'starter_large_guard',
        'min_zar': 20_000,
        'dailyLossPct': 0.020,
    },
    {
        'name': 'micro_guard',  # NEW - catches all small accounts
        'min_zar': 0,
        'dailyLossPct': 0.025,
    },
]

def get_safety_band(balance_zar):
    for band in LIVE_CAPITAL_SAFETY_BANDS:
        if balance_zar >= float(band['min_zar']):
            return band
    return None

print("✅ AUTOMATIC SCALING BY BALANCE\n")
print("Balance (USD) | Balance (ZAR) | Safety Band            | Daily Loss % | Daily Loss Limit")
print("=" * 95)

for usd in test_balances_usd:
    zar = usd * usd_to_zar
    band = get_safety_band(zar)
    daily_loss_pct = band['dailyLossPct'] * 100
    daily_loss_amount = usd * band['dailyLossPct']
    
    print(f"${usd:>6} ({usd:>5}%) | {zar:>11,.0f} | {band['name']:<22} | {daily_loss_pct:>11.2f}% | ${daily_loss_amount:>8.2f}")

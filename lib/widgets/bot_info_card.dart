import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Enhanced bot information card showing comprehensive metrics
/// Displays: invested vs equity, ROI, time-based performance, alerts
class BotInfoCard extends StatelessWidget {
  final Map<String, dynamic> bot;
  final VoidCallback? onTap;
  final VoidCallback? onViewAnalytics;
  final VoidCallback? onPauseResume;

  const BotInfoCard({
    Key? key,
    required this.bot,
    this.onTap,
    this.onViewAnalytics,
    this.onPauseResume,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final botId = bot['botId'] ?? 'Unknown Bot';
    final isEnabled = bot['enabled'] == true;
    final balance = ((bot['balance'] ?? 0) as num).toDouble();
    final invested = ((bot['invested'] ?? 0) as num).toDouble();
    final equity = ((bot['equity'] ?? balance) as num).toDouble();
    final profit = ((bot['profit'] ?? 0) as num).toDouble();
    final allTimeProfit = ((bot['allTimeProfit'] ?? profit) as num).toDouble();
    final trades = (bot['trades'] ?? 0) as int;
    final winRate = ((bot['winRate'] ?? 0) as num).toDouble();
    final roi = invested > 0 ? ((equity - invested) / invested * 100) : 0.0;
    final displayCurrency = (bot['displayCurrency'] ?? bot['currency'] ?? 'USD').toString();
    final errorMessage = bot['error_message']?.toString();
    final hasError = errorMessage != null && errorMessage.isNotEmpty;

    // Calculate performance indicators
    final isProfit = profit >= 0;
    final profitColor = isProfit ? const Color(0xFF69F0AE) : const Color(0xFFFF8A80);
    final roiColor = roi >= 0 ? const Color(0xFF69F0AE) : const Color(0xFFFF8A80);

    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 16),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              const Color(0xFF1A1F3A).withOpacity(0.95),
              const Color(0xFF0A0E21).withOpacity(0.95),
            ],
          ),
          borderRadius: BorderRadius.circular(18),
          border: Border.all(
            color: isEnabled
                ? const Color(0xFF00E5FF).withOpacity(0.3)
                : Colors.white.withOpacity(0.1),
            width: 1.5,
          ),
          boxShadow: [
            BoxShadow(
              color: isEnabled
                  ? const Color(0xFF00E5FF).withOpacity(0.15)
                  : Colors.black.withOpacity(0.2),
              blurRadius: 12,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.03),
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(18),
                  topRight: Radius.circular(18),
                ),
              ),
              child: Row(
                children: [
                  // Bot status indicator
                  Container(
                    width: 12,
                    height: 12,
                    decoration: BoxDecoration(
                      color: isEnabled ? const Color(0xFF69F0AE) : Colors.grey,
                      shape: BoxShape.circle,
                      boxShadow: [
                        BoxShadow(
                          color: isEnabled
                              ? const Color(0xFF69F0AE).withOpacity(0.5)
                              : Colors.transparent,
                          blurRadius: 8,
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 12),

                  // Bot name and strategy
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          botId,
                          style: GoogleFonts.poppins(
                            color: Colors.white,
                            fontSize: 16,
                            fontWeight: FontWeight.w700,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        Text(
                          bot['strategy'] ?? 'Trend Following',
                          style: GoogleFonts.poppins(
                            color: Colors.white60,
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ),

                  // Quick action buttons
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      if (onPauseResume != null)
                        IconButton(
                          onPressed: onPauseResume,
                          icon: Icon(
                            isEnabled ? Icons.pause_circle : Icons.play_circle,
                            color: const Color(0xFF00E5FF),
                          ),
                          padding: EdgeInsets.zero,
                          constraints: const BoxConstraints(),
                        ),
                      if (onViewAnalytics != null) ...[
                        const SizedBox(width: 8),
                        IconButton(
                          onPressed: onViewAnalytics,
                          icon: const Icon(
                            Icons.analytics_outlined,
                            color: Color(0xFFFFA726),
                          ),
                          padding: EdgeInsets.zero,
                          constraints: const BoxConstraints(),
                        ),
                      ],
                    ],
                  ),
                ],
              ),
            ),

            // Error Alert (if any)
            if (hasError)
              Container(
                margin: const EdgeInsets.fromLTRB(16, 12, 16, 0),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: const Color(0xFFFF8A80).withOpacity(0.1),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(
                    color: const Color(0xFFFF8A80).withOpacity(0.3),
                  ),
                ),
                child: Row(
                  children: [
                    const Icon(
                      Icons.info_outline,
                      color: Color(0xFFFF8A80),
                      size: 18,
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        errorMessage,
                        style: GoogleFonts.poppins(
                          color: const Color(0xFFFF8A80),
                          fontSize: 11,
                          height: 1.3,
                        ),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
              ),

            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  // Invested vs Equity Comparison
                  if (invested > 0) ...[
                    Row(
                      children: [
                        Expanded(
                          child: _buildMetricCard(
                            'Invested',
                            _formatMoney(invested, displayCurrency),
                            Colors.white70,
                            Icons.money,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: _buildMetricCard(
                            'Current',
                            _formatMoney(equity, displayCurrency),
                            equity >= invested
                                ? const Color(0xFF69F0AE)
                                : const Color(0xFFFF8A80),
                            Icons.account_balance_wallet,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),

                    // ROI Bar
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: roiColor.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(
                          color: roiColor.withOpacity(0.3),
                        ),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Row(
                            children: [
                              Icon(
                                roi >= 0
                                    ? Icons.trending_up
                                    : Icons.trending_down,
                                color: roiColor,
                                size: 18,
                              ),
                              const SizedBox(width: 8),
                              Text(
                                'ROI',
                                style: GoogleFonts.poppins(
                                  color: Colors.white70,
                                  fontSize: 12,
                                ),
                              ),
                            ],
                          ),
                          Text(
                            '${roi >= 0 ? '+' : ''}${roi.toStringAsFixed(1)}%',
                            style: GoogleFonts.poppins(
                              color: roiColor,
                              fontSize: 16,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 12),
                  ],

                  // Performance Grid
                  Row(
                    children: [
                      Expanded(
                        child: _buildStatBox(
                          'All-Time P/L',
                          _formatMoney(allTimeProfit, displayCurrency),
                          profitColor,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: _buildStatBox(
                          'Session P/L',
                          _formatMoney(profit, displayCurrency),
                          profitColor,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),

                  Row(
                    children: [
                      Expanded(
                        child: _buildStatBox(
                          'Total Trades',
                          trades.toString(),
                          const Color(0xFF00E5FF),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: _buildStatBox(
                          'Win Rate',
                          '${winRate.toStringAsFixed(1)}%',
                          winRate >= 50
                              ? const Color(0xFF69F0AE)
                              : const Color(0xFFFFA726),
                        ),
                      ),
                    ],
                  ),

                  // Performance Indicator
                  const SizedBox(height: 12),
                  _buildPerformanceBar(winRate),

                  // Quick Stats Row
                  const SizedBox(height: 12),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      _buildQuickStat(
                        'Balance',
                        _formatMoney(balance, displayCurrency),
                        Colors.white70,
                      ),
                      Container(
                        width: 1,
                        height: 24,
                        color: Colors.white12,
                      ),
                      _buildQuickStat(
                        'Running',
                        bot['runtime'] ?? '0h',
                        const Color(0xFF00E5FF),
                      ),
                      Container(
                        width: 1,
                        height: 24,
                        color: Colors.white12,
                      ),
                      _buildQuickStat(
                        'Status',
                        isEnabled ? 'ACTIVE' : 'PAUSED',
                        isEnabled
                            ? const Color(0xFF69F0AE)
                            : const Color(0xFFFFA726),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMetricCard(
    String label,
    String value,
    Color color,
    IconData icon,
  ) =>
      Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: color.withOpacity(0.08),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(
            color: color.withOpacity(0.2),
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, color: color, size: 14),
                const SizedBox(width: 6),
                Text(
                  label,
                  style: GoogleFonts.poppins(
                    color: Colors.white60,
                    fontSize: 10,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              value,
              style: GoogleFonts.poppins(
                color: color,
                fontSize: 14,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ),
      );

  Widget _buildStatBox(String label, String value, Color color) => Container(
        padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 12),
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.03),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: Colors.white.withOpacity(0.08),
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              label,
              style: GoogleFonts.poppins(
                color: Colors.white60,
                fontSize: 10,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              value,
              style: GoogleFonts.poppins(
                color: color,
                fontSize: 14,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ),
      );

  Widget _buildPerformanceBar(double winRate) {
    final performanceLevel = winRate >= 70
        ? 'Excellent'
        : winRate >= 60
            ? 'Good'
            : winRate >= 50
                ? 'Average'
                : 'Needs Improvement';
    final barColor = winRate >= 60
        ? const Color(0xFF69F0AE)
        : winRate >= 50
            ? const Color(0xFFFFA726)
            : const Color(0xFFFF8A80);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              'Performance',
              style: GoogleFonts.poppins(
                color: Colors.white70,
                fontSize: 11,
              ),
            ),
            Text(
              performanceLevel,
              style: GoogleFonts.poppins(
                color: barColor,
                fontSize: 11,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
        const SizedBox(height: 6),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: LinearProgressIndicator(
            value: winRate / 100,
            backgroundColor: Colors.white.withOpacity(0.1),
            valueColor: AlwaysStoppedAnimation<Color>(barColor),
            minHeight: 6,
          ),
        ),
      ],
    );
  }

  Widget _buildQuickStat(String label, String value, Color color) => Column(
        children: [
          Text(
            label,
            style: GoogleFonts.poppins(
              color: Colors.white60,
              fontSize: 9,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            value,
            style: GoogleFonts.poppins(
              color: color,
              fontSize: 11,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      );

  String _formatMoney(double amount, String currency) {
    final symbol = currency == 'ZAR'
        ? 'R'
        : currency == 'GBP'
            ? 'GBP'
            : r'$';
    final prefix = amount >= 0 ? '' : '-';
    return '$prefix$symbol${amount.abs().toStringAsFixed(2)}';
  }
}

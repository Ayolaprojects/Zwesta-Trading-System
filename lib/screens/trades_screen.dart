import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:http/http.dart' as http;
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../models/trade.dart';
import '../services/trading_service.dart';
import '../utils/constants.dart';
import '../utils/environment_config.dart';
import '../widgets/custom_widgets.dart';
import 'broker_integration_screen.dart';

class TradesScreen extends StatefulWidget {
  const TradesScreen({Key? key}) : super(key: key);

  @override
  State<TradesScreen> createState() => _TradesScreenState();
}

class _TradesScreenState extends State<TradesScreen> {
  int _selectedTab = 0; // 0: all, 1: open, 2: closed

  @override
  Widget build(BuildContext context) => Scaffold(
        extendBodyBehindAppBar: true,
        appBar: CustomAppBar(
          title: 'Trades',
          showBackButton: true,
          showLogo: false,
          actions: [
            IconButton(
              icon: const Icon(Icons.add),
              onPressed: () => _showOpenTradeDialog(context),
            ),
          ],
        ),
        body: Container(
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [Color(0xFF0A0E21), Color(0xFF1A237E), Color(0xFF512DA8)],
            ),
          ),
          child: _buildTradesContent(),
        ),
      );

  Widget _buildTradesContent() => Consumer<TradingService>(
        builder: (context, tradingService, _) => SafeArea(
          child: Column(
            children: [
              // Connected broker banner
              FutureBuilder<SharedPreferences>(
                future: SharedPreferences.getInstance(),
                builder: (ctx, snap) {
                  if (!snap.hasData) return const SizedBox.shrink();
                  final prefs = snap.data!;
                  final broker = prefs.getString('broker');
                  final connected = prefs.getBool('broker_connected') == true;
                  return GestureDetector(
                    onTap: () => Navigator.push(
                        context,
                        MaterialPageRoute(
                            builder: (_) => const BrokerIntegrationScreen())),
                    child: Container(
                      margin: const EdgeInsets.fromLTRB(16, 8, 16, 0),
                      padding: const EdgeInsets.symmetric(
                          horizontal: 14, vertical: 10),
                      decoration: BoxDecoration(
                        color: connected
                            ? Colors.green.withOpacity(0.1)
                            : Colors.orange.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(
                            color: connected
                                ? Colors.green.withOpacity(0.3)
                                : Colors.orange.withOpacity(0.3)),
                      ),
                      child: Row(
                        children: [
                          Icon(connected ? Icons.link : Icons.link_off,
                              color: connected ? Colors.green : Colors.orange,
                              size: 18),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Text(
                              connected
                                  ? 'Connected to ${broker ?? "Broker"}'
                                  : 'No broker connected',
                              style: GoogleFonts.poppins(
                                  color:
                                      connected ? Colors.green : Colors.orange,
                                  fontSize: 12,
                                  fontWeight: FontWeight.w500),
                            ),
                          ),
                          Text('Manage',
                              style: GoogleFonts.poppins(
                                  color: AppColors.primaryColor,
                                  fontSize: 11,
                                  fontWeight: FontWeight.w600)),
                          const SizedBox(width: 4),
                          const Icon(Icons.chevron_right,
                              color: AppColors.primaryColor, size: 16),
                        ],
                      ),
                    ),
                  );
                },
              ),

              // Live Positions Indicator
              Container(
                margin: const EdgeInsets.fromLTRB(16, 8, 16, 0),
                padding:
                    const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(
                  color: const Color(0xFF00E5FF).withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                      color: const Color(0xFF00E5FF).withOpacity(0.3)),
                ),
                child: Row(
                  children: [
                    Container(
                      width: 6,
                      height: 6,
                      decoration: const BoxDecoration(
                        shape: BoxShape.circle,
                        color: Color(0xFF00E5FF),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'Live MT5 positions • Auto-refreshing every 30 seconds',
                        style: GoogleFonts.poppins(
                          color: const Color(0xFF00E5FF),
                          fontSize: 11,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                    const Icon(Icons.update,
                        color: Color(0xFF00E5FF), size: 16),
                  ],
                ),
              ),

              // Account Balance Card
              Container(
                margin: const EdgeInsets.fromLTRB(16, 12, 16, 0),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [
                      const Color(0xFF1A237E).withOpacity(0.5),
                      const Color(0xFF0D47A1).withOpacity(0.3),
                    ],
                  ),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                      color: const Color(0xFF00E5FF).withOpacity(0.2)),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceAround,
                  children: [
                    _buildAccountMetric('Account Balance',
                        tradingService.accountBalance, Colors.white),
                    Container(
                        width: 1,
                        height: 40,
                        color: Colors.white.withOpacity(0.1)),
                    _buildAccountMetric('Equity', tradingService.accountEquity,
                        const Color(0xFF69F0AE)),
                    Container(
                        width: 1,
                        height: 40,
                        color: Colors.white.withOpacity(0.1)),
                    _buildAccountMetric('Free Margin',
                        tradingService.freeMargin, const Color(0xFF00E5FF)),
                  ],
                ),
              ),

              // Tab Selector
              Container(
                padding: const EdgeInsets.all(AppSpacing.md),
                child: Row(
                  children: [
                    _buildTabButton(
                      context,
                      'All',
                      0,
                      '${tradingService.trades.length}',
                    ),
                    const SizedBox(width: AppSpacing.md),
                    _buildTabButton(
                      context,
                      'Open',
                      1,
                      '${tradingService.activeTrades.length}',
                    ),
                    const SizedBox(width: AppSpacing.md),
                    _buildTabButton(
                      context,
                      'Closed',
                      2,
                      '${tradingService.closedTrades.length}',
                    ),
                    const SizedBox(width: AppSpacing.md),
                    _buildTabButton(
                      context,
                      'Live MT5',
                      3,
                      '${tradingService.liveOpenPositions.length}',
                    ),
                  ],
                ),
              ),

              // Trades List
              Expanded(
                child: RefreshIndicator(
                  onRefresh: () async {
                    await tradingService.fetchTrades();
                  },
                  child: _buildTradesList(context, tradingService),
                ),
              ),
            ],
          ),
        ),
      );

  Widget _buildAccountMetric(String label, double value, Color color) => Column(
        children: [
          Text(
            label,
            style: GoogleFonts.poppins(color: Colors.white60, fontSize: 10),
          ),
          const SizedBox(height: 4),
          Text(
            'R${value.toStringAsFixed(2)}',
            style: GoogleFonts.poppins(
              color: color,
              fontSize: 14,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      );

  Widget _buildLivePositionCard(BuildContext context, Trade position) {
    final symbol = position.symbol;
    final type = position.type == TradeType.buy ? 'BUY' : 'SELL';
    final volume = position.quantity;
    final openPrice = position.entryPrice;
    final currentPrice = position.currentPrice ?? position.entryPrice;
    final profit = position.profit ?? 0.0;
    final profitPct =
        openPrice > 0 ? ((currentPrice - openPrice) / openPrice * 100) : 0.0;
    final openTime = position.openedAt.toString().split('.')[0];

    final isBuy = position.type == TradeType.buy;
    final isProfitable = profit >= 0;
    // Derive currency prefix from the trade's currency field
    final currencyCode = position.currency.toUpperCase();
    final currencyPrefix = currencyCode == 'ZAR' ? 'R'
        : currencyCode == 'USD' ? r'$'
        : currencyCode == 'EUR' ? '\u20AC'
        : currencyCode == 'GBP' ? '\u00A3'
        : '$currencyCode ';
    // Prices for Binance USDT pairs are in USD; no R prefix needed
    final pricePrefix = currencyCode == 'ZAR' ? 'R' : '';
    final priceSuffix = currencyCode != 'ZAR' && currencyCode != 'USD' && currencyCode != 'EUR' && currencyCode != 'GBP' ? ' $currencyCode' : '';

    return Card(
      color: Colors.white.withOpacity(0.05),
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: isProfitable
                ? const Color(0xFF69F0AE).withOpacity(0.3)
                : const Color(0xFFFF8A80).withOpacity(0.3),
          ),
        ),
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: const Color(0xFF00E5FF).withOpacity(0.2),
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(
                        color: const Color(0xFF00E5FF).withOpacity(0.4)),
                  ),
                  child: Text(
                    'LIVE',
                    style: GoogleFonts.poppins(
                      color: const Color(0xFF00E5FF),
                      fontSize: 10,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    symbol,
                    style: GoogleFonts.poppins(
                      color: Colors.white,
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: isBuy
                        ? const Color(0xFF1B5E20).withOpacity(0.2)
                        : const Color(0xFFB71C1C).withOpacity(0.2),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    type,
                    style: GoogleFonts.poppins(
                      color: isBuy
                          ? const Color(0xFF69F0AE)
                          : const Color(0xFFFF8A80),
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Volume',
                        style: GoogleFonts.poppins(
                            color: Colors.white60, fontSize: 10)),
                    Text('$volume lots',
                        style: GoogleFonts.poppins(
                            color: Colors.white,
                            fontSize: 13,
                            fontWeight: FontWeight.w500)),
                  ],
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text('Open Price',
                        style: GoogleFonts.poppins(
                            color: Colors.white60, fontSize: 10)),
                    Text('$pricePrefix${openPrice.toStringAsFixed(5)}$priceSuffix',
                        style: GoogleFonts.poppins(
                            color: Colors.white,
                            fontSize: 13,
                            fontWeight: FontWeight.w500)),
                  ],
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text('Current Price',
                        style: GoogleFonts.poppins(
                            color: Colors.white60, fontSize: 10)),
                    Text('$pricePrefix${currentPrice.toStringAsFixed(5)}$priceSuffix',
                        style: GoogleFonts.poppins(
                            color: const Color(0xFF00E5FF),
                            fontSize: 13,
                            fontWeight: FontWeight.w500)),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: isProfitable
                    ? const Color(0xFF69F0AE).withOpacity(0.1)
                    : const Color(0xFFFF8A80).withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(
                  color: isProfitable
                      ? const Color(0xFF69F0AE).withOpacity(0.3)
                      : const Color(0xFFFF8A80).withOpacity(0.3),
                ),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      Icon(
                        isProfitable ? Icons.trending_up : Icons.trending_down,
                        color: isProfitable
                            ? const Color(0xFF69F0AE)
                            : const Color(0xFFFF8A80),
                        size: 18,
                      ),
                      const SizedBox(width: 8),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('P/L',
                              style: GoogleFonts.poppins(
                                  color: Colors.white60, fontSize: 10)),
                          Text(
                            '${isProfitable ? '+' : ''}$currencyPrefix${profit.toStringAsFixed(2)}',
                            style: GoogleFonts.poppins(
                              color: isProfitable
                                  ? const Color(0xFF69F0AE)
                                  : const Color(0xFFFF8A80),
                              fontSize: 14,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                  Text(
                    '${isProfitable ? '+' : ''}${profitPct.toStringAsFixed(2)}%',
                    style: GoogleFonts.poppins(
                      color: isProfitable
                          ? const Color(0xFF69F0AE)
                          : const Color(0xFFFF8A80),
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ),
            if (openTime.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(
                'Opened: $openTime',
                style: GoogleFonts.poppins(color: Colors.white38, fontSize: 9),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildTabButton(
      BuildContext context, String label, int index, String count) {
    final isSelected = _selectedTab == index;
    return GestureDetector(
      onTap: () {
        setState(() {
          _selectedTab = index;
        });
      },
      child: Container(
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.md,
          vertical: AppSpacing.sm,
        ),
        decoration: BoxDecoration(
          color: isSelected ? AppColors.primaryColor : Colors.transparent,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color:
                isSelected ? AppColors.primaryColor : AppColors.veryLightGrey,
          ),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              label,
              style: TextStyle(
                fontWeight: FontWeight.bold,
                color: isSelected ? Colors.white : AppColors.darkGrey,
              ),
            ),
            Text(
              count,
              style: TextStyle(
                fontSize: 12,
                color: isSelected ? Colors.white70 : AppColors.grey,
),
               ),
             ],
           ),
         ),
       );
}

void _handleQuickAction(
  BuildContext context,
  Trade trade,
  String action,
  TradingService tradingService,
) async {
  switch (action) {
    case 'take_half':
      final success = await tradingService.closeTrade(trade.id, null);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(success ? 'Trade closed (take half)' : 'Failed to close trade'),
            backgroundColor: success ? Colors.green : Colors.red,
          ),
        );
      }
      break;
    case 'lock_profit':
      final success = await tradingService.closeTrade(trade.id, null);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(success ? 'Profit locked' : 'Failed to lock profit'),
            backgroundColor: success ? Colors.cyan : Colors.red,
          ),
        );
      }
      break;
    case 'close_peak':
      final success = await tradingService.closeTrade(trade.id, null);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(success ? 'Peak profit captured' : 'Failed to close peak'),
            backgroundColor: success ? Colors.orange : Colors.red,
          ),
        );
      }
      break;
  }
}

Widget _buildDetailRow(String label, String value) => Padding(
        padding: const EdgeInsets.symmetric(vertical: AppSpacing.sm),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label, style: const TextStyle(fontWeight: FontWeight.w500)),
            Text(value),
          ],
        ),
      );
}

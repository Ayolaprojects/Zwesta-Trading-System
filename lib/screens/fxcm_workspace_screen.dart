import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../services/fxcm_trading_service.dart';

class FxcmWorkspaceScreen extends StatefulWidget {
  const FxcmWorkspaceScreen({Key? key}) : super(key: key);

  @override
  State<FxcmWorkspaceScreen> createState() => _FxcmWorkspaceScreenState();
}

class _FxcmWorkspaceScreenState extends State<FxcmWorkspaceScreen> {
  bool _loading = true;
  bool _closingAll = false;
  String? _error;

  Map<String, dynamic> _accounts = const {};
  Map<String, dynamic> _balance = const {};
  Map<String, dynamic> _funds = const {};
  Map<String, dynamic> _positions = const {};
  Map<String, dynamic> _orders = const {};
  Map<String, dynamic> _transactions = const {};
  Map<String, dynamic> _pricing = const {};

  static const List<String> _watchlist = <String>[
    'EUR/USD',
    'GBP/USD',
    'USD/JPY',
    'XAU/USD',
    'XAG/USD',
    'USTECH',
  ];

  @override
  void initState() {
    super.initState();
    _loadWorkspace();
  }

  Future<void> _loadWorkspace() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final responses = await Future.wait<Map<String, dynamic>>([
        FxcmTradingService.getAccounts(),
        FxcmTradingService.getBalance(),
        FxcmTradingService.getFunds(),
        FxcmTradingService.getPositions(),
        FxcmTradingService.getPendingOrders(),
        FxcmTradingService.getTransactions(),
        FxcmTradingService.getPricing(_watchlist.join(',')),
      ]);

      if (!mounted) {
        return;
      }

      setState(() {
        _accounts = responses[0];
        _balance = responses[1];
        _funds = responses[2];
        _positions = responses[3];
        _orders = responses[4];
        _transactions = responses[5];
        _pricing = responses[6];
        _error = _firstError(responses);
        _loading = false;
      });
    } catch (error) {
      if (!mounted) {
        return;
      }
      setState(() {
        _loading = false;
        _error = error.toString();
      });
    }
  }

  String? _firstError(List<Map<String, dynamic>> responses) {
    for (final response in responses) {
      if (response['success'] == false && (response['error']?.toString().isNotEmpty ?? false)) {
        return response['error'].toString();
      }
    }
    return null;
  }

  List<Map<String, dynamic>> _extractList(Map<String, dynamic> payload, List<String> keys) {
    for (final key in keys) {
      final value = payload[key];
      if (value is List) {
        return value.whereType<Map>().map((entry) => Map<String, dynamic>.from(entry)).toList();
      }
    }

    final response = payload['response'];
    if (response is Map<String, dynamic>) {
      return _extractList(response, keys);
    }
    return const <Map<String, dynamic>>[];
  }

  Map<String, dynamic> _extractMap(Map<String, dynamic> payload, List<String> keys) {
    for (final key in keys) {
      final value = payload[key];
      if (value is Map<String, dynamic>) {
        return value;
      }
      if (value is List && value.isNotEmpty && value.first is Map) {
        return Map<String, dynamic>.from(value.first as Map);
      }
    }

    final response = payload['response'];
    if (response is Map<String, dynamic>) {
      return _extractMap(response, keys);
    }
    return const <String, dynamic>{};
  }

  double _asDouble(dynamic value) {
    if (value is num) {
      return value.toDouble();
    }
    return double.tryParse(value?.toString() ?? '') ?? 0.0;
  }

  String _asText(dynamic value, [String fallback = '-']) {
    final text = value?.toString().trim() ?? '';
    return text.isEmpty ? fallback : text;
  }

  String _currencySymbol(String code) {
    switch (_asText(code, 'USD').toUpperCase()) {
      case 'ZAR':
        return 'R';
      case 'EUR':
        return '€';
      case 'GBP':
        return '£';
      case 'JPY':
        return '¥';
      default:
        return r'$';
    }
  }

  String _formatMoney(dynamic amount, [String currency = 'USD']) {
    final resolvedCurrency = _asText(currency, 'USD').toUpperCase();
    return '${_currencySymbol(resolvedCurrency)}${_asDouble(amount).toStringAsFixed(2)} $resolvedCurrency';
  }

  Color _profitColor(double value) => value >= 0 ? const Color(0xFF69F0AE) : const Color(0xFFFF8A80);

  Widget _sideChip(String side) {
    final normalized = side.toUpperCase();
    final accent = normalized == 'BUY' ? const Color(0xFF69F0AE) : const Color(0xFFFF8A80);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: accent.withOpacity(0.14),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: accent.withOpacity(0.45)),
      ),
      child: Text(
        normalized,
        style: GoogleFonts.ibmPlexSans(color: accent, fontSize: 10, fontWeight: FontWeight.w700),
      ),
    );
  }

  Widget _workspacePanel({required Widget child}) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF0B1626),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: Colors.white.withOpacity(0.08)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.18),
            blurRadius: 20,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: child,
    );
  }

  Future<void> _closeAllPositions() async {
    setState(() {
      _closingAll = true;
    });

    final result = await FxcmTradingService.closeAllPositions();

    if (!mounted) {
      return;
    }

    setState(() {
      _closingAll = false;
    });

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          result['success'] == true
              ? 'FXCM positions close request sent.'
              : (result['error']?.toString() ?? 'Failed to close FXCM positions.'),
        ),
        backgroundColor: result['success'] == true ? const Color(0xFF1B5E20) : const Color(0xFF8B0000),
      ),
    );

    if (result['success'] == true) {
      _loadWorkspace();
    }
  }

  @override
  Widget build(BuildContext context) {
    final account = _extractMap(_accounts, <String>['account', 'accounts']);
    final balance = _extractMap(_balance, <String>['balance', 'account', 'accounts']);
    final funds = _extractMap(_funds, <String>['funds', 'account', 'accounts']);
    final positions = _extractList(_positions, <String>['positions', 'open_positions', 'trades']);
    final orders = _extractList(_orders, <String>['orders', 'pending_orders']);
    final transactions = _extractList(_transactions, <String>['transactions', 'closed_positions', 'history']);
    final quotes = _extractList(_pricing, <String>['prices', 'quotes', 'offers', 'data']);

    final accountCurrency = _asText(
      balance['currency'] ?? funds['currency'] ?? account['currency'] ?? account['mc'],
      'USD',
    ).toUpperCase();

    return DefaultTabController(
      length: 5,
      child: Scaffold(
        backgroundColor: const Color(0xFF07111F),
        appBar: AppBar(
          backgroundColor: const Color(0xFF0E1C2F),
          title: Text(
            'FXCM Workspace',
            style: GoogleFonts.ibmPlexSans(fontWeight: FontWeight.w700, letterSpacing: 0.2),
          ),
          flexibleSpace: Container(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [Color(0xFF10253D), Color(0xFF09111D)],
              ),
            ),
          ),
          actions: [
            IconButton(
              tooltip: 'Refresh',
              onPressed: _loading ? null : _loadWorkspace,
              icon: const Icon(Icons.refresh),
            ),
          ],
          bottom: TabBar(
            isScrollable: true,
            indicatorColor: const Color(0xFF00D1FF),
            labelStyle: GoogleFonts.ibmPlexSans(fontWeight: FontWeight.w600),
            tabs: const [
              Tab(text: 'Overview'),
              Tab(text: 'Positions'),
              Tab(text: 'Orders'),
              Tab(text: 'Markets'),
              Tab(text: 'History'),
            ],
          ),
        ),
        body: _loading
            ? const Center(child: CircularProgressIndicator())
            : TabBarView(
                children: [
                  _buildOverview(account, balance, funds, accountCurrency, positions.length, orders.length),
                  _buildPositions(positions, accountCurrency),
                  _buildOrders(orders),
                  _buildMarkets(quotes),
                  _buildHistory(transactions, accountCurrency),
                ],
              ),
      ),
    );
  }

  Widget _buildOverview(
    Map<String, dynamic> account,
    Map<String, dynamic> balance,
    Map<String, dynamic> funds,
    String currency,
    int positionCount,
    int orderCount,
  ) {
    final balanceValue = balance['balance'] ?? account['balance'];
    final equityValue = balance['equity'] ?? account['equity'];
    final marginValue = funds['usedMargin'] ?? funds['usdMr'] ?? funds['margin'] ?? balance['margin'];
    final usableMarginValue = funds['usableMargin'] ?? funds['usable_margin'] ?? balance['marginFree'];
    final profitValue = balance['profit'] ?? balance['grossPL'] ?? account['grossPL'] ?? funds['grossPL'];
    final accountId = _asText(account['accountId'] ?? account['account_id'] ?? balance['accountId']);

    return RefreshIndicator(
      onRefresh: _loadWorkspace,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _workspacePanel(
            child: Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                gradient: const LinearGradient(colors: [Color(0xFF123456), Color(0xFF091521)]),
                borderRadius: BorderRadius.circular(18),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('Trading Station View', style: GoogleFonts.ibmPlexSans(color: Colors.white, fontSize: 20, fontWeight: FontWeight.w700)),
                            const SizedBox(height: 8),
                            Text(
                              accountId == '-' ? 'Connected FXCM account' : 'Account $accountId',
                              style: GoogleFonts.ibmPlexSans(color: Colors.white70, fontSize: 13),
                            ),
                          ],
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
                        decoration: BoxDecoration(
                          color: (_error == null ? const Color(0xFF69F0AE) : const Color(0xFFFFB74D)).withOpacity(0.14),
                          borderRadius: BorderRadius.circular(999),
                          border: Border.all(
                            color: (_error == null ? const Color(0xFF69F0AE) : const Color(0xFFFFB74D)).withOpacity(0.42),
                          ),
                        ),
                        child: Text(
                          _error == null ? 'CONNECTED VIEW' : 'DEGRADED DATA',
                          style: GoogleFonts.ibmPlexSans(
                            color: _error == null ? const Color(0xFF69F0AE) : const Color(0xFFFFB74D),
                            fontSize: 10,
                            fontWeight: FontWeight.w700,
                            letterSpacing: 0.4,
                          ),
                        ),
                      ),
                    ],
                  ),
                  if (_error != null) ...[
                    const SizedBox(height: 12),
                    Text(
                      _error!,
                      style: GoogleFonts.ibmPlexSans(color: const Color(0xFFFFB74D), fontSize: 12, height: 1.4),
                    ),
                  ],
                  const SizedBox(height: 18),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.black.withOpacity(0.18),
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: Colors.white.withOpacity(0.06)),
                    ),
                    child: Wrap(
                      spacing: 10,
                      runSpacing: 10,
                      children: [
                        _statTile('Balance', _formatMoney(balanceValue, currency), const Color(0xFF00D1FF)),
                        _statTile('Equity', _formatMoney(equityValue, currency), const Color(0xFF69F0AE)),
                        _statTile('Usable Margin', _formatMoney(usableMarginValue, currency), const Color(0xFFFFD166)),
                        _statTile('Used Margin', _formatMoney(marginValue, currency), const Color(0xFFFF8A80)),
                        _statTile('Gross P/L', _formatMoney(profitValue, currency), _profitColor(_asDouble(profitValue))),
                        _statTile('Open / Working', '$positionCount / $orderCount', Colors.white),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                  Align(
                    alignment: Alignment.centerRight,
                    child: OutlinedButton.icon(
                      onPressed: _closingAll ? null : _closeAllPositions,
                      style: OutlinedButton.styleFrom(
                        foregroundColor: const Color(0xFFFF8A80),
                        side: const BorderSide(color: Color(0xFFFF8A80)),
                      ),
                      icon: _closingAll
                          ? const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2))
                          : const Icon(Icons.close_fullscreen),
                      label: const Text('Close All Positions'),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _statTile(String label, String value, Color accent) {
    return Container(
      width: 164,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.04),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: accent.withOpacity(0.35)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: GoogleFonts.ibmPlexSans(color: Colors.white60, fontSize: 11, fontWeight: FontWeight.w600)),
          const SizedBox(height: 6),
          Text(value, style: GoogleFonts.ibmPlexSans(color: accent, fontSize: 16, fontWeight: FontWeight.w700)),
        ],
      ),
    );
  }

  Widget _buildPositions(List<Map<String, dynamic>> positions, String currency) {
    if (positions.isEmpty) {
      return _emptyState('No open FXCM positions.');
    }
    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: positions.length,
      separatorBuilder: (_, __) => const SizedBox(height: 12),
      itemBuilder: (context, index) {
        final position = positions[index];
        final side = _asText(position['type'] ?? position['buy_sell']).toUpperCase();
        final profit = _asDouble(position['profit_loss'] ?? position['grossPL'] ?? position['profit']);
        final accent = side == 'BUY' ? const Color(0xFF69F0AE) : const Color(0xFFFF8A80);
        return _dataCard(
          title: _asText(position['symbol'] ?? position['currency']),
          subtitle: 'Deal ${_asText(position['deal_id'] ?? position['tradeId'])}',
          accent: accent,
          leading: _sideChip(side),
          trailing: Text(_formatMoney(profit, currency), style: GoogleFonts.ibmPlexSans(color: _profitColor(profit), fontWeight: FontWeight.w700)),
          rows: [
            _kv('Size', _asText(position['size'] ?? position['amountK'] ?? position['amount'])),
            _kv('Open Rate', _asText(position['level'] ?? position['open'] ?? position['open_rate'])),
            _kv('Market', _asText(position['currency'] ?? position['symbol'])),
          ],
        );
      },
    );
  }

  Widget _buildOrders(List<Map<String, dynamic>> orders) {
    if (orders.isEmpty) {
      return _emptyState('No working FXCM orders.');
    }
    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: orders.length,
      separatorBuilder: (_, __) => const SizedBox(height: 12),
      itemBuilder: (context, index) {
        final order = orders[index];
        final side = _asText(order['type'] ?? order['buy_sell']).toUpperCase();
        return _dataCard(
          title: _asText(order['symbol'] ?? order['currency']),
          subtitle: 'Order ${_asText(order['orderId'] ?? order['order_id'])}',
          accent: const Color(0xFF00D1FF),
          leading: side == '-' ? null : _sideChip(side),
          rows: [
            _kv('Amount', _asText(order['size'] ?? order['amountK'] ?? order['amount'])),
            _kv('Rate', _asText(order['rate'] ?? order['price'])),
            _kv('Status', _asText(order['status'] ?? order['timeInForce'])),
          ],
        );
      },
    );
  }

  Widget _buildMarkets(List<Map<String, dynamic>> quotes) {
    if (quotes.isEmpty) {
      return _emptyState('No FXCM market watch data yet.');
    }
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _workspacePanel(
          child: Container(
            padding: const EdgeInsets.all(14),
            child: Column(
              children: [
                Row(
                  children: [
                    Expanded(child: Text('Instrument', style: GoogleFonts.ibmPlexSans(color: Colors.white38, fontSize: 11, fontWeight: FontWeight.w600))),
                    SizedBox(width: 92, child: Text('Bid', textAlign: TextAlign.right, style: GoogleFonts.ibmPlexSans(color: Colors.white38, fontSize: 11, fontWeight: FontWeight.w600))),
                    const SizedBox(width: 10),
                    SizedBox(width: 92, child: Text('Ask', textAlign: TextAlign.right, style: GoogleFonts.ibmPlexSans(color: Colors.white38, fontSize: 11, fontWeight: FontWeight.w600))),
                    const SizedBox(width: 10),
                    SizedBox(width: 70, child: Text('Spread', textAlign: TextAlign.right, style: GoogleFonts.ibmPlexSans(color: Colors.white38, fontSize: 11, fontWeight: FontWeight.w600))),
                  ],
                ),
                const SizedBox(height: 10),
                ...quotes.asMap().entries.map((entry) {
                  final quote = entry.value;
                  final bid = _asDouble(quote['bid'] ?? quote['Bid']);
                  final ask = _asDouble(quote['ask'] ?? quote['Ask']);
                  final spread = bid > 0 && ask > 0 ? ask - bid : 0.0;
                  final symbol = _asText(quote['symbol'] ?? quote['currency'] ?? quote['instrument']);
                  return Container(
                    margin: EdgeInsets.only(top: entry.key == 0 ? 0 : 10),
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 12),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.03),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: Colors.white.withOpacity(0.05)),
                    ),
                    child: Row(
                      children: [
                        Expanded(
                          child: Text(symbol, style: GoogleFonts.ibmPlexSans(color: Colors.white, fontSize: 13, fontWeight: FontWeight.w700)),
                        ),
                        SizedBox(
                          width: 92,
                          child: Text(
                            bid == 0 ? '-' : bid.toStringAsFixed(5),
                            textAlign: TextAlign.right,
                            style: GoogleFonts.ibmPlexSans(color: const Color(0xFF69F0AE), fontSize: 13, fontWeight: FontWeight.w700),
                          ),
                        ),
                        const SizedBox(width: 10),
                        SizedBox(
                          width: 92,
                          child: Text(
                            ask == 0 ? '-' : ask.toStringAsFixed(5),
                            textAlign: TextAlign.right,
                            style: GoogleFonts.ibmPlexSans(color: const Color(0xFFFFD166), fontSize: 13, fontWeight: FontWeight.w700),
                          ),
                        ),
                        const SizedBox(width: 10),
                        SizedBox(
                          width: 70,
                          child: Text(
                            spread == 0 ? '-' : spread.toStringAsFixed(5),
                            textAlign: TextAlign.right,
                            style: GoogleFonts.ibmPlexSans(color: Colors.white70, fontSize: 12, fontWeight: FontWeight.w600),
                          ),
                        ),
                      ],
                    ),
                  );
                }),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildHistory(List<Map<String, dynamic>> transactions, String currency) {
    if (transactions.isEmpty) {
      return _emptyState('No recent FXCM transaction history.');
    }
    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: transactions.length,
      separatorBuilder: (_, __) => const SizedBox(height: 12),
      itemBuilder: (context, index) {
        final txn = transactions[index];
        final pnl = _asDouble(txn['profit'] ?? txn['grossPL'] ?? txn['amount']);
        return _dataCard(
          title: _asText(txn['symbol'] ?? txn['currency'] ?? txn['type']),
          subtitle: _asText(txn['time'] ?? txn['date'] ?? txn['createdAt']),
          accent: const Color(0xFFB39DDB),
          leading: _asText(txn['type'] ?? txn['buy_sell']) == '-' ? null : _sideChip(_asText(txn['type'] ?? txn['buy_sell']).toUpperCase()),
          trailing: Text(_formatMoney(pnl, currency), style: GoogleFonts.ibmPlexSans(color: _profitColor(pnl), fontWeight: FontWeight.w700)),
          rows: [
            _kv('Volume', _asText(txn['volume'] ?? txn['amount'])),
            _kv('Price', _asText(txn['price'] ?? txn['rate'])),
            _kv('Ref', _asText(txn['deal_id'] ?? txn['tradeId'] ?? txn['id'])),
          ],
        );
      },
    );
  }

  Widget _emptyState(String text) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Text(text, style: GoogleFonts.ibmPlexSans(color: Colors.white60, fontSize: 14)),
      ),
    );
  }

  Widget _dataCard({
    required String title,
    required String subtitle,
    required Color accent,
    required List<Widget> rows,
    Widget? leading,
    Widget? trailing,
  }) {
    return _workspacePanel(
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: accent.withOpacity(0.12)),
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [accent.withOpacity(0.06), Colors.transparent],
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                if (leading != null) ...[
                  leading,
                  const SizedBox(width: 10),
                ],
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(title, style: GoogleFonts.ibmPlexSans(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w700)),
                      const SizedBox(height: 4),
                      Text(subtitle, style: GoogleFonts.ibmPlexSans(color: Colors.white54, fontSize: 11)),
                    ],
                  ),
                ),
                if (trailing != null) trailing,
              ],
            ),
            const SizedBox(height: 14),
            Wrap(spacing: 18, runSpacing: 10, children: rows),
          ],
        ),
      ),
    );
  }

  Widget _kv(String label, String value) {
    return SizedBox(
      width: 140,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: GoogleFonts.ibmPlexSans(color: Colors.white38, fontSize: 10, fontWeight: FontWeight.w600)),
          const SizedBox(height: 4),
          Text(value, style: GoogleFonts.ibmPlexSans(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}
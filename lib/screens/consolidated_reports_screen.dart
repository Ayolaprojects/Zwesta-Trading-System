import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import '../utils/environment_config.dart';
import '../widgets/logo_widget.dart';

class ConsolidatedReportsScreen extends StatefulWidget {
  const ConsolidatedReportsScreen({Key? key}) : super(key: key);

  @override
  State<ConsolidatedReportsScreen> createState() =>
      _ConsolidatedReportsScreenState();
}

class _ConsolidatedReportsScreenState extends State<ConsolidatedReportsScreen> {
  late final String _apiUrl = EnvironmentConfig.apiUrl;

  Map<String, dynamic> _reportData = {};
  bool _isLoading = false;
  String? _errorMessage;
  String _selectedMode = 'DEMO';

  String _normalizeCurrency(dynamic value) {
    final currency = value?.toString().trim().toUpperCase();
    return currency == null || currency.isEmpty ? 'USD' : currency;
  }

  String _currencySymbol(String currency) {
    switch (_normalizeCurrency(currency)) {
      case 'ZAR':
        return 'R';
      case 'GBP':
        return 'GBP';
      case 'USD':
      default:
        return r'$';
    }
  }

  String _formatMoney(num amount, String currency, {bool includeSign = false}) {
    final prefix = includeSign && amount > 0 ? '+' : '';
    return '$prefix${_currencySymbol(currency)}${amount.toStringAsFixed(2)}';
  }

  String _formatBreakdown(Map<String, double> totals) {
    if (totals.isEmpty) {
      return _formatMoney(0, 'USD');
    }
    final entries = totals.entries.toList()..sort((a, b) => a.key.compareTo(b.key));
    return entries.map((entry) => _formatMoney(entry.value, entry.key)).join(' • ');
  }

  String _reportKey(String broker, String accountNumber) {
    final normalizedBroker = broker.trim().isEmpty ? 'Unknown' : broker.trim();
    final normalizedAccount = accountNumber.trim().isEmpty ? 'N/A' : accountNumber.trim();
    return '$normalizedBroker|$normalizedAccount';
  }

  Map<String, dynamic> _createEmptyReport(String broker, String accountNumber, String currency) {
    return {
      'broker': broker,
      'accountNumber': accountNumber,
      'currency': _normalizeCurrency(currency),
      'totalTrades': 0,
      'winningTrades': 0,
      'losingTrades': 0,
      'winRate': 0.0,
      'totalProfit': 0.0,
      'totalLoss': 0.0,
      'netProfit': 0.0,
      'largestWin': 0.0,
      'largestLoss': 0.0,
    };
  }

  void _applyTradeToReport(Map<String, dynamic> report, Map<String, dynamic> trade) {
    final profit = ((trade['profit'] ?? 0) as num).toDouble();
    report['totalTrades'] = (report['totalTrades'] as int) + 1;
    report['netProfit'] = (report['netProfit'] as double) + profit;

    if (profit > 0) {
      report['winningTrades'] = (report['winningTrades'] as int) + 1;
      report['totalProfit'] = (report['totalProfit'] as double) + profit;
      report['largestWin'] = profit > (report['largestWin'] as double) ? profit : report['largestWin'];
    } else {
      final loss = profit.abs();
      report['losingTrades'] = (report['losingTrades'] as int) + 1;
      report['totalLoss'] = (report['totalLoss'] as double) + loss;
      report['largestLoss'] = loss > (report['largestLoss'] as double) ? loss : report['largestLoss'];
    }
  }

  @override
  void initState() {
    super.initState();
    _initializeMode();
  }

  Future<void> _initializeMode() async {
    final prefs = await SharedPreferences.getInstance();
    final mode = (prefs.getString('trading_mode') ?? 'DEMO').toUpperCase();
    if (!mounted) {
      return;
    }
    setState(() {
      _selectedMode = mode;
    });
    await _loadReports();
  }

  Future<void> _loadReports() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final prefs = await SharedPreferences.getInstance();
      final sessionToken = prefs.getString('auth_token');
      await prefs.setString('trading_mode', _selectedMode);

      if (sessionToken == null || sessionToken.isEmpty) {
        setState(() {
          _errorMessage = 'Session expired. Please login again.';
        });
        return;
      }

      final responses = await Future.wait([
        http.get(
          Uri.parse('$_apiUrl/api/account/detailed?mode=$_selectedMode'),
          headers: {
            'Content-Type': 'application/json',
            'X-Session-Token': sessionToken,
          },
        ),
        http.get(
          Uri.parse('$_apiUrl/api/trades/history?days=30'),
          headers: {
            'Content-Type': 'application/json',
            'X-Session-Token': sessionToken,
          },
        ),
      ]).timeout(const Duration(seconds: 10));

      final accountResponse = responses[0];
      final tradesResponse = responses[1];

      if (accountResponse.statusCode == 200 && tradesResponse.statusCode == 200) {
        final accountData = jsonDecode(accountResponse.body) as Map<String, dynamic>;
        final tradesData = jsonDecode(tradesResponse.body) as Map<String, dynamic>;
        final account = accountData['account'] as Map<String, dynamic>? ?? {};
        final allAccounts = (accountData['allAccounts'] as List? ?? [])
            .map((entry) => Map<String, dynamic>.from(entry as Map))
            .toList();
        final trades = (tradesData['trades'] as List? ?? [])
            .map((entry) => Map<String, dynamic>.from(entry as Map))
            .toList();

        final accounts = allAccounts.isNotEmpty
            ? allAccounts
            : [if (account.isNotEmpty) account];
        final reports = <String, Map<String, dynamic>>{};
        final brokerAccountCounts = <String, int>{};

        for (final accountEntry in accounts) {
          final broker = (accountEntry['broker'] ?? 'Unknown').toString();
          final accountNumber = (accountEntry['accountNumber'] ?? accountEntry['account_number'] ?? 'N/A').toString();
          final currency = (accountEntry['currency'] ?? 'USD').toString();
          final key = _reportKey(broker, accountNumber);
          reports[key] = _createEmptyReport(broker, accountNumber, currency);
          brokerAccountCounts[broker] = (brokerAccountCounts[broker] ?? 0) + 1;
        }

        for (final trade in trades) {
          final broker = (trade['broker'] ?? trade['source'] ?? account['broker'] ?? 'Unknown').toString();
          final explicitAccountNumber = (trade['accountNumber'] ?? trade['account_number'] ?? trade['account'] ?? '').toString();
          String accountNumber = explicitAccountNumber;

          if (accountNumber.trim().isEmpty && (brokerAccountCounts[broker] ?? 0) == 1) {
            final matchingAccount = accounts.firstWhere(
              (entry) => (entry['broker'] ?? '').toString() == broker,
              orElse: () => <String, dynamic>{},
            );
            accountNumber = (matchingAccount['accountNumber'] ?? matchingAccount['account_number'] ?? 'N/A').toString();
          }

          final key = _reportKey(broker, accountNumber);
          reports.putIfAbsent(
            key,
            () => _createEmptyReport(
              broker,
              accountNumber.isEmpty ? 'N/A' : accountNumber,
              (trade['currency'] ?? account['currency'] ?? 'USD').toString(),
            ),
          );
          _applyTradeToReport(reports[key]!, trade);
        }

        for (final report in reports.values) {
          final totalTrades = report['totalTrades'] as int;
          report['winRate'] = totalTrades == 0
              ? 0.0
              : ((report['winningTrades'] as int) / totalTrades) * 100;
        }

        setState(() {
          _reportData = {
            'success': true,
            'reports': reports,
          };
        });
      } else {
        setState(() {
          _errorMessage = 'Failed to load reports';
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Error: $e';
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _exportToPDF() async {
    try {
      // This would integrate with pdf_export_service
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('PDF export feature coming soon')),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final reports = _reportData['reports'] as Map<String, dynamic>? ?? {};

    return Scaffold(
      backgroundColor: const Color(0xFF0A0E21),
      appBar: AppBar(
        backgroundColor: const Color(0xFF111633),
        elevation: 0,
        title: const Row(
          children: [
            LogoWidget(size: 40, showText: false),
            SizedBox(width: 12),
            Text('Consolidated Reports'),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.home_outlined),
            tooltip: 'Home',
            onPressed: () => Navigator.of(context).popUntil((route) => route.isFirst),
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadReports,
          ),
          IconButton(
            icon: const Icon(Icons.picture_as_pdf),
            onPressed: _exportToPDF,
            tooltip: 'Export to PDF',
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF00E5FF)))
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Wrap(
                    spacing: 10,
                    runSpacing: 10,
                    children: [
                      ChoiceChip(
                        label: const Text('Live'),
                        selected: _selectedMode == 'LIVE',
                        onSelected: (selected) {
                          if (!selected) return;
                          setState(() {
                            _selectedMode = 'LIVE';
                          });
                          _loadReports();
                        },
                      ),
                      ChoiceChip(
                        label: const Text('Demo'),
                        selected: _selectedMode == 'DEMO',
                        onSelected: (selected) {
                          if (!selected) return;
                          setState(() {
                            _selectedMode = 'DEMO';
                          });
                          _loadReports();
                        },
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.06),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: Colors.white.withOpacity(0.08)),
                    ),
                    child: const Text(
                      'This report center mirrors the web summary flow. Use the dashboard Hub tab for deeper broker, wallet, and automation modules.',
                      style: TextStyle(color: Colors.white70, fontSize: 12),
                    ),
                  ),
                  const SizedBox(height: 16),
                  if (_errorMessage != null)
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.red.withOpacity(0.15),
                        border: Border.all(color: Colors.redAccent),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        _errorMessage!,
                        style: const TextStyle(color: Colors.redAccent),
                      ),
                    ),
                  const SizedBox(height: 16),
                  if (reports.isEmpty)
                    const Center(
                      child: Column(
                        children: [
                          Icon(
                            Icons.assessment,
                            size: 64,
                            color: Colors.white24,
                          ),
                          SizedBox(height: 16),
                          Text('No reports available', style: TextStyle(color: Colors.white70)),
                        ],
                      ),
                    )
                  else ...[
                    _buildSummaryCard(reports),
                    const SizedBox(height: 24),
                    const Text(
                      'Account Details',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 12),
                    ..._buildAccountReports(reports),
                  ],
                ],
              ),
            ),
    );
  }

  Widget _buildSummaryCard(Map<String, dynamic> reports) {
    double totalTrades = 0;
    final totalProfitByCurrency = <String, double>{};
    var accountCount = 0;
    double totalWinRate = 0;

    reports.forEach((key, report) {
      if (report is Map) {
        final currency = _normalizeCurrency(report['currency']);
        totalTrades += report['totalTrades']?.toDouble() ?? 0;
        totalProfitByCurrency[currency] = (totalProfitByCurrency[currency] ?? 0.0) + ((report['netProfit'] ?? 0).toDouble());
        totalWinRate += report['winRate']?.toDouble() ?? 0;
        accountCount++;
      }
    });

    final avgWinRate = accountCount > 0 ? totalWinRate / accountCount : 0;
    final totalProfit = totalProfitByCurrency.values.fold<double>(0, (sum, value) => sum + value);

    return Card(
      elevation: 4,
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Overall Summary',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: _buildSummaryStatistic(
                    'Accounts',
                    accountCount.toString(),
                    Colors.blue,
                  ),
                ),
                Expanded(
                  child: _buildSummaryStatistic(
                    'Total Trades',
                    totalTrades.toStringAsFixed(0),
                    Colors.purple,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: _buildSummaryStatistic(
                    'Win Rate',
                    '${avgWinRate.toStringAsFixed(1)}%',
                    Colors.orange,
                  ),
                ),
                Expanded(
                  child: _buildSummaryStatistic(
                    'Net Profit',
                    _formatBreakdown(totalProfitByCurrency),
                    totalProfit >= 0 ? Colors.green : Colors.red,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSummaryStatistic(String label, String value, Color color) => Column(
      children: [
        Text(
          label,
          style: TextStyle(
            fontSize: 12,
            color: Colors.grey[600],
          ),
        ),
        const SizedBox(height: 4),
        Text(
          value,
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
      ],
    );

  List<Widget> _buildAccountReports(Map<String, dynamic> reports) => reports.entries.map((entry) {
      final report = entry.value as Map<String, dynamic>;
      final broker = (report['broker'] ?? 'Unknown').toString();
      final accountNumber = (report['accountNumber'] ?? 'N/A').toString();
      final accountId = '$broker • $accountNumber';

      return _buildAccountReportCard(accountId, report);
    }).toList();

  Widget _buildAccountReportCard(String accountId, Map<String, dynamic> report) {
    final netProfit = report['netProfit'] as double? ?? 0;
    final isProfit = netProfit >= 0;
    final currency = _normalizeCurrency(report['currency']);

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      accountId,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Broker: ${report['broker'] ?? 'N/A'}',
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.grey[600],
                      ),
                    ),
                  ],
                ),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 6,
                  ),
                  decoration: BoxDecoration(
                    color: isProfit
                        ? Colors.green.shade50
                        : Colors.red.shade50,
                    border: Border.all(
                      color: isProfit ? Colors.green : Colors.red,
                    ),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    _formatMoney(netProfit, currency),
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: isProfit ? Colors.green : Colors.red,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Container(
              decoration: BoxDecoration(
                color: Colors.grey[50],
                borderRadius: BorderRadius.circular(8),
              ),
              padding: const EdgeInsets.all(12),
              child: Column(
                children: [
                  _buildReportRow(
                    'Total Trades',
                    (report['totalTrades'] ?? 0).toString(),
                  ),
                  _buildReportRow(
                    'Winning Trades',
                    '${report['winningTrades'] ?? 0} (${(report['winRate'] ?? 0).toStringAsFixed(1)}%)',
                    color: Colors.green,
                  ),
                  _buildReportRow(
                    'Losing Trades',
                    (report['losingTrades'] ?? 0).toString(),
                    color: Colors.red,
                  ),
                  const Divider(height: 12),
                  _buildReportRow(
                    'Total Profit',
                    _formatMoney((report['totalProfit'] ?? 0) as num, currency),
                    color: Colors.green,
                  ),
                  _buildReportRow(
                    'Total Loss',
                    _formatMoney(-((report['totalLoss'] ?? 0) as num), currency),
                    color: Colors.red,
                  ),
                  _buildReportRow(
                    'Largest Win',
                    _formatMoney((report['largestWin'] ?? 0) as num, currency),
                  ),
                  _buildReportRow(
                    'Largest Loss',
                    _formatMoney(-((report['largestLoss']?.abs() ?? 0) as num), currency),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildReportRow(String label, String value, {Color? color}) => Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label),
          Text(
            value,
            style: TextStyle(
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
        ],
      ),
    );
}

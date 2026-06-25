// import 'package:fl_chart/fl_chart.dart'; // Disabled for compatibility
import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import '../services/ig_trading_service.dart';
import '../utils/environment_config.dart';
import 'bot_configuration_screen.dart' show BotConfigurationScreen;
import 'bot_dashboard_screen.dart';
import 'consolidated_reports_screen.dart';

class BotAnalyticsScreen extends StatefulWidget {
  const BotAnalyticsScreen({
    required this.bot,
    Key? key,
  }) : super(key: key);
  final Map<String, dynamic> bot;

  @override
  State<BotAnalyticsScreen> createState() => _BotAnalyticsScreenState();
}

class _BotAnalyticsScreenState extends State<BotAnalyticsScreen> {
  Timer? _refreshTimer;
  late Map<String, dynamic> _botData;
  List<Map<String, dynamic>> _fallbackTradeHistory = [];
  DateTime? _lastFallbackTradeRefreshAt;

  // Withdrawal analytics state
  Map<String, dynamic>? _withdrawalAnalytics;
  bool _withdrawalLoading = false;

  // IG state
  bool _isIG = false;
  bool _igLoading = false;
  Map<String, dynamic>? _igBalance;
  List<dynamic> _igPositions = [];
  List<dynamic> _igTransactions = [];
  String? _igError;

  @override
  void initState() {
    super.initState();
    _botData = Map<String, dynamic>.from(widget.bot);
    final brokerType = _botData['broker_type'] ?? _botData['broker'] ?? 'MT5';
    _isIG = brokerType.toString().toUpperCase().contains('IG');

    _refreshAnalytics();
    _loadWithdrawalAnalytics();
    _refreshTimer = Timer.periodic(const Duration(seconds: 10), (_) {
      if (mounted) {
        _refreshAnalytics();
      }
    });

    if (_isIG) {
      _loadIGData();
    }
  }

  Future<void> _loadTradeHistoryFallback() async {
    final now = DateTime.now();
    if (_lastFallbackTradeRefreshAt != null && now.difference(_lastFallbackTradeRefreshAt!) < const Duration(seconds: 8)) {
      return;
    }
    _lastFallbackTradeRefreshAt = now;

    try {
      final prefs = await SharedPreferences.getInstance();
      final sessionToken = prefs.getString('auth_token');
      final botId = _botData['botId'];
      if (sessionToken == null || sessionToken.isEmpty || botId == null) {
        return;
      }

      final response = await http.get(
        Uri.parse('${EnvironmentConfig.apiUrl}/api/bot/$botId/trades-detailed?limit=30'),
        headers: {
          'Content-Type': 'application/json',
          'X-Session-Token': sessionToken,
        },
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        final trades = (data['trades'] as List? ?? [])
            .map((entry) => Map<String, dynamic>.from(entry as Map))
            .toList();
        if (mounted) {
          setState(() {
            _fallbackTradeHistory = trades;
          });
        }
      }
    } catch (e) {
      debugPrint('Error loading fallback trade history: $e');
    }
  }

  Future<void> _loadIGData() async {
    if (!_isIG) {
      return;
    }
    setState(() {
      _igLoading = true;
      _igError = null;
    });
    try {
      final results = await Future.wait([
        IGTradingService.getBalance(),
        IGTradingService.getPositions(),
        IGTradingService.getTransactions(pageSize: 20),
      ]);
      if (mounted) {
        setState(() {
          _igLoading = false;
          final balData = results[0];
          if (balData['success'] == true) {
            _igBalance = balData;
          }
          final posData = results[1];
          if (posData['success'] == true) {
            _igPositions = posData['positions'] ?? [];
          }
          final txData = results[2];
          if (txData['success'] == true) {
            _igTransactions = txData['transactions'] ?? [];
          }
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _igLoading = false;
          _igError = e.toString();
        });
      }
    }
  }

  Future<void> _loadWithdrawalAnalytics() async {
    if (mounted) setState(() => _withdrawalLoading = true);
    try {
      final prefs = await SharedPreferences.getInstance();
      final sessionToken = prefs.getString('auth_token');
      if (sessionToken == null || sessionToken.isEmpty) return;

      final response = await http.get(
        Uri.parse('${EnvironmentConfig.apiUrl}/api/withdrawals/analytics'),
        headers: {
          'Content-Type': 'application/json',
          'X-Session-Token': sessionToken,
        },
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        if (data['success'] == true && mounted) {
          setState(() => _withdrawalAnalytics = data);
        }
      }
    } catch (e) {
      debugPrint('Error loading withdrawal analytics: $e');
    } finally {
      if (mounted) setState(() => _withdrawalLoading = false);
    }
  }

  Future<void> _refreshAnalytics() async {
    // Fetch fresh bot data from backend API
    try {
      final prefs = await SharedPreferences.getInstance();
      final sessionToken = prefs.getString('auth_token');
      final currentBotId = _botData['botId'];

      if (sessionToken == null || sessionToken.isEmpty) {
        debugPrint('Skipping analytics refresh: missing session token');
        _refreshTimer?.cancel();
        return;
      }

      if (currentBotId == null || currentBotId.toString().isEmpty) {
        return;
      }

      final url =
          '${EnvironmentConfig.apiUrl}/api/bot/$currentBotId/analytics-snapshot';

      final response = await http.get(
        Uri.parse(url),
        headers: {
          'Content-Type': 'application/json',
          'X-Session-Token': sessionToken,
        },
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['success'] == true) {
          final bot = data['bot'];
          if (bot is Map<String, dynamic> && mounted) {
            final newBotId = bot['botId'];
            if (newBotId != currentBotId) {
              _fallbackTradeHistory = [];
            }
            setState(() {
              _botData = bot;
            });
            await _loadTradeHistoryFallback();
          }
        }
      } else if (response.statusCode == 401 || response.statusCode == 403) {
        debugPrint('Stopping analytics refresh due to unauthorized session');
        _refreshTimer?.cancel();
      }
    } catch (e) {
      debugPrint('Error refreshing analytics: $e');
    }
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    super.dispose();
  }

  double _toDouble(dynamic value, [double fallback = 0]) {
    if (value == null) {
      return fallback;
    }
    if (value is num) {
      return value.toDouble();
    }
    return double.tryParse(value.toString()) ?? fallback;
  }

  DateTime? _tradeTimestamp(Map<String, dynamic> trade) {
    final timeRaw =
        trade['closedAt'] ??
        trade['exitTime'] ??
        trade['time'] ??
        trade['closeTime'] ??
        trade['time_close'] ??
        trade['openedAt'] ??
        trade['entryTime'] ??
        trade['time_open'] ??
        trade['openTime'];
    if (timeRaw == null) {
      return null;
    }
    if (timeRaw is num) {
      final millis = timeRaw > 1e12 ? timeRaw.toInt() : timeRaw.toInt() * 1000;
      return DateTime.fromMillisecondsSinceEpoch(millis);
    }
    return DateTime.tryParse(timeRaw.toString());
  }

  int _tradeTimestampMillis(Map<String, dynamic> trade) {
    return _tradeTimestamp(trade)?.millisecondsSinceEpoch ?? 0;
  }

  String _tradeIdentityKey(Map<String, dynamic> trade) {
    final ticket = trade['ticket']?.toString().trim();
    if (ticket != null && ticket.isNotEmpty) {
      return 'ticket:$ticket';
    }

    final tradeId =
        trade['tradeId']?.toString().trim() ??
        trade['trade_id']?.toString().trim() ??
        trade['trade_id']?.toString().trim();
    if (tradeId != null && tradeId.isNotEmpty) {
      return 'trade:$tradeId';
    }

    final symbol = trade['symbol']?.toString().trim() ?? '';
    final type = trade['type']?.toString().trim() ?? '';
    final status = trade['status']?.toString().trim() ?? '';
    final timestamp = _tradeTimestampMillis(trade);
    final volume = trade['volume']?.toString().trim() ?? '';
    return 'fallback:$symbol|$type|$status|$timestamp|$volume';
  }

  Map<String, dynamic> _mergeTradeRecords(
    Map<String, dynamic> current,
    Map<String, dynamic> incoming,
  ) {
    final merged = <String, dynamic>{...current, ...incoming};

    for (final key in const [
      'closedAt',
      'exitTime',
      'time',
      'closeTime',
      'time_close',
      'openedAt',
      'entryTime',
      'time_open',
      'openTime',
      'ticket',
      'tradeId',
      'trade_id',
      'symbol',
      'type',
      'status',
      'profit',
      'entryPrice',
      'exitPrice',
      'currentPrice',
      'volume',
    ]) {
      final currentValue = current[key];
      final incomingValue = incoming[key];
      final currentIsEmpty = currentValue == null || currentValue.toString().trim().isEmpty;
      final incomingIsFilled = incomingValue != null && incomingValue.toString().trim().isNotEmpty;
      if (currentIsEmpty && incomingIsFilled) {
        merged[key] = incomingValue;
      }
    }

    return merged;
  }
  )

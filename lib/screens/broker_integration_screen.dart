import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:http/http.dart' as http;
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../models/broker_connection_model.dart';
import '../services/broker_connection_service.dart';
import '../services/broker_credentials_service.dart';
import '../services/trading_service.dart';
import '../utils/constants.dart';
import '../utils/environment_config.dart';
import '../widgets/logo_widget.dart';
import 'bot_configuration_route.dart';
import 'bot_dashboard_screen.dart';
import 'broker_analytics_dashboard.dart';
import 'consolidated_reports_screen.dart';
import 'dashboard_screen.dart';

class BrokerIntegrationScreen extends StatefulWidget {

  const BrokerIntegrationScreen({
    Key? key,
    this.onBackPressed,
  }) : super(key: key);
  final VoidCallback? onBackPressed;

  @override
  State<BrokerIntegrationScreen> createState() =>
      _BrokerIntegrationScreenState();
}

class _BrokerIntegrationScreenState extends State<BrokerIntegrationScreen> {
  late TextEditingController _serverController;
  late TextEditingController _accountController;
  late TextEditingController _passwordController;
  late TextEditingController _apiKeyController;
  late TextEditingController _usernameController;
  String _selectedBroker = 'Exness';
  bool _showSuccess = false;
  bool _isTestingConnection = false;
  bool _isConnected = false;
  bool _autoReconnectEnabled = false;
  bool _isLiveMode = false;  // DEMO by default
  DateTime? _lastConnectionTime;
  double _accountBalance = 0;
  double _accountEquity = 0;
  double _accountFreeMargin = 0;
  double _accountMargin = 0;
  double _accountMarginLevel = 0;
  double _accountProfit = 0;
  String _accountCurrency = 'USD';  // Actual currency of the connected account (USD, ZAR, etc.)
  List<BrokerAccount> _savedAccounts = [];
  BrokerAccount? _activeAccount;

  // ✅ ONLY INTEGRATED BROKERS - These are fully working and tested
  final List<String> brokers = [
    'Exness',      // ✅ Primary MT5 path with crypto support
    'Binance',     // ✅ Primary crypto spot trading path
    'Luno',        // ✅ REST API crypto spot trading path
    'FXCM',        // ✅ REST API forex/CFD trading
    'PXBT',        // ✅ Prime XBT crypto trading
  ];

  String _sanitizeSelectedBroker(String broker) {
    final normalizedBroker = _normalizeBrokerDisplayName(broker);
    if (brokers.contains(normalizedBroker)) {
      return normalizedBroker;
    }
    return 'Exness';
  }

  final Map<String, String> brokerServers = {
    'Binance': 'spot',
    'FXCM': 'REST-API',
    'Pepperstone': 'Pepperstone MT5 Live',
    'FxOpen': 'FxOpen-MT5',
    'Exness': 'Exness-MT5Trial9',
    'Darwinex': 'Darwinex MT5',
    'IG Markets': 'REST-API',
    'FXM': 'REST-API',
    'AvaTrade': 'Ava-Real',
    'FP Markets': 'FPMarkets-Live',
    'Zulu Trade (SA)': 'ZuluTrade ZA',
    'Ovex (SA)': 'Ovex SA',
    'PXBT': 'PXBTTrading-1',
    'Prime XBT': 'PXBTTrading-1',
    'Trade Nations': 'TradeNations-MT5',
    'MetaQuotes': 'MetaQuotes-MT5',
  };

  @override
  void initState() {
    super.initState();
    _serverController = TextEditingController();
    _accountController = TextEditingController();
    _passwordController = TextEditingController();
    _apiKeyController = TextEditingController();
    _usernameController = TextEditingController();
    _loadSavedCredentials();
    _loadSavedAccounts();
  }

  bool get _isBinanceBroker => _selectedBroker.toLowerCase() == 'binance';
    bool get _isLunoBroker => _selectedBroker.toLowerCase() == 'luno';
  bool get _isFxcmBroker =>
      _selectedBroker.toLowerCase() == 'fxcm' ||
      _selectedBroker.toLowerCase() == 'fxm';
  bool get _isExnessBroker => _selectedBroker.toLowerCase() == 'exness';
  bool get _isPxbtBroker =>
      _selectedBroker.toLowerCase() == 'pxbt' ||
      _selectedBroker.toLowerCase() == 'prime xbt';
    bool get _isMt5Broker => !_isBinanceBroker && !_isLunoBroker && !_isFxcmBroker;

  String _normalizeBrokerDisplayName(String broker) {
    final raw = broker.trim();
    if (raw.isEmpty) return 'Exness';
    final lower = raw.toLowerCase();
    if (lower == 'fxm') return 'FXCM';
    if (lower == 'prime xbt' || lower == 'pxbt') return 'PXBT';
    if (lower == 'binance') return 'Binance';
    if (lower == 'luno') return 'Luno';
    if (lower == 'exness') return 'Exness';
    return raw;
  }

  Future<void> _persistPreferredBrokerChoice(String broker) async {
    final prefs = await SharedPreferences.getInstance();
    final userId = prefs.getString('user_id') ?? '';
    await prefs.setString(
      _userScopedPrefKey('preferred_broker_display', userId),
      _sanitizeSelectedBroker(broker),
    );
  }

  double _doubleValue(dynamic value) =>
      value is num ? value.toDouble() : double.tryParse(value?.toString() ?? '0') ?? 0.0;

  static const Map<String, String> _exnessKnownLiveServers = {
    '223689940': 'MT5Real30',
    '295677214': 'Exness-MT5Real27',
  };

  static const Map<String, String> _exnessKnownServerPaths = {
    'MT5Real30': r'C:\MT5\Exness-Live\Max terminal64.exe\terminal64.exe',
    'Exness-MT5Real27': r'C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe',
    'Exness-MT5Trial9': r'C:\Program Files\MetaTrader 5\terminal64.exe',
  };

  String _resolveExnessServer({
    bool? isLiveOverride,
    String? accountNumber,
    String? fallbackServer,
  }) {
    final isLive = isLiveOverride ?? _isLiveMode;
    final providedServer = (fallbackServer ?? '').trim();
    if (providedServer.isNotEmpty) {
      return providedServer;
    }
    if (!isLive) {
      return 'Exness-MT5Trial9';
    }
    final normalizedAccount = (accountNumber ?? _accountController.text).trim();
    return _exnessKnownLiveServers[normalizedAccount] ?? 'Exness-MT5Real27';
  }

  String? _preferredMt5TerminalPath() {
    if (_isExnessBroker) {
      final resolvedServer = _resolveExnessServer(
        isLiveOverride: _isLiveMode,
        accountNumber: _accountController.text,
        fallbackServer: _serverController.text,
      );
      return _exnessKnownServerPaths[resolvedServer] ?? (_isLiveMode ? r'C:\MT5\Exness-Live' : r'C:\MT5\Exness-Demo');
    }
    return null;
  }

  String _currencySymbol(String currency) {
    switch (currency.toUpperCase()) {
      case 'ZAR':
        return 'R';
      case 'GBP':
        return '£';
      case 'EUR':
        return '€';
      default:
        return r'$';
    }
  }

  String _formatCurrency(double amount) =>
      '${_currencySymbol(_accountCurrency)}${amount.toStringAsFixed(2)} $_accountCurrency';

  String _formatMarginLevel(double value) => value > 0 ? '${value.toStringAsFixed(2)}%' : '-';

  String _userScopedPrefKey(String baseKey, String userId) {
    final normalizedUserId = userId.trim();
    if (normalizedUserId.isEmpty) {
      return baseKey;
    }
    return '${baseKey}_$normalizedUserId';
  }

  String _modePrefKey(String baseKey, bool isLive, {String userId = ''}) {
    final modeKey = '${baseKey}_${isLive ? 'live' : 'demo'}';
    return _userScopedPrefKey(modeKey, userId);
  }

  String? _scopedString(SharedPreferences prefs, String baseKey, {String userId = '', bool allowLegacyFallback = false}) {
    final scopedValue = prefs.getString(_userScopedPrefKey(baseKey, userId));
    if (scopedValue != null) {
      return scopedValue;
    }
    if (allowLegacyFallback || userId.trim().isEmpty) {
      return prefs.getString(baseKey);
    }
    return null;
  }

  bool? _scopedBool(SharedPreferences prefs, String baseKey, {String userId = '', bool allowLegacyFallback = false}) {
    final scopedKey = _userScopedPrefKey(baseKey, userId);
    if (prefs.containsKey(scopedKey)) {
      return prefs.getBool(scopedKey);
    }
    if (allowLegacyFallback || userId.trim().isEmpty) {
      return prefs.getBool(baseKey);
    }
    return null;
  }

  double? _scopedDouble(SharedPreferences prefs, String baseKey, {String userId = '', bool allowLegacyFallback = false}) {
    final scopedKey = _userScopedPrefKey(baseKey, userId);
    if (prefs.containsKey(scopedKey)) {
      return prefs.getDouble(scopedKey);
    }
    if (allowLegacyFallback || userId.trim().isEmpty) {
      return prefs.getDouble(baseKey);
    }
    return null;
  }

  String _effectiveAccountNumber() {
    if (_isBinanceBroker) {
      return '';
    }
    if (_isFxcmBroker) {
      return _accountController.text.trim();
    }
    return _accountController.text.trim();
  }

  Future<void> _persistModeScopedCredentials() async {
    final prefs = await SharedPreferences.getInstance();
    final userId = prefs.getString('user_id') ?? '';
    if (_isBinanceBroker) {
      await prefs.setString(_modePrefKey('binance_api_key', _isLiveMode, userId: userId), _apiKeyController.text);
      await prefs.setString(_modePrefKey('binance_api_secret', _isLiveMode, userId: userId), _passwordController.text);
      await prefs.setString(_modePrefKey('binance_market', _isLiveMode, userId: userId), _serverController.text);
      return;
    }
    if (_isLunoBroker) {
      await prefs.setString(_modePrefKey('luno_api_key', _isLiveMode, userId: userId), _apiKeyController.text);
      await prefs.setString(_modePrefKey('luno_api_secret', _isLiveMode, userId: userId), _passwordController.text);
      await prefs.setString(_modePrefKey('luno_base_url', _isLiveMode, userId: userId), _serverController.text);
      return;
    }

    await prefs.setString(_modePrefKey('mt5_account', _isLiveMode, userId: userId), _accountController.text);
    await prefs.setString(_modePrefKey('mt5_password', _isLiveMode, userId: userId), _passwordController.text);
    await prefs.setString(_modePrefKey('mt5_server', _isLiveMode, userId: userId), _serverController.text);
    if (_isFxcmBroker) {
      await prefs.setString(_modePrefKey('fxcm_account', _isLiveMode, userId: userId), _accountController.text);
      await prefs.setString(_modePrefKey('fxcm_password', _isLiveMode, userId: userId), _passwordController.text);
      await prefs.setString(_modePrefKey('fxcm_server', _isLiveMode, userId: userId), _serverController.text);
    }
  }

  Future<void> _persistCurrentInputDraft() async {
    final prefs = await SharedPreferences.getInstance();
    final userId = prefs.getString('user_id') ?? '';
    await prefs.setString(_userScopedPrefKey('broker', userId), _selectedBroker);
    await prefs.setBool(_userScopedPrefKey('is_live_mode', userId), _isLiveMode);
    if (_isBinanceBroker) {
      await prefs.setString(_userScopedPrefKey('broker_api_key', userId), _apiKeyController.text);
      await prefs.setString(_userScopedPrefKey('binance_api_secret', userId), _passwordController.text);
      await prefs.setString(_userScopedPrefKey('binance_market', userId), _serverController.text);
      await prefs.remove(_userScopedPrefKey('account_number', userId));
    } else if (_isLunoBroker) {
      await prefs.setString(_userScopedPrefKey('luno_api_key', userId), _apiKeyController.text);
      await prefs.setString(_userScopedPrefKey('luno_api_secret', userId), _passwordController.text);
      await prefs.setString(_userScopedPrefKey('luno_base_url', userId), _serverController.text);
      await prefs.remove(_userScopedPrefKey('account_number', userId));
    } else if (_isFxcmBroker) {
      await prefs.setString(_userScopedPrefKey('fxcm_account_number', userId), _accountController.text);
      await prefs.setString(_userScopedPrefKey('fxcm_password', userId), _passwordController.text);
      await prefs.setString(_userScopedPrefKey('fxcm_server', userId), _serverController.text);
    } else {
      await prefs.setString(_userScopedPrefKey('account_number', userId), _accountController.text);
      await prefs.setString(_userScopedPrefKey('mt5_account', userId), _accountController.text);
      await prefs.setString(_userScopedPrefKey('mt5_password', userId), _passwordController.text);
      await prefs.setString(_userScopedPrefKey('mt5_server', userId), _serverController.text);
    }
    await prefs.setString(_userScopedPrefKey('broker_api_key', userId), _apiKeyController.text);
    await prefs.setString(_userScopedPrefKey('broker_username', userId), _usernameController.text);
    await _persistModeScopedCredentials();
  }

  Future<void> _restoreModeScopedCredentials() async {
    final prefs = await SharedPreferences.getInstance();
    final userId = prefs.getString('user_id') ?? '';
    if (_isBinanceBroker) {
      final modeApiKey = prefs.getString(_modePrefKey('binance_api_key', _isLiveMode, userId: userId));
      final modeApiSecret = prefs.getString(_modePrefKey('binance_api_secret', _isLiveMode, userId: userId));
      final modeMarket = prefs.getString(_modePrefKey('binance_market', _isLiveMode, userId: userId));
      final fallbackMarket = _scopedString(prefs, 'binance_market', userId: userId) ?? '';
      final computedServer = _defaultServerForSelectedBroker(isLiveOverride: _isLiveMode);

      setState(() {
        _accountController.clear();
        _apiKeyController.text = modeApiKey ?? (prefs.getString('broker_api_key') ?? '');
        _passwordController.text = modeApiSecret ?? (prefs.getString('binance_api_secret') ?? '');
        _serverController.text = (modeMarket != null && modeMarket.isNotEmpty)
            ? modeMarket
            : (fallbackMarket.isNotEmpty ? fallbackMarket : computedServer);
        _isConnected = false;
        _activeAccount = null;
      });
      return;
    }

    if (_isLunoBroker) {
      final modeApiKey = prefs.getString(_modePrefKey('luno_api_key', _isLiveMode, userId: userId));
      final modeApiSecret = prefs.getString(_modePrefKey('luno_api_secret', _isLiveMode, userId: userId));
      final modeBaseUrl = prefs.getString(_modePrefKey('luno_base_url', _isLiveMode, userId: userId));
      final fallbackBaseUrl = _scopedString(prefs, 'luno_base_url', userId: userId) ?? '';
      final computedServer = _defaultServerForSelectedBroker(isLiveOverride: _isLiveMode);

      setState(() {
        _accountController.clear();
        _apiKeyController.text = modeApiKey ?? (_scopedString(prefs, 'luno_api_key', userId: userId) ?? '');
        _passwordController.text = modeApiSecret ?? (_scopedString(prefs, 'luno_api_secret', userId: userId) ?? '');
        _serverController.text = (modeBaseUrl != null && modeBaseUrl.isNotEmpty)
            ? modeBaseUrl
            : (fallbackBaseUrl.isNotEmpty ? fallbackBaseUrl : computedServer);
        _isConnected = false;
        _activeAccount = null;
      });
      return;
    }

    final modeAccount = _isFxcmBroker
      ? prefs.getString(_modePrefKey('fxcm_account', _isLiveMode, userId: userId))
      : prefs.getString(_modePrefKey('mt5_account', _isLiveMode, userId: userId));
    final modePassword = _isFxcmBroker
      ? prefs.getString(_modePrefKey('fxcm_password', _isLiveMode, userId: userId))
      : prefs.getString(_modePrefKey('mt5_password', _isLiveMode, userId: userId));
    final modeServer = _isFxcmBroker
      ? prefs.getString(_modePrefKey('fxcm_server', _isLiveMode, userId: userId))
      : prefs.getString(_modePrefKey('mt5_server', _isLiveMode, userId: userId));
    final fallbackAccount = _isFxcmBroker
      ? (_scopedString(prefs, 'fxcm_account_number', userId: userId) ?? '')
      : (_scopedString(prefs, 'account_number', userId: userId) ?? _scopedString(prefs, 'mt5_account', userId: userId) ?? '');
    final fallbackPassword = _isFxcmBroker
      ? (_scopedString(prefs, 'fxcm_password', userId: userId) ?? '')
      : (_scopedString(prefs, 'mt5_password', userId: userId) ?? '');
    final fallbackServer = _isFxcmBroker
      ? (_scopedString(prefs, 'fxcm_server', userId: userId) ?? '')
      : (_scopedString(prefs, 'mt5_server', userId: userId) ?? '');
    final resolvedAccount = (modeAccount ?? fallbackAccount).trim();
    final computedServer = _defaultServerForSelectedBroker(
      isLiveOverride: _isLiveMode,
      accountNumber: resolvedAccount,
      fallbackServer: (modeServer != null && modeServer.isNotEmpty) ? modeServer : fallbackServer,
    );

    setState(() {
      _accountController.text = modeAccount ?? fallbackAccount;
      _passwordController.text = modePassword ?? fallbackPassword;
      _serverController.text = (modeServer != null && modeServer.isNotEmpty)
          ? modeServer
          : (fallbackServer.isNotEmpty ? fallbackServer : computedServer);
      _isConnected = false;
      _activeAccount = null;
    });
  }

  String _defaultServerForSelectedBroker({bool? isLiveOverride, String? accountNumber, String? fallbackServer}) {
    final isLive = isLiveOverride ?? _isLiveMode;
    if (_selectedBroker.toLowerCase() == 'exness') {
      return _resolveExnessServer(
        isLiveOverride: isLive,
        accountNumber: accountNumber,
        fallbackServer: fallbackServer,
      );
    }
    if (_isLunoBroker) {
      return fallbackServer ?? brokerServers[_selectedBroker] ?? 'https://api.luno.com';
    }
    if (_isFxcmBroker) {
      return isLive ? 'real' : 'demo';
    }
    return brokerServers[_selectedBroker] ?? '';
  }

  void _loadSavedAccounts() async {
    final accounts = BrokerConnectionService.getSavedAccounts()
        .where((a) => !a.brokerName.toLowerCase().contains('xm'))
        .toList();
    setState(() => _savedAccounts = accounts);
  }

  void _loadSavedCredentials() async {
    final prefs = await SharedPreferences.getInstance();
    final userId = prefs.getString('user_id') ?? '';
    final savedBroker = _scopedString(prefs, 'broker', userId: userId) ?? 'Exness';
    final normalizedSavedBroker = _sanitizeSelectedBroker(
      savedBroker.toLowerCase().contains('xm') ? 'Exness' : savedBroker,
    );
    final savedMode = _scopedBool(prefs, 'is_live_mode', userId: userId) ?? false;
    final isBinanceSavedBroker = normalizedSavedBroker.toLowerCase() == 'binance';
    final isLunoSavedBroker = normalizedSavedBroker.toLowerCase() == 'luno';
    final isFxcmSavedBroker = normalizedSavedBroker.toLowerCase() == 'fxcm';
    final modeAccount = isFxcmSavedBroker
      ? prefs.getString(_modePrefKey('fxcm_account', savedMode, userId: userId))
      : (isBinanceSavedBroker
          ? prefs.getString(_modePrefKey('binance_account', savedMode, userId: userId))
        : (isLunoSavedBroker
          ? prefs.getString(_modePrefKey('luno_account', savedMode, userId: userId))
          : prefs.getString(_modePrefKey('mt5_account', savedMode, userId: userId))));
    final modePassword = isFxcmSavedBroker
      ? prefs.getString(_modePrefKey('fxcm_password', savedMode, userId: userId))
      : (isBinanceSavedBroker
          ? prefs.getString(_modePrefKey('binance_api_secret', savedMode, userId: userId))
        : (isLunoSavedBroker
          ? prefs.getString(_modePrefKey('luno_api_secret', savedMode, userId: userId))
          : prefs.getString(_modePrefKey('mt5_password', savedMode, userId: userId))));
    final modeServer = isFxcmSavedBroker
      ? prefs.getString(_modePrefKey('fxcm_server', savedMode, userId: userId))
      : (isBinanceSavedBroker
          ? prefs.getString(_modePrefKey('binance_market', savedMode, userId: userId))
        : (isLunoSavedBroker
          ? prefs.getString(_modePrefKey('luno_base_url', savedMode, userId: userId))
          : prefs.getString(_modePrefKey('mt5_server', savedMode, userId: userId))));
    final savedAccount = isBinanceSavedBroker
      ? ''
      : (modeAccount ?? (isFxcmSavedBroker
          ? (_scopedString(prefs, 'fxcm_account_number', userId: userId) ?? '')
        : (isLunoSavedBroker
          ? ''
          : (_scopedString(prefs, 'account_number', userId: userId) ?? _scopedString(prefs, 'mt5_account', userId: userId) ?? ''))));
    final savedServer = modeServer ?? (isFxcmSavedBroker
      ? (_scopedString(prefs, 'fxcm_server', userId: userId) ?? '')
      : (isBinanceSavedBroker
          ? (_scopedString(prefs, 'binance_market', userId: userId) ?? '')
        : (isLunoSavedBroker
          ? (_scopedString(prefs, 'luno_base_url', userId: userId) ?? '')
          : (_scopedString(prefs, 'mt5_server', userId: userId) ?? ''))));
    setState(() {
      _selectedBroker = normalizedSavedBroker;
      _isLiveMode = savedMode;  // Load saved mode
      _accountController.text = isBinanceSavedBroker
        ? ''
        : savedAccount;
      _passwordController.text = modePassword ?? (isFxcmSavedBroker
        ? (_scopedString(prefs, 'fxcm_password', userId: userId) ?? '')
        : (isBinanceSavedBroker
            ? (_scopedString(prefs, 'binance_api_secret', userId: userId) ?? '')
            : (isLunoSavedBroker
                ? (_scopedString(prefs, 'luno_api_secret', userId: userId) ?? '')
                : (_scopedString(prefs, 'mt5_password', userId: userId) ?? ''))));
      _apiKeyController.text = isLunoSavedBroker
          ? (_scopedString(prefs, 'luno_api_key', userId: userId) ?? '')
          : (_scopedString(prefs, 'broker_api_key', userId: userId) ?? '');
      _usernameController.text = _scopedString(prefs, 'broker_username', userId: userId) ?? '';
      _isConnected = _scopedBool(prefs, 'broker_connected', userId: userId) ?? false;
      _accountBalance = _scopedDouble(prefs, 'account_balance', userId: userId) ?? 0;
      _accountEquity = _scopedDouble(prefs, 'account_equity', userId: userId) ?? 0;
      _accountFreeMargin = _scopedDouble(prefs, 'account_free_margin', userId: userId) ?? 0;
      _accountMargin = _scopedDouble(prefs, 'account_margin', userId: userId) ?? 0;
      _accountMarginLevel = _scopedDouble(prefs, 'account_margin_level', userId: userId) ?? 0;
      _accountProfit = _scopedDouble(prefs, 'account_profit', userId: userId) ?? 0;
      _accountCurrency = _scopedString(prefs, 'account_currency', userId: userId) ?? 'USD';
      _autoReconnectEnabled = prefs.getBool('auto_reconnect_enabled') ?? false;
      final computedServer = _defaultServerForSelectedBroker(
        isLiveOverride: _isLiveMode,
        accountNumber: savedAccount,
        fallbackServer: savedServer,
      );
      _serverController.text = savedServer.isNotEmpty
          ? savedServer
          : computedServer;
      final connectionTimeStr = _scopedString(prefs, 'connection_time', userId: userId);
      if (connectionTimeStr != null) {
        _lastConnectionTime = DateTime.parse(connectionTimeStr);
      }
    });
  }

  void _saveCredentials() async {
    // Require test connection before saving
    if (!_isConnected) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('❌ Must test connection first (click "Test Connection" button)'),
          backgroundColor: Colors.orange,
          duration: Duration(seconds: 4),
        ),
      );
      return;
    }
    
    // Prevent double-save
    if (_showSuccess) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('✅ Already saved - please wait'),
          backgroundColor: Colors.green,
          duration: Duration(seconds: 2),
        ),
      );
      return;
    }

    final effectiveAccountNumber = _effectiveAccountNumber();
    final missingMt5 = _isMt5Broker && (_accountController.text.isEmpty || _passwordController.text.isEmpty);
    final missingBinance = (_isBinanceBroker || _isLunoBroker) && (_apiKeyController.text.isEmpty || _passwordController.text.isEmpty);
    final hasFxcmUsernamePassword = _usernameController.text.isNotEmpty && _passwordController.text.isNotEmpty;
    final hasFxcmToken = _apiKeyController.text.isNotEmpty;
    final missingFxcm = _isFxcmBroker && (!hasFxcmUsernamePassword && !hasFxcmToken);

    if (missingMt5 || missingBinance || missingFxcm) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please fill all required broker fields')),
      );
      return;
    }

    final prefs = await SharedPreferences.getInstance();
    final userId = prefs.getString('user_id') ?? '';
    final mt5TerminalPath = _preferredMt5TerminalPath();
    await prefs.setString(_userScopedPrefKey('broker', userId), _selectedBroker);
    if (_isLunoBroker) {
      await prefs.setString(_userScopedPrefKey('luno_api_key', userId), _apiKeyController.text);
      await prefs.setString(_userScopedPrefKey('luno_api_secret', userId), _passwordController.text);
      await prefs.setString(_userScopedPrefKey('luno_base_url', userId), _serverController.text);
      await prefs.remove(_userScopedPrefKey('account_number', userId));
    } else {
      await prefs.setString(_userScopedPrefKey('mt5_account', userId), _accountController.text);
      await prefs.setString(_userScopedPrefKey('mt5_password', userId), _passwordController.text);
      await prefs.setString(_userScopedPrefKey('mt5_server', userId), _serverController.text);
      await prefs.setString(_userScopedPrefKey('broker_api_key', userId), _apiKeyController.text);
    }
    await prefs.setString(_userScopedPrefKey('broker_username', userId), _usernameController.text);
    if (mt5TerminalPath != null) {
      await prefs.setString(_userScopedPrefKey('mt5_terminal_path', userId), mt5TerminalPath);
    }

    if (_isConnected) {
      await prefs.setBool(_userScopedPrefKey('broker_connected', userId), true);
      await prefs.setString(_userScopedPrefKey('connection_time', userId), DateTime.now().toIso8601String());
      await prefs.setDouble(_userScopedPrefKey('account_balance', userId), _accountBalance);
      await prefs.setDouble(_userScopedPrefKey('account_equity', userId), _accountEquity);
      await prefs.setDouble(_userScopedPrefKey('account_free_margin', userId), _accountFreeMargin);
      await prefs.setDouble(_userScopedPrefKey('account_margin', userId), _accountMargin);
      await prefs.setDouble(_userScopedPrefKey('account_margin_level', userId), _accountMarginLevel);
      await prefs.setDouble(_userScopedPrefKey('account_profit', userId), _accountProfit);
    }

    await _persistModeScopedCredentials();

    if (mounted) {
      // Save to backend via BrokerCredentialsService
      final brokerService = Provider.of<BrokerCredentialsService>(context, listen: false);
      final success = await brokerService.saveCredential(
        broker: _selectedBroker,
        accountNumber: effectiveAccountNumber,
        password: _passwordController.text,
        server: _serverController.text,
        isLive: _isLiveMode,
        apiKey: (_isBinanceBroker || _isLunoBroker) && _apiKeyController.text.isNotEmpty ? _apiKeyController.text : null,
        apiSecret: (_isBinanceBroker || _isLunoBroker) && _passwordController.text.isNotEmpty ? _passwordController.text : null,
        username: _usernameController.text.isNotEmpty ? _usernameController.text : null,
        mt5TerminalPath: mt5TerminalPath,
      );

      if (!success) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('❌ Failed to save credentials: ${brokerService.errorMessage}'),
              backgroundColor: Colors.red,
            ),
          );
        }
        return;
      }

      // Also sync with local trading service
      final tradingService = Provider.of<TradingService>(context, listen: false);
      await tradingService.syncBrokerAccount(
        brokerName: _selectedBroker,
        accountNumber: _isFxcmBroker ? _accountController.text.trim() : effectiveAccountNumber,
        server: _serverController.text,
      );
    }

    setState(() => _showSuccess = true);
    Future.delayed(const Duration(seconds: 2), () {
      if (mounted) setState(() => _showSuccess = false);
    });
  }

  /// Check if Exness is available on the backend
  Future<Map<String, dynamic>> _checkExnessAvailability() async {
    try {
      final baseUrl = EnvironmentConfig.apiUrl;
      final response = await http.get(
        Uri.parse('$baseUrl/api/brokers/check-exness'),
      ).timeout(const Duration(seconds: 5));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        return {
          'available': data['available'] ?? false,
          'installed': data['installed'] ?? false,
          'path_exists': data['path_exists'] ?? false,
          'version': data['version'] ?? 'Unknown',
          'error': data['error'] ?? data['reason'],
        };
      } else {
        return {
          'available': false,
          'error': 'Failed to check Exness availability',
        };
      }
    } catch (e) {
      return {
        'available': false,
        'error': 'Error checking Exness: $e',
      };
    }
  }

  /// Check if PXBT MT5 is available on the backend
  Future<Map<String, dynamic>> _checkPxbtAvailability() async {
    try {
      final baseUrl = EnvironmentConfig.apiUrl;
      final response = await http.get(
        Uri.parse('$baseUrl/api/brokers/check-pxbt'),
      ).timeout(const Duration(seconds: 5));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        return {
          'available': data['available'] ?? false,
          'installed': data['installed'] ?? false,
          'path_exists': data['path_exists'] ?? false,
          'version': data['version'] ?? 'Unknown',
          'error': data['error'] ?? data['reason'],
        };
      } else {
        return {
          'available': false,
          'error': 'Failed to check PXBT availability',
        };
      }
    } catch (e) {
      return {
        'available': false,
        'error': 'Error checking PXBT: $e',
      };
    }
  }

  void _testConnection() async {
    await _persistCurrentInputDraft();

    // Check Exness/PXBT availability first when selected
    if (_isExnessBroker) {
      setState(() => _isTestingConnection = true);
      
      final exnessCheck = await _checkExnessAvailability();
      
      // Availability precheck is advisory only; still allow real credential test.
      if (exnessCheck['available'] != true) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('⚠️ Exness precheck warning: ${exnessCheck['error'] ?? "MT5 path/IPC not confirmed yet"}. Continuing with connection test...'),
              backgroundColor: Colors.orange,
              duration: const Duration(seconds: 4),
            ),
          );
        }
      }
    }

    if (_isPxbtBroker) {
      setState(() => _isTestingConnection = true);

      final pxbtCheck = await _checkPxbtAvailability();

      // Availability precheck is advisory only; still allow real credential test.
      if (pxbtCheck['available'] != true) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('⚠️ PXBT precheck warning: ${pxbtCheck['error'] ?? "MT5 path/IPC not confirmed yet"}. Continuing with connection test...'),
              backgroundColor: Colors.orange,
              duration: const Duration(seconds: 4),
            ),
          );
        }
      }
    }

    final effectiveAccountNumber = _effectiveAccountNumber();
    final missingMt5 = (_isMt5Broker || _isExnessBroker) && (_accountController.text.isEmpty || _passwordController.text.isEmpty);
    final missingBinance = (_isBinanceBroker || _isLunoBroker) && (_apiKeyController.text.isEmpty || _passwordController.text.isEmpty);
    final hasFxcmUsernamePassword = _usernameController.text.isNotEmpty && _passwordController.text.isNotEmpty;
    final hasFxcmToken = _apiKeyController.text.isNotEmpty;
    final missingFxcm = _isFxcmBroker && (!hasFxcmUsernamePassword && !hasFxcmToken);

    if (missingMt5 || missingBinance || missingFxcm) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please fill all required connection fields')),
      );
      return;
    }

    setState(() => _isTestingConnection = true);

    // Show loading message with context about MT5 connection delays
    if (_isExnessBroker) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('🔌 Testing Exness connection...'),
          duration: const Duration(seconds: 3),
          backgroundColor: Colors.blue.withOpacity(0.7),
        ),
      );
    }
    if (_isPxbtBroker) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('🔌 Testing PXBT connection... (may take 30-60 seconds)'),
          duration: const Duration(seconds: 3),
          backgroundColor: Colors.blue.withOpacity(0.7),
        ),
      );
    }

    try {
      final mt5TerminalPath = _preferredMt5TerminalPath();
      final result = await BrokerConnectionService.testConnection(
        broker: _selectedBroker,
        accountNumber: effectiveAccountNumber,
        password: _passwordController.text,
        server: _serverController.text,
        apiKey: (_isBinanceBroker || _isLunoBroker || _isFxcmBroker)
            ? (_apiKeyController.text.isEmpty ? null : _apiKeyController.text)
            : null,
        apiSecret: (_isBinanceBroker || _isLunoBroker) ? _passwordController.text : null,
        username: _usernameController.text.isEmpty ? null : _usernameController.text,
        accountId: effectiveAccountNumber,
        market: _isBinanceBroker ? _serverController.text : null,
        mt5TerminalPath: mt5TerminalPath,
        isLive: _isLiveMode,
      );

      if (!mounted) return;

      if (result['success'] == true) {
        // Backend returns: credential_id, broker, account_number, balance, currency, status, timestamp
        final credentialId = result['credential_id'] as String?;
        final balance = (result['balance'] ?? 10000.0).toDouble();
        final equity = _doubleValue(result['equity'] ?? balance);
        final freeMargin = _doubleValue(result['free_margin'] ?? 0.0);
        final margin = _doubleValue(result['margin'] ?? 0.0);
        final marginLevel = _doubleValue(result['margin_level'] ?? 0.0);
        final profit = _doubleValue(result['total_pl'] ?? 0.0);
        final isDemo = !(result['is_live'] == true);
        final currency = (result['currency'] as String? ?? 'USD').toUpperCase();
        final status = (result['status'] as String? ?? 'SAVED').toUpperCase();
        final isConnected = result['connected'] == true;
        final warning = result['warning'] as String?;
        final currencySymbol = currency == 'ZAR' ? 'R' : (currency == 'GBP' ? '£' : (currency == 'EUR' ? '€' : r'$'));
        
        // Create BrokerAccount from backend response
        final account = BrokerAccount(
          id: credentialId ?? '${_selectedBroker}_${_accountController.text}',
          brokerName: _selectedBroker,
          accountNumber: (result['account_number'] as String?) ?? _accountController.text,
          server: _serverController.text,
          isDemo: isDemo,
          accountBalance: balance,
          leverage: 100,
          spreadAverage: 1.5,
          createdAt: DateTime.now(),
          lastConnected: DateTime.now(),
          isActive: true,
          connectionStatus: status,
        );

        setState(() {
          _isTestingConnection = false;
          _isConnected = isConnected;
          _activeAccount = account;
          _lastConnectionTime = isConnected ? DateTime.now() : null;
          _accountBalance = balance;
          _accountEquity = equity;
          _accountFreeMargin = freeMargin;
          _accountMargin = margin;
          _accountMarginLevel = marginLevel;
          _accountProfit = profit;
          _accountCurrency = currency;
          _accountController.text = account.accountNumber;
        });

        final prefs = await SharedPreferences.getInstance();
        final userId = prefs.getString('user_id') ?? '';
        await prefs.setBool(_userScopedPrefKey('broker_connected', userId), isConnected);
        if (_lastConnectionTime != null) {
          await prefs.setString(_userScopedPrefKey('connection_time', userId), _lastConnectionTime!.toIso8601String());
        } else {
          await prefs.remove(_userScopedPrefKey('connection_time', userId));
        }
        await prefs.setDouble(_userScopedPrefKey('account_balance', userId), _accountBalance);
        await prefs.setDouble(_userScopedPrefKey('account_equity', userId), _accountEquity);
        await prefs.setDouble(_userScopedPrefKey('account_free_margin', userId), _accountFreeMargin);
        await prefs.setDouble(_userScopedPrefKey('account_margin', userId), _accountMargin);
        await prefs.setDouble(_userScopedPrefKey('account_margin_level', userId), _accountMarginLevel);
        await prefs.setDouble(_userScopedPrefKey('account_profit', userId), _accountProfit);
        await prefs.setBool(_userScopedPrefKey('is_live_mode', userId), _isLiveMode);
        await prefs.setString(_userScopedPrefKey('account_currency', userId), currency);
        await prefs.setString(
          _userScopedPrefKey('verified_broker_snapshot', userId),
          jsonEncode({
            'broker': _selectedBroker,
            'accountNumber': account.accountNumber,
            'balance': _accountBalance,
            'equity': _accountEquity,
            'marginFree': _accountFreeMargin,
            'margin': _accountMargin,
            'margin_level': _accountMarginLevel,
            'total_pl': _accountProfit,
            'currency': currency,
            'displayCurrency': currency,
            'connected': isConnected,
            'mode': _isLiveMode ? 'Live' : 'Demo',
            'is_live': _isLiveMode,
            'last_update': _lastConnectionTime?.toIso8601String(),
            'dataSource': 'verified_broker_test',
          }),
        );
        if (credentialId != null) {
          await prefs.setString(_userScopedPrefKey('credential_id', userId), credentialId);
          await prefs.setString(_userScopedPrefKey('broker_name', userId), _selectedBroker);
          if (_isFxcmBroker) {
            await prefs.setString(_userScopedPrefKey('fxcm_account_number', userId), account.accountNumber);
          } else if (_isLunoBroker) {
            await prefs.remove(_userScopedPrefKey('account_number', userId));
          } else {
            await prefs.setString(_userScopedPrefKey('account_number', userId), account.accountNumber);
            await prefs.setString(_userScopedPrefKey('mt5_account', userId), account.accountNumber);
          }
        }

        await _persistModeScopedCredentials();
          await prefs.setString(
            _userScopedPrefKey('preferred_broker_display', userId),
            _normalizeBrokerDisplayName(_selectedBroker),
          );

        if (mounted) {
          final tradingService = Provider.of<TradingService>(context, listen: false);
          if (isConnected) {
            await tradingService.syncBrokerAccount(
              brokerName: _selectedBroker,
              accountNumber: account.accountNumber,
              server: _serverController.text,
            );
          }
        }

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              isConnected
                  ? '✓ Connected! Balance: $currencySymbol${balance.toStringAsFixed(2)} $currency'
                  : (warning ?? 'Credential saved, but MT5 warmup is still pending.'),
            ),
            backgroundColor: isConnected ? AppColors.successColor : Colors.orange,
            duration: const Duration(seconds: 3),
          ),
        );
      } else {
        setState(() => _isTestingConnection = false);
        final isBinanceAuthFailure = _isBinanceBroker && result['errorCode'] == 'AUTH_FAILED';
        final message = (result['message'] ?? 'Connection failed').toString();
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              isBinanceAuthFailure
                  ? '✗ $message'
                  : '✗ $message',
            ),
            backgroundColor: AppColors.dangerColor,
            duration: Duration(seconds: isBinanceAuthFailure ? 8 : 3),
          ),
        );
      }
    } catch (e) {
      setState(() => _isTestingConnection = false);
      print('DEBUG: Test connection error: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('✗ Error: $e'),
          backgroundColor: AppColors.dangerColor,
        ),
      );
    }
  }

  void _startAutoReconnect() async {
    if (_activeAccount == null) return;

    setState(() => _autoReconnectEnabled = true);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('auto_reconnect_enabled', true);

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('✓ Auto-reconnect enabled'),
        backgroundColor: AppColors.successColor,
      ),
    );
  }

  void _navigateToAnalytics() {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (context) => const BrokerAnalyticsDashboard(),
      ),
    );
  }

  @override
  void dispose() {
    _serverController.dispose();
    _accountController.dispose();
    _passwordController.dispose();
    _apiKeyController.dispose();
    _usernameController.dispose();
    BrokerConnectionService.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
      appBar: AppBar(
        title: const Row(
          children: [
            LogoWidget(size: 40, showText: false),
            SizedBox(width: 12),
            Flexible(
              child: Text('Broker Integration'),
            ),
          ],
        ),
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.dashboard_rounded),
            tooltip: 'Home',
            onPressed: () {
              Navigator.pushAndRemoveUntil(
                context,
                MaterialPageRoute(builder: (_) => const DashboardScreen()),
                (route) => route.isFirst,
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.assessment_outlined),
            tooltip: 'Reports',
            onPressed: () {
              Navigator.push(context, MaterialPageRoute(builder: (_) => const ConsolidatedReportsScreen()));
            },
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  IconButton(
                    icon: const Icon(Icons.arrow_back),
                    onPressed: widget.onBackPressed ?? () => Navigator.of(context).pop(),
                  ),
                  const Text(
                    'Broker Integration',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                ],
              ),
              if (_isConnected)
                ElevatedButton.icon(
                  onPressed: _navigateToAnalytics,
                  icon: const Icon(Icons.analytics),
                  label: const Text('Analytics'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.primaryColor,
                  ),
                ),
            ],
          ),
          const SizedBox(height: 16),
          if (_showSuccess) ...[
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.successColor,
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Row(
                children: [
                  Icon(Icons.check_circle, color: Colors.white),
                  SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      'Broker credentials saved successfully!',
                      style: TextStyle(color: Colors.white),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            // ✅ Quick Action Buttons After Successful Connection
            Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [
                    const Color(0xFF1A237E).withOpacity(0.5),
                    const Color(0xFF0D47A1).withOpacity(0.5),
                  ],
                ),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.white.withOpacity(0.1)),
              ),
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'What\'s Next?',
                    style: GoogleFonts.poppins(
                      color: Colors.white,
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 16),
                  // Create Bot Button
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: () {
                        Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (context) => const BotConfigurationRoute(),
                          ),
                        );
                      },
                      icon: const Icon(Icons.smart_toy),
                      label: const Text('Create Trading Bot'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF7C4DFF),
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 12),
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: () {
                        Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (context) => const BotConfigurationRoute(
                              focusTestedTemplates: true,
                            ),
                          ),
                        );
                      },
                      icon: const Icon(Icons.auto_awesome),
                      label: const Text('Use Tested Binance Template'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFFF3BA2F).withOpacity(0.18),
                        foregroundColor: const Color(0xFFF3BA2F),
                        padding: const EdgeInsets.symmetric(vertical: 12),
                        side: const BorderSide(color: Color(0xFFF3BA2F)),
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  // View Active Bots Button
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: () {
                        Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (context) => const BotDashboardScreen(),
                          ),
                        );
                      },
                      icon: const Icon(Icons.dashboard),
                      label: const Text('View Active Bots'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF00E5FF).withOpacity(0.2),
                        foregroundColor: const Color(0xFF00E5FF),
                        padding: const EdgeInsets.symmetric(vertical: 12),
                        side: const BorderSide(color: Color(0xFF00E5FF)),
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  // Go to Dashboard Button
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: () {
                        Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (context) => const DashboardScreen(),
                          ),
                        );
                      },
                      icon: const Icon(Icons.home),
                      label: const Text('Go to Dashboard'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF69F0AE).withOpacity(0.15),
                        foregroundColor: const Color(0xFF69F0AE),
                        padding: const EdgeInsets.symmetric(vertical: 12),
                        side: const BorderSide(color: Color(0xFF69F0AE)),
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 32),
          ] else
            const SizedBox(height: 20),
          Text(
            _isBinanceBroker
              ? 'Binance API Connection'
              : _isLunoBroker
                ? 'Luno API Connection'
                : _isFxcmBroker
                  ? 'FXCM Connection'
                  : 'MT5 Broker Connection',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: 8),
          Text(
            _isBinanceBroker
              ? 'Connect your funded Binance account for crypto bot trading'
              : _isLunoBroker
                ? 'Connect your Luno account for crypto spot trading'
                : _isFxcmBroker
                  ? 'Connect your FXCM Trading Station account for dashboards and account analytics'
                  : 'Connect your MetaTrader 5 account for automated trading',
            style: Theme.of(context).textTheme.bodySmall,
          ),
          const SizedBox(height: 24),
          Text(
            'Select Your Broker',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 12),
          Card(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              child: DropdownButton<String>(
                value: _selectedBroker,
                isExpanded: true,
                underline: const SizedBox(),
                onChanged: (newValue) {
                  if (newValue != null) {
                    setState(() {
                      _selectedBroker = _sanitizeSelectedBroker(newValue);
                      if (_isBinanceBroker || _isLunoBroker) {
                        _accountController.clear();
                        _usernameController.clear();
                      }
                      _serverController.text = _defaultServerForSelectedBroker();
                    });
                    _restoreModeScopedCredentials();
                    _persistPreferredBrokerChoice(newValue);
                  }
                },
                items: brokers.map((broker) => DropdownMenuItem<String>(
                    value: broker,
                    child: Text(broker),
                  )).toList(),
              ),
            ),
          ),
          const SizedBox(height: 24),
          if (_isMt5Broker) ...[
            Text(
              'MT5 Server',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 12),
            if (_isExnessBroker) ...[
              // Exness: quick-pick chips + free-text field
              Wrap(
                spacing: 8,
                runSpacing: 4,
                children: [
                  for (final srv in [
                    'Exness-MT5Real27',
                    'Exness-MT5Real30',
                    'MT5Real30',
                    'Exness-MT5Real',
                    'Exness-MT5Trial9',
                    'Exness-MT5Trial',
                  ])
                    ChoiceChip(
                      label: Text(srv, style: const TextStyle(fontSize: 12)),
                      selected: _serverController.text == srv,
                      onSelected: (_) => setState(() => _serverController.text = srv),
                      selectedColor: Colors.orange.shade700,
                    ),
                ],
              ),
              const SizedBox(height: 8),
            ],
            TextField(
              controller: _serverController,
              readOnly: false,
              decoration: InputDecoration(
                labelText: 'Server',
                hintText: _isExnessBroker
                    ? 'e.g. Exness-MT5Real30  (check your Exness portal)'
                    : 'e.g. MetaQuotes-Demo',
                border: const OutlineInputBorder(),
                prefixIcon: const Icon(Icons.storage),
                filled: true,
                fillColor: Colors.grey[900],
              ),
            ),
            const SizedBox(height: 24),
            Text(
              'MT5 Account Number',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _accountController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(
                labelText: 'Account Number (your MT5 account ID)',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.account_circle),
                hintText: 'demo or 136372035',
              ),
            ),
            const SizedBox(height: 24),
            Text(
              'MT5 Password',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _passwordController,
              obscureText: true,
              decoration: const InputDecoration(
                labelText: 'MT5 Password (your broker password)',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.lock),
                hintText: 'demo123',
              ),
            ),
          ],
          if (_isFxcmBroker) ...[
            // FXCM Info Box
            Container(
              padding: const EdgeInsets.all(14),
              margin: const EdgeInsets.only(bottom: 24),
              decoration: BoxDecoration(
                color: Colors.blue.withOpacity(0.08),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.blue.withOpacity(0.3)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '🌐 FXCM Trading Station',
                    style: GoogleFonts.poppins(
                      fontWeight: FontWeight.w700,
                      fontSize: 14,
                      color: Colors.blue.shade900,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Use one of these FXCM login methods:\n\n1. Login ID + Password\n   Use this when the backend supports ForexConnect.\n\n2. Login ID + API Access Token\n   Use a token generated inside FXCM Trading Station.\n\nThe Trading Account ID field below is optional. Leave it blank if you only know your Login ID and let the backend resolve the actual account row.\n\nTo get your API token:\n1. Log into FXCM Trading Station\n2. Open Settings\n3. Click "Generate API Token"\n4. Copy the token into the optional field below',
                    style: GoogleFonts.poppins(
                      fontSize: 12,
                      color: const Color(0xFF16324F),
                      height: 1.4,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    'If you see "failed to resolve api.fxcm.com", your backend VPS cannot resolve FXCM hosts. That is a DNS/network problem on the server, not a bad FXCM login.',
                    style: GoogleFonts.poppins(
                      fontWeight: FontWeight.w600,
                      fontSize: 11,
                      color: Colors.orange.shade900,
                      height: 1.4,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    'Supported trading pairs:',
                    style: GoogleFonts.poppins(
                      fontWeight: FontWeight.w600,
                      fontSize: 11,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    'EUR/USD, GBP/USD, USD/JPY, USD/CHF, AUD/USD, NZD/USD, USD/CAD, XAU/USD, XAG/USD',
                    style: GoogleFonts.poppins(
                      fontSize: 11,
                      color: Colors.white60,
                      fontStyle: FontStyle.italic,
                    ),
                  ),
                ],
              ),
            ),
            
            Text('Login ID', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 12),
            TextField(
              controller: _usernameController,
              decoration: const InputDecoration(
                labelText: 'FXCM Login ID',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.person),
                hintText: 'e.g. D291208899',
              ),
            ),
            const SizedBox(height: 24),

            Text('Trading Account ID (Optional)', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 12),
            TextField(
              controller: _accountController,
              decoration: const InputDecoration(
                labelText: 'FXCM Trading Account ID',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.badge_outlined),
                hintText: 'Leave blank to auto-resolve after login',
              ),
            ),
            const SizedBox(height: 24),

            Text('Password', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 12),
            TextField(
              controller: _passwordController,
              obscureText: true,
              decoration: const InputDecoration(
                labelText: 'FXCM Trading Station Password',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.lock),
                hintText: 'Required for Login ID + Password mode',
              ),
            ),
            const SizedBox(height: 24),

            Text('API Access Token (Optional)', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 12),
            TextField(
              controller: _apiKeyController,
              decoration: const InputDecoration(
                labelText: 'FXCM API Token',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.vpn_key),
                hintText: 'Paste token from Trading Station if using token auth',
              ),
            ),
            const SizedBox(height: 24),
          ],
          if (_isBinanceBroker) ...[
            Text('Binance API Key', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 12),
            TextField(
              controller: _apiKeyController,
              decoration: const InputDecoration(
                labelText: 'Client Binance API Key',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.vpn_key),
                hintText: 'Use this logged-in client\'s Binance API key',
              ),
            ),
            const SizedBox(height: 24),
            Text('Binance API Secret', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 12),
            TextField(
              controller: _passwordController,
              obscureText: true,
              decoration: const InputDecoration(
                labelText: 'Client Binance API Secret',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.lock),
                hintText: 'Never reuse an admin or shared master key',
              ),
            ),
            const SizedBox(height: 24),
            Text('Trading Market', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 12),
            Card(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                child: DropdownButton<String>(
                  value: _serverController.text.isEmpty ? 'spot' : _serverController.text,
                  isExpanded: true,
                  underline: const SizedBox(),
                  onChanged: (value) {
                    if (value != null) {
                      setState(() {
                        _serverController.text = value;
                        // Do not overwrite account — Binance has no account number
                      });
                    }
                  },
                  items: const [
                    DropdownMenuItem(value: 'spot', child: Text('Spot')),
                    DropdownMenuItem(value: 'futures', child: Text('Futures')),
                  ],
                ),
              ),
            ),
          ],
          if (_isLunoBroker) ...[
            Text('Luno API Key', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 12),
            TextField(
              controller: _apiKeyController,
              decoration: const InputDecoration(
                labelText: 'Luno API Key',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.vpn_key),
                hintText: 'Paste your Luno API key',
              ),
            ),
            const SizedBox(height: 24),
            Text('Luno API Secret', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 12),
            TextField(
              controller: _passwordController,
              obscureText: true,
              decoration: const InputDecoration(
                labelText: 'Luno API Secret',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.lock),
                hintText: 'Paste your Luno API secret',
              ),
            ),
            const SizedBox(height: 24),
            Text('Base URL', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 12),
            TextField(
              controller: _serverController,
              decoration: const InputDecoration(
                labelText: 'Luno Base URL',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.language),
                hintText: 'https://api.luno.com',
              ),
            ),
            const SizedBox(height: 24),
          ],
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: const Color(0xFFF0B90B).withOpacity(0.12),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: const Color(0xFFF0B90B).withOpacity(0.5)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(Icons.security, color: const Color(0xFFF0B90B), size: 20),
                    const SizedBox(width: 8),
                    Text(
                      'Security Instructions',
                      style: GoogleFonts.poppins(
                        fontWeight: FontWeight.w700,
                        color: Colors.white,
                        fontSize: 14,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  'Each client must connect their own API credentials. Keep withdrawals disabled and restrict API access to trusted IPs before enabling live trading.',
                  style: GoogleFonts.poppins(
                    fontSize: 13,
                    color: Colors.white.withOpacity(0.9),
                    height: 1.4,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          Text(
            'Account Mode',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 12),
          Card(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              child: Row(
                children: [
                  Expanded(
                    child: RadioListTile<bool>(
                      title: const Text('DEMO'),
                      subtitle: const Text('Paper trading'),
                      value: false,
                      groupValue: _isLiveMode,
                      onChanged: (value) {
                        if (value != null) {
                          setState(() {
                            _isLiveMode = value;
                          });
                          _restoreModeScopedCredentials();
                        }
                      },
                    ),
                  ),
                  Expanded(
                    child: RadioListTile<bool>(
                      title: const Text('LIVE'),
                      subtitle: const Text('Real trading'),
                      value: true,
                      groupValue: _isLiveMode,
                      onChanged: (value) {
                        if (value != null) {
                          setState(() {
                            _isLiveMode = value;
                          });
                          _restoreModeScopedCredentials();
                        }
                      },
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 32),
          // Connection Status Card
          Container(
            margin: const EdgeInsets.only(bottom: 20),
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: const Color(0xFF1A1F3A),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(
                color: _isConnected 
                  ? AppColors.successColor.withOpacity(0.3)
                  : Colors.orange.withOpacity(0.2),
              ),
              boxShadow: [
                BoxShadow(
                  color: (_isConnected ? AppColors.successColor : Colors.orange).withOpacity(0.15),
                  blurRadius: 12,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Status header
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Row(
                      children: [
                        Container(
                          width: 14,
                          height: 14,
                          margin: const EdgeInsets.only(bottom: 2),
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: _isConnected ? AppColors.successColor : Colors.orange,
                            boxShadow: [
                              BoxShadow(
                                color: (_isConnected ? AppColors.successColor : Colors.orange).withOpacity(0.5),
                                blurRadius: 8,
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(width: 10),
                        Text(
                          _isConnected ? 'CONNECTED ✓' : 'Status: Not Connected',
                          style: GoogleFonts.poppins(
                            color: _isConnected ? AppColors.successColor : Colors.orange,
                            fontWeight: FontWeight.bold,
                            fontSize: 15,
                          ),
                        ),
                      ],
                    ),
                    if (_isConnected)
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                        decoration: BoxDecoration(
                          color: _isLiveMode 
                            ? Colors.red.withOpacity(0.25)
                            : Colors.orange.withOpacity(0.25),
                          borderRadius: BorderRadius.circular(14),
                          border: Border.all(
                            color: _isLiveMode ? Colors.red : Colors.orange,
                          ),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(
                              _isLiveMode ? Icons.warning : Icons.school,
                              color: _isLiveMode ? Colors.red : Colors.orange,
                              size: 16,
                            ),
                            const SizedBox(width: 6),
                            Text(
                              _isLiveMode ? 'LIVE' : 'DEMO',
                              style: GoogleFonts.poppins(
                                color: _isLiveMode ? Colors.red : Colors.orange,
                                fontWeight: FontWeight.bold,
                                fontSize: 13,
                              ),
                            ),
                          ],
                        ),
                      ),
                  ],
                ),
                if (_isConnected) ...[
                  const SizedBox(height: 14),
                  Text(
                    'Broker Status: CONNECTED',
                    style: GoogleFonts.poppins(
                      color: AppColors.successColor,
                      fontWeight: FontWeight.bold,
                      fontSize: 13,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: AppColors.successColor.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: AppColors.successColor.withOpacity(0.3),
                      ),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Connected Account Snapshot:',
                          style: GoogleFonts.poppins(
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                            fontSize: 13,
                          ),
                        ),
                        const SizedBox(height: 10),
                        _buildStatusInfoRow('Account', _accountController.text),
                        const SizedBox(height: 8),
                        _buildStatusInfoRow('Connection', _lastConnectionTime?.toString().split('.')[0] ?? 'N/A'),
                        const SizedBox(height: 8),
                        _buildStatusInfoRow('Balance', _formatCurrency(_accountBalance)),
                        const SizedBox(height: 8),
                        _buildStatusInfoRow('Equity', _formatCurrency(_accountEquity)),
                        const SizedBox(height: 8),
                        _buildStatusInfoRow('Free Margin', _formatCurrency(_accountFreeMargin)),
                        const SizedBox(height: 8),
                        _buildStatusInfoRow('Margin', _formatCurrency(_accountMargin)),
                        const SizedBox(height: 8),
                        _buildStatusInfoRow('Margin Level', _formatMarginLevel(_accountMarginLevel)),
                        const SizedBox(height: 8),
                        _buildStatusInfoRow('P/L', _formatCurrency(_accountProfit)),
                      ],
                    ),
                  ),
                ] else ...[
                  const SizedBox(height: 12),
                  Text(
                    'Click "Test Connection" to validate credentials',
                    style: GoogleFonts.poppins(
                      fontSize: 12,
                      color: Colors.white70,
                    ),
                  ),
                ],
              ],
            ),
          ),
          // Auto-reconnect checkbox
          if (_isConnected)
            Padding(
              padding: const EdgeInsets.only(bottom: 16),
              child: CheckboxListTile(
                title: Text(
                  'Enable Auto-Reconnect',
                  style: GoogleFonts.poppins(fontSize: 13),
                ),
                value: _autoReconnectEnabled,
                onChanged: (value) {
                  if (value == true) {
                    _startAutoReconnect();
                  }
                },
                contentPadding: EdgeInsets.zero,
              ),
            ),
          // Buttons
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: _saveCredentials,
              icon: const Icon(Icons.save, size: 20, color: Colors.white),
              label: Text(
                'Save Credentials',
                style: GoogleFonts.poppins(
                  fontSize: 15,
                  fontWeight: FontWeight.w600,
                  color: Colors.white,
                  letterSpacing: 0.5,
                ),
              ),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primaryColor,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                elevation: 4,
              ),
            ),
          ),
          const SizedBox(height: 12),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: _isTestingConnection ? null : _testConnection,
              icon: _isTestingConnection
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        valueColor: AlwaysStoppedAnimation(Colors.white),
                      ),
                    )
                  : const Icon(Icons.cloud_sync, size: 20, color: Colors.white),
              label: Text(
                _isTestingConnection ? 'Testing Connection...' : 'Test Connection',
                style: GoogleFonts.poppins(
                  fontSize: 15,
                  fontWeight: FontWeight.w600,
                  color: Colors.white,
                  letterSpacing: 0.5,
                ),
              ),
              style: ElevatedButton.styleFrom(
                backgroundColor: _isConnected ? AppColors.successColor : AppColors.primaryColor,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                elevation: 4,
              ),
            ),
          ),
          if (_savedAccounts.isNotEmpty) ...[
            const SizedBox(height: 16),
            const Text(
              'Saved Accounts',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
            ),
            const SizedBox(height: 12),
            ListView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: _savedAccounts.length,
              itemBuilder: (context, index) {
                final account = _savedAccounts[index];
                return Card(
                  margin: const EdgeInsets.only(bottom: 8),
                  child: ListTile(
                    title: Text('${account.brokerName} - ${account.accountNumber}'),
                    subtitle: Text('Server: ${account.server}'),
                    trailing: Chip(
                      label: Text(account.isDemo ? 'DEMO' : 'LIVE'),
                      backgroundColor: account.isDemo ? Colors.orange : Colors.green,
                    ),
                  ),
                );
              },
            ),
          ],
          const SizedBox(height: 20),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              border: Border.all(color: Colors.white24),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _isBinanceBroker
                      ? '📱 How to get your Binance API credentials:'
                      : _isFxcmBroker
                          ? '📱 How to connect your FXCM account:'
                          : '📱 How to get your MT5 credentials:',
                  style: const TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 14,
                  ),
                ),
                const SizedBox(height: 12),
                Text(
                  _isBinanceBroker
                      ? '1. Create a separate Binance API key for this client account\n2. Enable reading and spot or futures trading only\n3. Keep withdrawals disabled\n4. Restrict the key to the VPS public IP\n5. Copy the API key and secret and choose Spot or Futures\n6. Fund that same client Binance account before starting the bot'
                      : _isFxcmBroker
                          ? '1. Enter your FXCM Login ID and Trading Station password\n2. Leave Trading Account ID blank if you do not know it\n3. The backend will resolve the actual FXCM account row after login\n4. If needed, generate an API token from Trading Station Settings\n5. Select DEMO or LIVE to match your account'
                          : '1. Open your MetaTrader 5 terminal\n2. Login with your broker account\n3. Your account number appears at the top\n4. Use your MT5 login password\n5. Server will auto-populate',
                  style: const TextStyle(fontSize: 12, color: Colors.white70),
                ),
                const SizedBox(height: 16),
                const Text(
                  '✓ Example Credentials:',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 6),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                  decoration: BoxDecoration(
                    color: Colors.grey[800],
                    borderRadius: BorderRadius.circular(4),
                    border: Border.all(color: Colors.grey[700]!),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        _isBinanceBroker
                            ? 'API Key: paste this client\'s Binance API key'
                            : (_isFxcmBroker ? 'Login ID: D291208899' : 'Account: demo or 136372035'),
                        style: const TextStyle(fontFamily: 'monospace', fontSize: 11),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        _isBinanceBroker
                            ? 'Secret: paste this client\'s Binance API secret'
                            : (_isFxcmBroker ? 'Trading Account ID: optional, backend can auto-resolve' : 'Password: demo123'),
                        style: const TextStyle(fontFamily: 'monospace', fontSize: 11),
                      ),
                      if (_isFxcmBroker) ...[
                        const SizedBox(height: 4),
                        const Text(
                          'Password: Oaxm3',
                        style: const TextStyle(fontFamily: 'monospace', fontSize: 11),
                      ),
                      ],
                    ],
                  ),
                ),
              ],
            ),
          ),
          // Navigation footer icons
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: const BoxDecoration(
              border: Border(top: BorderSide(color: Colors.white10)),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                Tooltip(
                  message: 'Back to Previous Screen',
                  child: IconButton(
                    icon: const Icon(Icons.arrow_back, size: 24),
                    onPressed: widget.onBackPressed ?? () => Navigator.pop(context),
                    tooltip: 'Go Back',
                  ),
                ),
                Tooltip(
                  message: 'Refresh Connection Status',
                  child: IconButton(
                    icon: const Icon(Icons.refresh, size: 24),
                    onPressed: _isTestingConnection ? null : _testConnection,
                    tooltip: 'Refresh',
                  ),
                ),
                Tooltip(
                  message: 'Connection Settings',
                  child: IconButton(
                    icon: const Icon(Icons.settings, size: 24),
                    onPressed: () {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('Settings: Auto-reconnect and account preferences')),
                      );
                    },
                    tooltip: 'Settings',
                  ),
                ),
                Tooltip(
                  message: 'View Connection History',
                  child: IconButton(
                    icon: const Icon(Icons.history, size: 24),
                    onPressed: () {
                      showDialog(
                        context: context,
                        builder: (context) => AlertDialog(
                          title: const Text('Connection History'),
                          content: SingleChildScrollView(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Text('Last Connection: ${_lastConnectionTime?.toString() ?? "N/A"}'),
                                const SizedBox(height: 8),
                                Text('Status: ${_isConnected ? "Connected" : "Disconnected"}'),
                                const SizedBox(height: 8),
                                Text('Mode: ${_isLiveMode ? "LIVE 🔴" : "DEMO 🟠"}'),
                              ],
                            ),
                          ),
                          actions: [
                            TextButton(
                              onPressed: () => Navigator.pop(context),
                              child: const Text('Close'),
                            ),
                          ],
                        ),
                      );
                    },
                    tooltip: 'History',
                  ),
                ),
                Tooltip(
                  message: 'Help & Documentation',
                  child: IconButton(
                    icon: const Icon(Icons.help_outline, size: 24),
                    onPressed: () {
                      showDialog(
                        context: context,
                        builder: (context) => AlertDialog(
                          title: const Text('Broker Integration Help'),
                          content: const SingleChildScrollView(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Text('📱 Demo Mode (Orange): Training account for testing'),
                                SizedBox(height: 8),
                                Text('🔴 Live Mode (Red): Real money trading - USE WITH CAUTION'),
                                SizedBox(height: 12),
                                Text('✓ When Connected:'),
                                Text('  • Account is authenticated'),
                                Text('  • Bots can place real trades'),
                                Text('  • Balance is synchronized'),
                              ],
                            ),
                          ),
                          actions: [
                            TextButton(
                              onPressed: () => Navigator.pop(context),
                              child: const Text('Close'),
                            ),
                          ],
                        ),
                      );
                    },
                    tooltip: 'Help',
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
      ),
    );

  Widget _buildStatusInfoRow(String label, String value) => Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: GoogleFonts.poppins(
            color: Colors.white70,
            fontSize: 12,
          ),
        ),
        Text(
          value,
          style: GoogleFonts.poppins(
            color: Colors.white,
            fontSize: 12,
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );

}

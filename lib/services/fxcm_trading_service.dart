import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../utils/environment_config.dart';

/// Service for FXCM API operations from Flutter.
/// Calls backend endpoints in fxcm_service.py.
class FxcmTradingService {
  static String get _baseUrl => EnvironmentConfig.apiUrl;

  static Future<Map<String, String>> _authHeaders({bool jsonContent = false}) async {
    final prefs = await SharedPreferences.getInstance();
    final sessionToken = prefs.getString('auth_token') ?? '';
    final headers = <String, String>{
      if (sessionToken.isNotEmpty) 'X-Session-Token': sessionToken,
    };
    if (jsonContent) {
      headers['Content-Type'] = 'application/json';
    }
    return headers;
  }

  // ==================== LOGIN ====================

  static Future<Map<String, dynamic>> login({String? token}) async {
    try {
      final body = <String, dynamic>{};
      if (token != null) body['token'] = token;

      final resp = await http.post(
        Uri.parse('$_baseUrl/api/fxcm/login'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(body),
      ).timeout(const Duration(seconds: 15));

      if (resp.statusCode == 200) return jsonDecode(resp.body);
      return {'success': false, 'error': 'Server error ${resp.statusCode}'};
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }

  // ==================== ACCOUNTS ====================

  static Future<Map<String, dynamic>> getAccounts() async {
    try {
      final resp = await http.get(
        Uri.parse('$_baseUrl/api/fxcm/accounts'),
      ).timeout(const Duration(seconds: 10));

      if (resp.statusCode == 200) return jsonDecode(resp.body);
      return {'success': false, 'error': 'Server error ${resp.statusCode}'};
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }

  // ==================== BALANCE ====================

  static Future<Map<String, dynamic>> getBalance() async {
    try {
      final resp = await http.get(
        Uri.parse('$_baseUrl/api/fxcm/balance'),
      ).timeout(const Duration(seconds: 10));

      if (resp.statusCode == 200) return jsonDecode(resp.body);
      return {'success': false, 'error': 'Server error ${resp.statusCode}'};
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }

  // ==================== FUNDS ====================

  static Future<Map<String, dynamic>> getFunds() async {
    try {
      final resp = await http.get(
        Uri.parse('$_baseUrl/api/fxcm/funds'),
      ).timeout(const Duration(seconds: 10));

      if (resp.statusCode == 200) return jsonDecode(resp.body);
      return {'success': false, 'error': 'Server error ${resp.statusCode}'};
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }

  // ==================== POSITIONS ====================

  static Future<Map<String, dynamic>> getPositions() async {
    try {
      final resp = await http.get(
        Uri.parse('$_baseUrl/api/fxcm/positions'),
      ).timeout(const Duration(seconds: 10));

      if (resp.statusCode == 200) return jsonDecode(resp.body);
      return {'success': false, 'error': 'Server error ${resp.statusCode}'};
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }

  // ==================== CLOSE POSITION ====================

  static Future<Map<String, dynamic>> closePosition({
    required String dealId,
  }) async {
    try {
      final resp = await http.post(
        Uri.parse('$_baseUrl/api/fxcm/close-position'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'dealId': dealId}),
      ).timeout(const Duration(seconds: 15));

      if (resp.statusCode == 200) return jsonDecode(resp.body);
      return {'success': false, 'error': 'Server error ${resp.statusCode}'};
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }

  // ==================== CLOSE ALL POSITIONS ====================

  static Future<Map<String, dynamic>> closeAllPositions() async {
    try {
      final resp = await http.post(
        Uri.parse('$_baseUrl/api/fxcm/close-all-positions'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({}),
      ).timeout(const Duration(seconds: 30));

      if (resp.statusCode == 200) return jsonDecode(resp.body);
      return {'success': false, 'error': 'Server error ${resp.statusCode}'};
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }

  // ==================== PLACE ORDER ====================

  static Future<Map<String, dynamic>> placeOrder({
    required String instrument,
    required String direction,
    required double size,
    double? stopPrice,
    double? limitPrice,
  }) async {
    try {
      final body = <String, dynamic>{
        'instrument': instrument,
        'direction': direction,
        'size': size,
      };
      if (stopPrice != null) body['stopPrice'] = stopPrice;
      if (limitPrice != null) body['limitPrice'] = limitPrice;

      final resp = await http.post(
        Uri.parse('$_baseUrl/api/fxcm/place-order'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(body),
      ).timeout(const Duration(seconds: 15));

      if (resp.statusCode == 200) return jsonDecode(resp.body);
      return {'success': false, 'error': 'Server error ${resp.statusCode}'};
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }

  // ==================== PENDING ORDERS ====================

  static Future<Map<String, dynamic>> getPendingOrders() async {
    try {
      final resp = await http.get(
        Uri.parse('$_baseUrl/api/fxcm/pending-orders'),
      ).timeout(const Duration(seconds: 10));

      if (resp.statusCode == 200) return jsonDecode(resp.body);
      return {'success': false, 'error': 'Server error ${resp.statusCode}'};
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }

  static Future<Map<String, dynamic>> cancelOrder(String orderId) async {
    try {
      final resp = await http.delete(
        Uri.parse('$_baseUrl/api/fxcm/pending-orders/$orderId'),
      ).timeout(const Duration(seconds: 10));

      if (resp.statusCode == 200) return jsonDecode(resp.body);
      return {'success': false, 'error': 'Server error ${resp.statusCode}'};
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }

  // ==================== TRANSACTIONS ====================

  static Future<Map<String, dynamic>> getTransactions() async {
    try {
      final resp = await http.get(
        Uri.parse('$_baseUrl/api/fxcm/transactions'),
      ).timeout(const Duration(seconds: 10));

      if (resp.statusCode == 200) return jsonDecode(resp.body);
      return {'success': false, 'error': 'Server error ${resp.statusCode}'};
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }

  // ==================== INSTRUMENTS ====================

  static Future<Map<String, dynamic>> searchInstruments(String searchTerm) async {
    try {
      final encoded = Uri.encodeComponent(searchTerm);
      final resp = await http.get(
        Uri.parse('$_baseUrl/api/fxcm/instruments?searchTerm=$encoded'),
      ).timeout(const Duration(seconds: 10));

      if (resp.statusCode == 200) return jsonDecode(resp.body);
      return {'success': false, 'error': 'Server error ${resp.statusCode}'};
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }

  // ==================== PRICING ====================

  static Future<Map<String, dynamic>> getPricing(String instruments) async {
    try {
      final encoded = Uri.encodeComponent(instruments);
      final resp = await http.get(
        Uri.parse('$_baseUrl/api/fxcm/pricing?instruments=$encoded'),
      ).timeout(const Duration(seconds: 10));

      if (resp.statusCode == 200) return jsonDecode(resp.body);
      return {'success': false, 'error': 'Server error ${resp.statusCode}'};
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }

  // ==================== CANDLES ====================

  static Future<Map<String, dynamic>> getCandles(
    String instrument, {
    String period = 'H1',
    int count = 100,
  }) async {
    try {
      final resp = await http.get(
        Uri.parse('$_baseUrl/api/fxcm/candles/$instrument?period=$period&num=$count'),
      ).timeout(const Duration(seconds: 15));

      if (resp.statusCode == 200) return jsonDecode(resp.body);
      return {'success': false, 'error': 'Server error ${resp.statusCode}'};
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }

  // ==================== PROFIT CHECK & AUTO-CLOSE ====================

  static Future<Map<String, dynamic>> profitCheck({
    required double targetProfit,
    required String userId,
    bool autoClose = true,
  }) async {
    try {
      final headers = await _authHeaders(jsonContent: true);
      final resp = await http.post(
        Uri.parse('$_baseUrl/api/fxcm/profit-check'),
        headers: headers,
        body: jsonEncode({
          'target_profit': targetProfit,
          'auto_close': autoClose,
        }),
      ).timeout(const Duration(seconds: 30));

      if (resp.statusCode == 200) return jsonDecode(resp.body);
      return {'success': false, 'error': 'Server error ${resp.statusCode}'};
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }

  // ==================== WITHDRAWAL NOTIFICATIONS ====================

  static Future<Map<String, dynamic>> getWithdrawalNotifications(String userId) async {
    try {
      final headers = await _authHeaders();
      final resp = await http.get(
        Uri.parse('$_baseUrl/api/fxcm/withdrawal-notifications'),
        headers: headers,
      ).timeout(const Duration(seconds: 10));

      if (resp.statusCode == 200) return jsonDecode(resp.body);
      return {'success': false, 'error': 'Server error ${resp.statusCode}'};
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }

  static Future<Map<String, dynamic>> createWithdrawalNotification({
    required String userId,
    required double realizedProfit,
    required int positionsClosed,
    required double balanceAvailable,
  }) async {
    try {
      final headers = await _authHeaders(jsonContent: true);
      final resp = await http.post(
        Uri.parse('$_baseUrl/api/fxcm/withdrawal-notifications'),
        headers: headers,
        body: jsonEncode({
          'realized_profit': realizedProfit,
          'positions_closed': positionsClosed,
          'balance_available': balanceAvailable,
        }),
      ).timeout(const Duration(seconds: 10));

      if (resp.statusCode == 200) return jsonDecode(resp.body);
      return {'success': false, 'error': 'Server error ${resp.statusCode}'};
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }
}

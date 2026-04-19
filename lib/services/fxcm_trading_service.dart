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

  static Map<String, dynamic> _decodeResponse(http.Response resp) {
    try {
      return jsonDecode(resp.body) as Map<String, dynamic>;
    } catch (_) {
      return {
        'success': resp.statusCode >= 200 && resp.statusCode < 300,
        'error': 'Server error ${resp.statusCode}',
        'status_code': resp.statusCode,
        'raw_body': resp.body,
      };
    }
  }

  static Future<Map<String, dynamic>> _request(
    String method,
    String path, {
    Map<String, dynamic>? body,
    bool requireJsonContent = false,
  }) async {
    try {
      final headers = await _authHeaders(jsonContent: requireJsonContent || body != null);
      late http.Response resp;
      final uri = Uri.parse('$_baseUrl$path');

      switch (method.toUpperCase()) {
        case 'POST':
          resp = await http.post(
            uri,
            headers: headers,
            body: body == null ? null : jsonEncode(body),
          );
          break;
        case 'DELETE':
          resp = await http.delete(
            uri,
            headers: headers,
          );
          break;
        default:
          resp = await http.get(
            uri,
            headers: headers,
          );
      }

      return _decodeResponse(resp);
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }

  // ==================== LOGIN ====================

  static Future<Map<String, dynamic>> login({String? token}) async {
    try {
      final body = <String, dynamic>{};
      if (token != null) body['token'] = token;

      return await _request(
        'POST',
        '/api/fxcm/login',
        body: body,
        requireJsonContent: true,
      ).timeout(const Duration(seconds: 15));
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }

  // ==================== ACCOUNTS ====================

  static Future<Map<String, dynamic>> getAccounts() async {
    return _request('GET', '/api/fxcm/accounts').timeout(const Duration(seconds: 10));
  }

  // ==================== BALANCE ====================

  static Future<Map<String, dynamic>> getBalance() async {
    return _request('GET', '/api/fxcm/balance').timeout(const Duration(seconds: 10));
  }

  // ==================== FUNDS ====================

  static Future<Map<String, dynamic>> getFunds() async {
    return _request('GET', '/api/fxcm/funds').timeout(const Duration(seconds: 10));
  }

  // ==================== POSITIONS ====================

  static Future<Map<String, dynamic>> getPositions() async {
    return _request('GET', '/api/fxcm/positions').timeout(const Duration(seconds: 10));
  }

  // ==================== CLOSE POSITION ====================

  static Future<Map<String, dynamic>> closePosition({
    required String dealId,
  }) async {
    return _request(
      'POST',
      '/api/fxcm/close-position',
      body: {'dealId': dealId},
      requireJsonContent: true,
    ).timeout(const Duration(seconds: 15));
  }

  // ==================== CLOSE ALL POSITIONS ====================

  static Future<Map<String, dynamic>> closeAllPositions() async {
    return _request(
      'POST',
      '/api/fxcm/close-all-positions',
      body: {},
      requireJsonContent: true,
    ).timeout(const Duration(seconds: 30));
  }

  // ==================== PLACE ORDER ====================

  static Future<Map<String, dynamic>> placeOrder({
    required String instrument,
    required String direction,
    required double size,
    double? stopPrice,
    double? limitPrice,
  }) async {
    final body = <String, dynamic>{
      'instrument': instrument,
      'direction': direction,
      'size': size,
    };
    if (stopPrice != null) body['stopPrice'] = stopPrice;
    if (limitPrice != null) body['limitPrice'] = limitPrice;

    return _request(
      'POST',
      '/api/fxcm/place-order',
      body: body,
      requireJsonContent: true,
    ).timeout(const Duration(seconds: 15));
  }

  // ==================== PENDING ORDERS ====================

  static Future<Map<String, dynamic>> getPendingOrders() async {
    return _request('GET', '/api/fxcm/pending-orders').timeout(const Duration(seconds: 10));
  }

  static Future<Map<String, dynamic>> cancelOrder(String orderId) async {
    return _request('DELETE', '/api/fxcm/pending-orders/$orderId').timeout(const Duration(seconds: 10));
  }

  // ==================== TRANSACTIONS ====================

  static Future<Map<String, dynamic>> getTransactions() async {
    return _request('GET', '/api/fxcm/transactions').timeout(const Duration(seconds: 10));
  }

  // ==================== INSTRUMENTS ====================

  static Future<Map<String, dynamic>> searchInstruments(String searchTerm) async {
    final encoded = Uri.encodeComponent(searchTerm);
    return _request('GET', '/api/fxcm/instruments?searchTerm=$encoded').timeout(const Duration(seconds: 10));
  }

  // ==================== PRICING ====================

  static Future<Map<String, dynamic>> getPricing(String instruments) async {
    final encoded = Uri.encodeComponent(instruments);
    return _request('GET', '/api/fxcm/pricing?instruments=$encoded').timeout(const Duration(seconds: 10));
  }

  // ==================== CANDLES ====================

  static Future<Map<String, dynamic>> getCandles(
    String instrument, {
    String period = 'H1',
    int count = 100,
  }) async {
    return _request('GET', '/api/fxcm/candles/$instrument?period=$period&num=$count').timeout(const Duration(seconds: 15));
  }

  // ==================== PROFIT CHECK & AUTO-CLOSE ====================

  static Future<Map<String, dynamic>> profitCheck({
    required double targetProfit,
    required String userId,
    bool autoClose = true,
  }) async {
    return _request(
      'POST',
      '/api/fxcm/profit-check',
      body: {
        'target_profit': targetProfit,
        'auto_close': autoClose,
      },
      requireJsonContent: true,
    ).timeout(const Duration(seconds: 30));
  }

  // ==================== WITHDRAWAL NOTIFICATIONS ====================

  static Future<Map<String, dynamic>> getWithdrawalNotifications(String userId) async {
    return _request('GET', '/api/fxcm/withdrawal-notifications').timeout(const Duration(seconds: 10));
  }

  static Future<Map<String, dynamic>> createWithdrawalNotification({
    required String userId,
    required double realizedProfit,
    required int positionsClosed,
    required double balanceAvailable,
  }) async {
    return _request(
      'POST',
      '/api/fxcm/withdrawal-notifications',
      body: {
        'realized_profit': realizedProfit,
        'positions_closed': positionsClosed,
        'balance_available': balanceAvailable,
      },
      requireJsonContent: true,
    ).timeout(const Duration(seconds: 10));
  }
}

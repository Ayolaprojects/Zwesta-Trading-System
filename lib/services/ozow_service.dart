import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import '../utils/environment_config.dart';

class OzowService {
  static String get _baseUrl => EnvironmentConfig.apiUrl;

  static Future<Map<String, dynamic>> initializeWalletTopUp({
    required double amount,
    String currency = 'ZAR',
    Map<String, dynamic>? metadata,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    final sessionToken = prefs.getString('auth_token');
    if (sessionToken == null || sessionToken.isEmpty) {
      throw Exception('User not authenticated');
    }

    final response = await http.post(
      Uri.parse('$_baseUrl/api/payments/ozow/initialize'),
      headers: {
        'Content-Type': 'application/json',
        'X-Session-Token': sessionToken,
      },
      body: jsonEncode({
        'amount': amount,
        'currency': currency,
        'purpose': 'wallet_topup',
        'metadata': metadata ?? const {'source': 'wallet_screen'},
      }),
    ).timeout(const Duration(seconds: 20));

    final data = jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode != 200 || data['success'] != true) {
      throw Exception((data['error'] ?? data['message'] ?? 'Ozow initialization failed').toString());
    }
    return data;
  }

  static Future<Map<String, dynamic>> getPaymentStatus(String paymentReference) async {
    final prefs = await SharedPreferences.getInstance();
    final sessionToken = prefs.getString('auth_token');
    if (sessionToken == null || sessionToken.isEmpty) {
      throw Exception('User not authenticated');
    }

    final response = await http.get(
      Uri.parse('$_baseUrl/api/payments/ozow/status/$paymentReference'),
      headers: {
        'Content-Type': 'application/json',
        'X-Session-Token': sessionToken,
      },
    ).timeout(const Duration(seconds: 15));

    final data = jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode != 200 || data['success'] != true) {
      throw Exception((data['error'] ?? data['message'] ?? 'Unable to fetch Ozow status').toString());
    }
    return data;
  }
}

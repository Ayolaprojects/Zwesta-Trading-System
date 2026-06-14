import 'dart:convert';

import 'package:http/http.dart' as http;

import '../utils/environment_config.dart';

class ApiService {
  /// Optional callback invoked when the server returns 401 (session expired).
  /// Callers (e.g. AuthService) set this once so every service auto-logs out.
  static void Function()? onUnauthorized;

  ApiService({String? apiKey, String? sessionToken})
      : _apiKey = apiKey ?? EnvironmentConfig.apiKey,
        _sessionToken = sessionToken {
    _baseUrl = EnvironmentConfig.apiUrl;
  }

  final String _apiKey;
  String? _sessionToken;
  late String _baseUrl;

  /// Update the session token after login (called by AuthService).
  void setSessionToken(String? token) => _sessionToken = token;

  Map<String, String> _getHeaders() {
    final headers = <String, String>{
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $_apiKey',
    };
    if (_sessionToken != null && _sessionToken!.isNotEmpty) {
      headers['X-Session-Token'] = _sessionToken!;
    }
    return headers;
  }

  Future<Map<String, dynamic>> get(String endpoint) async {
    try {
      final response = await http.get(
        Uri.parse('$_baseUrl$endpoint'),
        headers: _getHeaders(),
      ).timeout(const Duration(seconds: 30));

      return _handleResponse(response);
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }

  Future<Map<String, dynamic>> post(String endpoint, Map<String, dynamic> body) async {
    try {
      final response = await http.post(
        Uri.parse('$_baseUrl$endpoint'),
        headers: _getHeaders(),
        body: jsonEncode(body),
      ).timeout(const Duration(seconds: 30));

      return _handleResponse(response);
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }

  Future<Map<String, dynamic>> put(String endpoint, Map<String, dynamic> body) async {
    try {
      final response = await http.put(
        Uri.parse('$_baseUrl$endpoint'),
        headers: _getHeaders(),
        body: jsonEncode(body),
      ).timeout(const Duration(seconds: 30));

      return _handleResponse(response);
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }

  Future<Map<String, dynamic>> delete(String endpoint) async {
    try {
      final response = await http.delete(
        Uri.parse('$_baseUrl$endpoint'),
        headers: _getHeaders(),
      ).timeout(const Duration(seconds: 30));

      return _handleResponse(response);
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }

  Map<String, dynamic> _handleResponse(http.Response response) {
    // Auto-logout on session expiry — fires callback registered by AuthService
    if (response.statusCode == 401) {
      onUnauthorized?.call();
      return {
        'success': false,
        'status_code': 401,
        'error': 'Session expired. Please login again.',
      };
    }
    try {
      final decoded = jsonDecode(response.body) as Map<String, dynamic>;
      return decoded;
    } catch (e) {
      return {
        'success': response.statusCode == 200,
        'status_code': response.statusCode,
        'error': 'Failed to decode response',
        'raw_body': response.body,
      };
    }
  }
}

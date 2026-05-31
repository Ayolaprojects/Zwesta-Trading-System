import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import '../utils/environment_config.dart';

class KillSwitchResult {
  final bool active;
  final int stoppedBots;
  final String? message;
  final String? error;

  const KillSwitchResult({
    required this.active,
    this.stoppedBots = 0,
    this.message,
    this.error,
  });

  bool get ok => error == null;
}

class KillSwitchService {
  static Future<Map<String, String>?> _authHeaders() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token');
    if (token == null || token.isEmpty) return null;
    return {
      'Content-Type': 'application/json',
      'X-Session-Token': token,
    };
  }

  /// GET /api/bots/kill-switch — returns current kill switch state.
  static Future<KillSwitchResult> getStatus() async {
    try {
      final headers = await _authHeaders();
      if (headers == null) {
        return const KillSwitchResult(active: false, error: 'Not signed in');
      }
      final resp = await http
          .get(Uri.parse('${EnvironmentConfig.apiUrl}/api/bots/kill-switch'),
              headers: headers)
          .timeout(const Duration(seconds: 8));
      if (resp.statusCode != 200) {
        return KillSwitchResult(
          active: false,
          error: 'HTTP ${resp.statusCode}',
        );
      }
      final body = jsonDecode(resp.body) as Map<String, dynamic>;
      return KillSwitchResult(
        active: body['killSwitchActive'] == true,
      );
    } catch (e) {
      return KillSwitchResult(active: false, error: e.toString());
    }
  }

  /// POST /api/bots/kill-all — activates kill switch and stops every bot.
  static Future<KillSwitchResult> activate({String reason = 'user-panic'}) async {
    try {
      final headers = await _authHeaders();
      if (headers == null) {
        return const KillSwitchResult(active: false, error: 'Not signed in');
      }
      final resp = await http
          .post(
            Uri.parse('${EnvironmentConfig.apiUrl}/api/bots/kill-all'),
            headers: headers,
            body: jsonEncode({'reason': reason}),
          )
          .timeout(const Duration(seconds: 15));
      if (resp.statusCode != 200) {
        return KillSwitchResult(
          active: false,
          error: 'HTTP ${resp.statusCode}: ${resp.body}',
        );
      }
      final body = jsonDecode(resp.body) as Map<String, dynamic>;
      return KillSwitchResult(
        active: body['killSwitchActive'] == true,
        stoppedBots: (body['stoppedBots'] as num?)?.toInt() ?? 0,
        message: body['message']?.toString(),
      );
    } catch (e) {
      return KillSwitchResult(active: false, error: e.toString());
    }
  }

  /// POST /api/bots/kill-switch/clear — clears kill switch (bots stay stopped).
  static Future<KillSwitchResult> clear() async {
    try {
      final headers = await _authHeaders();
      if (headers == null) {
        return const KillSwitchResult(active: false, error: 'Not signed in');
      }
      final resp = await http
          .post(
            Uri.parse(
                '${EnvironmentConfig.apiUrl}/api/bots/kill-switch/clear'),
            headers: headers,
          )
          .timeout(const Duration(seconds: 8));
      if (resp.statusCode != 200) {
        return KillSwitchResult(
          active: true,
          error: 'HTTP ${resp.statusCode}: ${resp.body}',
        );
      }
      final body = jsonDecode(resp.body) as Map<String, dynamic>;
      return KillSwitchResult(
        active: body['killSwitchActive'] == true,
        message: body['message']?.toString(),
      );
    } catch (e) {
      return KillSwitchResult(active: true, error: e.toString());
    }
  }
}

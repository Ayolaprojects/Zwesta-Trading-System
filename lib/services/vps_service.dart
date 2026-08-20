import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import '../models/vps_model.dart';
import '../utils/environment_config.dart';

class VpsService extends ChangeNotifier {
  VpsService() {
    _apiUrl = EnvironmentConfig.apiUrl;
  }

  String? _apiUrl;
  List<VpsConfig> _vpsConfigs = [];
  VpsStatus? _currentVpsStatus;
  bool _isLoading = false;
  bool _isTestingConnection = false;
  bool _isSaving = false;
  bool _isDeleting = false;
  String? _errorMessage;

  List<VpsConfig> get vpsConfigs => List.unmodifiable(_vpsConfigs);
  VpsStatus? get currentVpsStatus => _currentVpsStatus;
  bool get isLoading => _isLoading;
  bool get isTestingConnection => _isTestingConnection;
  bool get isSaving => _isSaving;
  bool get isDeleting => _isDeleting;
  String? get errorMessage => _errorMessage;

  void _setLoading(bool value, {String? error}) {
    _isLoading = value;
    _errorMessage = error;
    notifyListeners();
  }

  void _setTesting(bool value) {
    _isTestingConnection = value;
    notifyListeners();
  }

  void _setSaving(bool value) {
    _isSaving = value;
    notifyListeners();
  }

  void _setDeleting(bool value) {
    _isDeleting = value;
    notifyListeners();
  }

  Future<String?> _getSessionToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('auth_token');
  }

  Future<void> fetchVpsConfigs() async {
    _setLoading(true, error: null);
    try {
      final sessionToken = await _getSessionToken();
      if (sessionToken == null || sessionToken.isEmpty) {
        _setLoading(false, error: 'Session expired. Please login again.');
        return;
      }

      final response = await http.get(
        Uri.parse('$_apiUrl/api/vps/list'),
        headers: {
          'Content-Type': 'application/json',
          'X-Session-Token': sessionToken,
        },
      ).timeout(const Duration(seconds: 15));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['success'] == true) {
          final configs = (data['vps_configs'] as List? ?? [])
              .map((c) => VpsConfig.fromJson(c as Map<String, dynamic>))
              .toList();
          _vpsConfigs = configs;
          _errorMessage = null;
        } else {
          _errorMessage = data['error'] ?? 'Failed to fetch VPS configs';
        }
      } else if (response.statusCode == 401) {
        _errorMessage = 'Session expired. Please login again.';
      } else {
        _errorMessage = 'Backend returned status ${response.statusCode}';
      }
    } catch (e) {
      _errorMessage = 'Error fetching VPS configs: $e';
      debugPrint('VPS fetch error: $e');
    }
    _setLoading(false);
  }

  Future<bool> saveVpsConfig({
    required String vpsName,
    required String vpsIp,
    required int vpsPort,
    required String username,
    required String password,
    required int rdpPort,
    required int apiPort,
    required String mt5Path,
    required String notes,
    String? vpsId,
  }) async {
    _setSaving(true);
    try {
      final sessionToken = await _getSessionToken();
      if (sessionToken == null || sessionToken.isEmpty) {
        _errorMessage = 'Session expired. Please login again.';
        _setSaving(false);
        return false;
      }

      final requestBody = {
        'vps_name': vpsName,
        'vps_ip': vpsIp,
        'vps_port': vpsPort,
        'username': username,
        'password': password,
        'rdp_port': rdpPort,
        'api_port': apiPort,
        'mt5_path': mt5Path,
        'notes': notes,
      };
      if (vpsId != null && vpsId.isNotEmpty) {
        requestBody['vps_id'] = vpsId;
      }

      final response = await http.post(
        Uri.parse('$_apiUrl/api/vps/config'),
        headers: {
          'Content-Type': 'application/json',
          'X-Session-Token': sessionToken,
        },
        body: jsonEncode(requestBody),
      ).timeout(const Duration(seconds: 15));

      final data = jsonDecode(response.body);
      if (response.statusCode >= 200 && response.statusCode < 300 && data['success'] == true) {
        debugPrint('✅ VPS config saved: $vpsName');
        _errorMessage = null;
        await fetchVpsConfigs();
        return true;
      } else if (response.statusCode == 401) {
        _errorMessage = 'Session expired. Please login again.';
      } else {
        _errorMessage = data['error']?.toString() ?? 'Failed to save VPS config';
      }
    } catch (e) {
      _errorMessage = 'Error saving VPS config: $e';
      debugPrint('VPS save error: $e');
    }
    _setSaving(false);
    return false;
  }

  Future<bool> deleteVpsConfig(String vpsId) async {
    _setDeleting(true);
    try {
      final sessionToken = await _getSessionToken();
      if (sessionToken == null || sessionToken.isEmpty) {
        _errorMessage = 'Session expired. Please login again.';
        _setDeleting(false);
        return false;
      }

      final response = await http.post(
        Uri.parse('$_apiUrl/api/vps/$vpsId/delete'),
        headers: {
          'Content-Type': 'application/json',
          'X-Session-Token': sessionToken,
        },
      ).timeout(const Duration(seconds: 15));

      final data = jsonDecode(response.body);
      if (response.statusCode == 200 && data['success'] == true) {
        _vpsConfigs.removeWhere((c) => c.vpsId == vpsId);
        if (_currentVpsStatus?.vpsId == vpsId) {
          _currentVpsStatus = null;
        }
        _errorMessage = null;
        notifyListeners();
        return true;
      } else if (response.statusCode == 401) {
        _errorMessage = 'Session expired. Please login again.';
      } else {
        _errorMessage = data['error']?.toString() ?? 'Failed to delete VPS config';
      }
    } catch (e) {
      _errorMessage = 'Error deleting VPS config: $e';
      debugPrint('VPS delete error: $e');
    }
    _setDeleting(false);
    return false;
  }

  Future<VpsStatus?> fetchVpsStatus(String vpsId) async {
    _setTesting(true);
    _currentVpsStatus = null;
    try {
      final sessionToken = await _getSessionToken();
      if (sessionToken == null || sessionToken.isEmpty) {
        _errorMessage = 'Session expired. Please login again.';
        _setTesting(false);
        return null;
      }

      final response = await http.get(
        Uri.parse('$_apiUrl/api/vps/$vpsId/status'),
        headers: {
          'Content-Type': 'application/json',
          'X-Session-Token': sessionToken,
        },
      ).timeout(const Duration(seconds: 15));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['success'] == true) {
          final status = VpsStatus.fromJson(data['vps_status'] as Map<String, dynamic>);
          _currentVpsStatus = status;
          _errorMessage = null;
          return status;
        } else {
          _errorMessage = data['error'] ?? 'Failed to fetch VPS status';
        }
      } else if (response.statusCode == 401) {
        _errorMessage = 'Session expired. Please login again.';
      } else {
        _errorMessage = 'Backend returned status ${response.statusCode}';
      }
    } catch (e) {
      _errorMessage = 'Error fetching VPS status: $e';
      debugPrint('VPS status error: $e');
    }
    _setTesting(false);
    return null;
  }

  Future<bool> testVpsConnection(String vpsId) async {
    _setTesting(true);
    _currentVpsStatus = null;
    try {
      final sessionToken = await _getSessionToken();
      if (sessionToken == null || sessionToken.isEmpty) {
        _errorMessage = 'Session expired. Please login again.';
        _setTesting(false);
        return false;
      }

      final response = await http.post(
        Uri.parse('$_apiUrl/api/vps/$vpsId/test-connection'),
        headers: {
          'Content-Type': 'application/json',
          'X-Session-Token': sessionToken,
        },
      ).timeout(const Duration(seconds: 20));

      final data = jsonDecode(response.body);
      if (response.statusCode == 200 && data['success'] == true) {
        _errorMessage = null;
        return true;
      } else if (response.statusCode == 401) {
        _errorMessage = 'Session expired. Please login again.';
      } else {
        _errorMessage = data['error']?.toString() ?? 'Failed to test VPS connection';
      }
    } catch (e) {
      _errorMessage = 'Error testing VPS connection: $e';
      debugPrint('VPS connection test error: $e');
    }
    _setTesting(false);
    return false;
  }

  Future<VpsRemoteAccess?> fetchVpsRemoteAccess(String vpsId) async {
    try {
      final sessionToken = await _getSessionToken();
      if (sessionToken == null || sessionToken.isEmpty) {
        _errorMessage = 'Session expired. Please login again.';
        return null;
      }

      final response = await http.post(
        Uri.parse('$_apiUrl/api/vps/$vpsId/remote-access'),
        headers: {
          'Content-Type': 'application/json',
          'X-Session-Token': sessionToken,
        },
      ).timeout(const Duration(seconds: 15));

      final data = jsonDecode(response.body);
      if (response.statusCode == 200 && data['success'] == true) {
        return VpsRemoteAccess.fromJson(data);
      } else if (response.statusCode == 401) {
        _errorMessage = 'Session expired. Please login again.';
      } else {
        _errorMessage = data['error']?.toString() ?? 'Failed to get remote access details';
      }
    } catch (e) {
      _errorMessage = 'Error fetching remote access: $e';
      debugPrint('VPS remote access error: $e');
    }
    return null;
  }

  Future<bool> refreshAllStatuses() async {
    if (_vpsConfigs.isEmpty) return false;

    var anySuccess = false;
    for (final config in _vpsConfigs) {
      final status = await fetchVpsStatus(config.vpsId);
      if (status != null) {
        anySuccess = true;
      }
    }
    return anySuccess;
  }

  @override
  void dispose() {
    _currentVpsStatus = null;
    super.dispose();
  }
}

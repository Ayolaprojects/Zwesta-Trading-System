import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

class BinanceOfflineUserCredential {
  BinanceOfflineUserCredential({
    required this.id,
    required this.userId,
    required this.credentialId,
    required this.apiKey,
    required this.apiSecret,
    required this.market,
    required this.isLive,
    required this.brokerName,
    required this.accountNumber,
    required this.createdAt,
    required this.lastUsedAt,
    this.memo = '',
  });

  factory BinanceOfflineUserCredential.fromJson(Map<String, dynamic> json) {
    return BinanceOfflineUserCredential(
      id: (json['id'] ?? json['credential_id'] ?? json['credentialId'] ?? '').toString(),
      userId: (json['user_id'] ?? '').toString(),
      credentialId: (json['credential_id'] ?? json['credentialId'] ?? '').toString(),
      apiKey: (json['api_key'] ?? json['apiKey'] ?? '').toString(),
      apiSecret: (json['api_secret'] ?? json['apiSecret'] ?? json['password'] ?? '').toString(),
      market: (json['market'] ?? json['server'] ?? 'spot').toString(),
      isLive: json['is_live'] ?? false,
      brokerName: (json['broker_name'] ?? json['broker'] ?? 'Binance').toString(),
      accountNumber: (json['account_number'] ?? json['accountNumber'] ?? '').toString(),
      createdAt: DateTime.parse((json['created_at'] ?? DateTime.now().toIso8601String()).toString()),
      lastUsedAt: DateTime.parse((json['last_used_at'] ?? DateTime.now().toIso8601String()).toString()),
      memo: (json['memo'] ?? json['label'] ?? '').toString(),
    );
  }

  final String id;
  final String userId;
  final String credentialId;
  final String apiKey;
  final String apiSecret;
  final String market;
  final bool isLive;
  final String brokerName;
  final String accountNumber;
  final DateTime createdAt;
  final DateTime lastUsedAt;
  final String memo;

  BinanceOfflineUserCredential copyWith({
    String? credentialId,
    String? apiKey,
    String? apiSecret,
    String? market,
    bool? isLive,
    String? brokerName,
    String? accountNumber,
    String? memo,
  }) {
    return BinanceOfflineUserCredential(
      id: id,
      userId: userId,
      credentialId: credentialId ?? this.credentialId,
      apiKey: apiKey ?? this.apiKey,
      apiSecret: apiSecret ?? this.apiSecret,
      market: market ?? this.market,
      isLive: isLive ?? this.isLive,
      brokerName: brokerName ?? this.brokerName,
      accountNumber: accountNumber ?? this.accountNumber,
      createdAt: createdAt,
      lastUsedAt: lastUsedAt,
      memo: memo ?? this.memo,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'user_id': userId,
      'credential_id': credentialId,
      'api_key': apiKey,
      'api_secret': apiSecret,
      'market': market,
      'is_live': isLive,
      'broker_name': brokerName,
      'account_number': accountNumber,
      'created_at': createdAt.toIso8601String(),
      'last_used_at': lastUsedAt.toIso8601String(),
      'memo': memo,
    };
  }
}

class BinanceOfflineCredentialService extends ChangeNotifier {
  BinanceOfflineCredentialService._();
  static final BinanceOfflineCredentialService instance =
      BinanceOfflineCredentialService._();

  static const String _offlineStorageKey = 'binance_offline_credentials';
  static const String _activeOfflineKey = 'binance_active_offline_credential_id';

  List<BinanceOfflineUserCredential> _credentials = [];
  BinanceOfflineUserCredential? _activeCredential;

  List<BinanceOfflineUserCredential> get credentials =>
      List.unmodifiable(_credentials);
  BinanceOfflineUserCredential? get activeCredential => _activeCredential;

  Future<void> initializeForUser(String? userId) async {
    await _load();
    notifyListeners();
  }

  Future<void> clearUserState() async {
    _credentials = [];
    _activeCredential = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_offlineStorageKey);
    await prefs.remove(_activeOfflineKey);
    notifyListeners();
  }

  Future<void> persistCredential(BinanceOfflineUserCredential credential) async {
    final index = _credentials.indexWhere(
      (c) => c.credentialId == credential.credentialId,
    );
    final updated = _sorted(
      index >= 0
          ? _credentials
              .asMap()
              .map((i, c) => MapEntry(i, i == index ? credential : c))
              .values
              .toList()
          : [..._credentials, credential],
    );
    _credentials = updated;
    _activeCredential = _credentials.first;
    await _save();
    notifyListeners();
  }

  Future<void> removeCredential(String credentialId) async {
    _credentials.removeWhere((c) => c.credentialId == credentialId);
    if (_activeCredential != null &&
        _activeCredential!.credentialId == credentialId) {
      _activeCredential =
          _credentials.isNotEmpty ? _credentials.first : null;
    }
    await _save();
    notifyListeners();
  }

  Future<void> setActiveCredential(String credentialId) async {
    final match = _credentials.firstWhere(
      (c) => c.credentialId == credentialId,
      orElse: () => _credentials.first,
    );
    _activeCredential = match;
    await _save();
    notifyListeners();
  }

  Future<void> loadFromJson(String rawJson, {String? userId}) async {
    final decoded = jsonDecode(rawJson);
    final List<dynamic> source = decoded is List
        ? decoded
        : decoded is Map && decoded['credentials'] is List
            ? decoded['credentials'] as List<dynamic>
            : <dynamic>[];
    final userScoped = source.map((item) {
      final map = Map<String, dynamic>.from(item as Map);
      if (userId != null && userId.trim().isNotEmpty) {
        map['user_id'] = userId.trim();
      }
      return BinanceOfflineUserCredential.fromJson(map);
    }).toList();
    _credentials = _sorted(userScoped);
    _activeCredential = _credentials.isNotEmpty ? _credentials.first : null;
    await _save();
    notifyListeners();
  }

  BinanceOfflineUserCredential? credentialForMode({
    bool? isLive,
    String? market,
  }) {
    final normalizedLive = isLive?.toString().toLowerCase();
    final normalizedMarket = (market ?? '').trim().toLowerCase();
    final matches = _credentials.where((c) {
      final liveOk = normalizedLive == null ||
          c.isLive.toString().toLowerCase() == normalizedLive;
      final marketOk = normalizedMarket.isEmpty ||
          (c.market ?? '').trim().toLowerCase() == normalizedMarket;
      return liveOk && marketOk;
    }).toList();
    if (matches.isEmpty) return null;
    return matches.firstWhere(
      (c) => c == _activeCredential,
      orElse: () => matches.first,
    );
  }

  Future<void> _load() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_offlineStorageKey);
    if (raw == null || raw.trim().isEmpty) return;
    try {
      final decoded = jsonDecode(raw) as List;
      _credentials =
          _sorted(decoded.map((e) => BinanceOfflineUserCredential.fromJson(Map<String, dynamic>.from(e as Map))).toList());
      final activeId = prefs.getString(_activeOfflineKey);
      if (activeId != null && activeId.isNotEmpty) {
        _activeCredential = _credentials.firstWhere(
          (c) => c.credentialId == activeId,
          orElse: () => _credentials.isNotEmpty ? _credentials.first : null,
        );
      } else if (_credentials.isNotEmpty) {
        _activeCredential = _credentials.first;
      }
    } catch (e) {
      debugPrint('BinanceOfflineCredentialService load error: $e');
    }
  }

  Future<void> _save() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(
        _offlineStorageKey, jsonEncode(_credentials.map((c) => c.toJson()).toList()));
    if (_activeCredential != null) {
      await prefs.setString(_activeOfflineKey, _activeCredential!.credentialId);
    } else {
      await prefs.remove(_activeOfflineKey);
    }
  }

  List<BinanceOfflineUserCredential> _sorted(
      List<BinanceOfflineUserCredential> items) {
    final list = List<BinanceOfflineUserCredential>.from(items);
    list.sort((a, b) => b.lastUsedAt.compareTo(a.lastUsedAt));
    return list;
  }
}

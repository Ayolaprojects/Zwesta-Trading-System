import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../models/broker_connection_model.dart';

class BinanceUserCredential {
  BinanceUserCredential({
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

  factory BinanceUserCredential.fromJson(Map<String, dynamic> json) {
    return BinanceUserCredential(
      id: json['id'] ?? json['credential_id'] ?? '',
      userId: json['user_id'] ?? '',
      credentialId: json['credential_id'] ?? json['credentialId'] ?? '',
      apiKey: json['api_key'] ?? json['apiKey'] ?? '',
      apiSecret: json['api_secret'] ?? json['apiSecret'] ?? json['password'] ?? '',
      market: json['market'] ?? json['server'] ?? 'spot',
      isLive: json['is_live'] ?? false,
      brokerName: json['broker_name'] ?? json['broker'] ?? 'Binance',
      accountNumber: json['account_number'] ?? json['accountNumber'] ?? '',
      createdAt: DateTime.parse(json['created_at'] ?? DateTime.now().toIso8601String()),
      lastUsedAt: DateTime.parse(json['last_used_at'] ?? DateTime.now().toIso8601String()),
      memo: json['memo'] ?? json['label'] ?? '',
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

  BinanceUserCredential copyWith({
    String? credentialId,
    String? apiKey,
    String? apiSecret,
    String? market,
    bool? isLive,
    String? brokerName,
    String? accountNumber,
    String? memo,
  }) {
    return BinanceUserCredential(
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
}

class BinanceUserCredentialService extends ChangeNotifier {
  BinanceUserCredentialService._();
  static final BinanceUserCredentialService instance = BinanceUserCredentialService._();

  List<BinanceUserCredential> _credentials = [];
  BinanceUserCredential? _activeCredential;

  static const String _storageKey = 'binance_user_credentials';
  static const String _activeKey = 'binance_active_user_credential_id';

  List<BinanceUserCredential> get credentials => List.unmodifiable(_credentials);
  BinanceUserCredential? get activeCredential => _activeCredential;

  Future<void> _load() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_storageKey);
    if (raw != null && raw.trim().isNotEmpty) {
      try {
        final decoded = jsonDecode(raw) as List;
        final list = decoded.map((item) => BinanceUserCredential.fromJson(item as Map<String, dynamic>)).toList();
        _credentials = _sorted(list);
        final activeId = prefs.getString(_activeKey);
        if (activeId != null && activeId.isNotEmpty) {
          _activeCredential = _credentials.firstWhere(
            (c) => c.credentialId == activeId,
            orElse: () => _credentials.first,
          );
        } else if (_credentials.isNotEmpty) {
          _activeCredential = _credentials.first;
        }
      } catch (e) {
        debugPrint('BinanceUserCredentialService load error: $e');
      }
    }
  }

  Future<void> _persist() async {
    final prefs = await SharedPreferences.getInstance();
    final payload = _credentials.map((c) => c.toJson()).toList();
    await prefs.setString(_storageKey, jsonEncode(payload));
    if (_activeCredential != null) {
      await prefs.setString(_activeKey, _activeCredential!.credentialId);
    } else {
      await prefs.remove(_activeKey);
    }
  }

  List<BinanceUserCredential> _sorted(List<BinanceUserCredential> items) {
    final list = List<BinanceUserCredential>.from(items);
    list.sort((a, b) => b.lastUsedAt.compareTo(a.lastUsedAt));
    return list;
  }

  // Call this when app starts or when user logs in.
  Future<void> initializeForUser(String? userId) async {
    await _load();
    notifyListeners();
  }

  // Call this on logout to prevent credential bleed-through.
  Future<void> clearUserState() async {
    _credentials = [];
    _activeCredential = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_storageKey);
    await prefs.remove(_activeKey);
    notifyListeners();
  }

  Future<void> addOrUpdateCredential({
    required String userId,
    required String credentialId,
    required String apiKey,
    required String apiSecret,
    required String market,
    required bool isLive,
    String? brokerName,
    String? accountNumber,
    String? memo,
  }) async {
    final trimmedUserId = userId.trim();
    if (trimmedUserId.isEmpty) {
      throw Exception('Missing user context for Binance credential storage');
    }

    final existingIndex = _credentials.indexWhere(
      (c) => c.userId == trimmedUserId && c.credentialId == credentialId,
    );
    final now = DateTime.now();
    if (existingIndex >= 0) {
      _credentials[existingIndex] = _credentials[existingIndex].copyWith(
        apiKey: apiKey,
        apiSecret: apiSecret,
        market: market,
        isLive: isLive,
        brokerName: brokerName,
        accountNumber: accountNumber,
        memo: memo,
      ).copyWith(lastUsedAt: now);
    } else {
      _credentials.add(BinanceUserCredential(
        id: credentialId.isEmpty ? _generateId() : credentialId,
        userId: trimmedUserId,
        credentialId: credentialId.isEmpty ? _generateId() : credentialId,
        apiKey: apiKey,
        apiSecret: apiSecret,
        market: market,
        isLive: isLive,
        brokerName: brokerName ?? 'Binance',
        accountNumber: accountNumber ?? '',
        createdAt: now,
        lastUsedAt: now,
        memo: memo ?? '',
      ));
    }
    _credentials = _sorted(_credentials);
    _activeCredential = _credentials.first;
    await _persist();
    notifyListeners();
  }

  Future<void> setActiveCredential(String credentialId) async {
    final match = _credentials.firstWhere(
      (c) => c.credentialId == credentialId,
      orElse: () => _credentials.first,
    );
    _activeCredential = match;
    await _persist();
    notifyListeners();
  }

  Future<void> removeCredential(String credentialId) async {
    _credentials.removeWhere((c) => c.credentialId == credentialId);
    if (_activeCredential != null && _activeCredential!.credentialId == credentialId) {
      _activeCredential = _credentials.isNotEmpty ? _credentials.first : null;
    }
    await _persist();
    notifyListeners();
  }

  BinanceUserCredential? credentialForMode({bool? isLive, String? market}) {
    final normalizedLive = isLive?.toString().toLowerCase();
    final normalizedMarket = (market ?? '').trim().toLowerCase();
    final matches = _credentials.where((c) {
      final liveOk = normalizedLive == null || c.isLive.toString().toLowerCase() == normalizedLive;
      final marketOk = normalizedMarket.isEmpty || (c.market ?? '').trim().toLowerCase() == normalizedMarket;
      return liveOk && marketOk;
    }).toList();
    if (matches.isEmpty) return null;
    return matches.firstWhere(
      (c) => c == _activeCredential,
      orElse: () => matches.first,
    );
  }

  String _generateId() {
    return 'binance_user_${DateTime.now().millisecondsSinceEpoch}_${_credentials.length + 1}';
  }
}

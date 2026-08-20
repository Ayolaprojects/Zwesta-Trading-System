import 'package:flutter/foundation.dart';

enum SignalType { buy, sell, close }

enum SignalSource {
  technical,
  economicNews,
  priceAction,
  machineLearning,
  manual,
}

class TradingSignal {
  final String id;
  final String symbol;
  final SignalType type;
  final SignalSource source;
  final double price;
  final double? takeProfit;
  final double? stopLoss;
  final double? confidence;
  final String? strategyId;
  final String? strategyName;
  final Map<String, dynamic>? metadata;
  final DateTime timestamp;
  final double? positionSize;
  final double? riskRewardRatio;

  TradingSignal({
    String? id,
    required this.symbol,
    required this.type,
    required this.price,
    this.source = SignalSource.technical,
    this.takeProfit,
    this.stopLoss,
    this.confidence,
    this.strategyId,
    this.strategyName,
    this.metadata,
    DateTime? timestamp,
    this.positionSize,
    this.riskRewardRatio,
  })  : id = id ?? UniqueKey().toString(),
        timestamp = timestamp ?? DateTime.now();

  bool get isBuySignal => type == SignalType.buy || type == SignalType.close;
  bool get isSellSignal => type == SignalType.sell;

  Map<String, dynamic> toJson() => {
        'id': id,
        'symbol': symbol,
        'type': type.toString().split('.').last,
        'source': source.toString().split('.').last,
        'price': price,
        'takeProfit': takeProfit,
        'stopLoss': stopLoss,
        'confidence': confidence,
        'strategyId': strategyId,
        'strategyName': strategyName,
        'metadata': metadata,
        'timestamp': timestamp.toIso8601String(),
        'positionSize': positionSize,
        'riskRewardRatio': riskRewardRatio,
      };

  factory TradingSignal.fromJson(Map<String, dynamic> json) {
    String parseSignalType(dynamic value) {
      if (value is String) {
        return value.toLowerCase();
      }
      return 'buy';
    }

    final typeStr = parseSignalType(json['type']);
    final type = switch (typeStr) {
      'buy' => SignalType.buy,
      'sell' => SignalType.sell,
      'close' => SignalType.close,
      _ => SignalType.buy,
    };

    final sourceStr = (json['source'] as String?)?.toLowerCase() ?? 'technical';
    final source = switch (sourceStr) {
      'economic_news' => SignalSource.economicNews,
      'price_action' => SignalSource.priceAction,
      'machine_learning' => SignalSource.machineLearning,
      'manual' => SignalSource.manual,
      _ => SignalSource.technical,
    };

    return TradingSignal(
      id: json['id'] ?? UniqueKey().toString(),
      symbol: json['symbol'] ?? '',
      type: type,
      source: source,
      price: (json['price'] ?? 0).toDouble(),
      takeProfit: json['takeProfit']?.toDouble(),
      stopLoss: json['stopLoss']?.toDouble(),
      confidence: json['confidence']?.toDouble(),
      strategyId: json['strategyId']?.toString(),
      strategyName: json['strategyName']?.toString(),
      metadata: json['metadata'] is Map ? Map<String, dynamic>.from(json['metadata']) : null,
      timestamp: DateTime.tryParse(json['timestamp'] ?? '') ?? DateTime.now(),
      positionSize: json['positionSize']?.toDouble(),
      riskRewardRatio: json['riskRewardRatio']?.toDouble(),
    );
  }

  TradingSignal copyWith({
    String? symbol,
    SignalType? type,
    SignalSource? source,
    double? price,
    double? takeProfit,
    double? stopLoss,
    double? confidence,
    String? strategyId,
    String? strategyName,
    Map<String, dynamic>? metadata,
    DateTime? timestamp,
    double? positionSize,
    double? riskRewardRatio,
  }) {
    return TradingSignal(
      id: id,
      symbol: symbol ?? this.symbol,
      type: type ?? this.type,
      source: source ?? this.source,
      price: price ?? this.price,
      takeProfit: takeProfit ?? this.takeProfit,
      stopLoss: stopLoss ?? this.stopLoss,
      confidence: confidence ?? this.confidence,
      strategyId: strategyId ?? this.strategyId,
      strategyName: strategyName ?? this.strategyName,
      metadata: metadata ?? this.metadata,
      timestamp: timestamp ?? this.timestamp,
      positionSize: positionSize ?? this.positionSize,
      riskRewardRatio: riskRewardRatio ?? this.riskRewardRatio,
    );
  }
}

class TradeAlert {
  final String id;
  final TradingSignal signal;
  final AlertStatus status;
  final DateTime createdAt;
  final DateTime? acknowledgedAt;
  final String? message;
  final AlertPriority priority;
  final bool requiresAction;
  final Map<String, dynamic>? actionResult;

  TradeAlert({
    String? id,
    required this.signal,
    this.status = AlertStatus.pending,
    DateTime? createdAt,
    this.acknowledgedAt,
    this.message,
    this.priority = AlertPriority.normal,
    this.requiresAction = true,
    this.actionResult,
  })  : id = id ?? UniqueKey().toString(),
        createdAt = createdAt ?? DateTime.now();

  bool get isPending => status == AlertStatus.pending;
  bool get isAcknowledged => status == AlertStatus.acknowledged;
  bool get isActioned => status == AlertStatus.actioned;
  bool get isDismissed => status == AlertStatus.dismissed;

  TradeAlert copyWith({
    AlertStatus? status,
    DateTime? acknowledgedAt,
    String? message,
    AlertPriority? priority,
    bool? requiresAction,
    Map<String, dynamic>? actionResult,
  }) {
    return TradeAlert(
      id: id,
      signal: signal,
      status: status ?? this.status,
      createdAt: createdAt,
      acknowledgedAt: acknowledgedAt ?? this.acknowledgedAt,
      message: message ?? this.message,
      priority: priority ?? this.priority,
      requiresAction: requiresAction ?? this.requiresAction,
      actionResult: actionResult ?? this.actionResult,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'signal': signal.toJson(),
      'status': status.toString().split('.').last,
      'createdAt': createdAt.toIso8601String(),
      'acknowledgedAt': acknowledgedAt?.toIso8601String(),
      'message': message,
      'priority': priority.toString().split('.').last,
      'requiresAction': requiresAction,
      'actionResult': actionResult,
    };
  }

  factory TradeAlert.fromJson(Map<String, dynamic> json) {
    final statusStr = (json['status'] as String?)?.toLowerCase() ?? 'pending';
    final status = switch (statusStr) {
      'acknowledged' => AlertStatus.acknowledged,
      'actioned' => AlertStatus.actioned,
      'dismissed' => AlertStatus.dismissed,
      _ => AlertStatus.pending,
    };

    final priorityStr = (json['priority'] as String?)?.toLowerCase() ?? 'normal';
    final priority = switch (priorityStr) {
      'high' => AlertPriority.high,
      'low' => AlertPriority.low,
      _ => AlertPriority.normal,
    };

    return TradeAlert(
      id: json['id'] ?? UniqueKey().toString(),
      signal: TradingSignal.fromJson(Map<String, dynamic>.from(json['signal'] as Map)),
      status: status,
      createdAt: DateTime.tryParse(json['createdAt'] ?? '') ?? DateTime.now(),
      acknowledgedAt: json['acknowledgedAt'] != null
          ? DateTime.tryParse(json['acknowledgedAt'])
          : null,
      message: json['message']?.toString(),
      priority: priority,
      requiresAction: json['requiresAction'] ?? true,
      actionResult: json['actionResult'] is Map
          ? Map<String, dynamic>.from(json['actionResult'])
          : null,
    );
  }
}

enum AlertStatus { pending, acknowledged, actioned, dismissed }

enum AlertPriority { low, normal, high }

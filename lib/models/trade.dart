enum TradeStatus { open, closed, pending }
enum TradeType { buy, sell }

class Trade {
  final String id;
  final String symbol;
  final TradeType type;
  final double quantity;
  final double entryPrice;
  final double? currentPrice;
  final double? takeProfit;
  final double? stopLoss;
  final TradeStatus status;
  final DateTime openedAt;
  final DateTime? closedAt;
  final double? profit;
  final double? profitPercentage;
  /// Currency the profit/price is denominated in (e.g. 'ZAR', 'USDT', 'USD').
  final String currency;

  Trade({
    required this.id,
    required this.symbol,
    required this.type,
    required this.quantity,
    required this.entryPrice,
    this.currentPrice,
    this.takeProfit,
    this.stopLoss,
    required this.status,
    required this.openedAt,
    this.closedAt,
    this.profit,
    this.profitPercentage,
    this.currency = 'ZAR',
  });

  /// Infer the quote currency from a Binance symbol (e.g. BTCUSDT → USDT).
  static String _inferCurrency(String symbol, String? explicit) {
    if (explicit != null && explicit.trim().isNotEmpty) return explicit.trim().toUpperCase();
    final s = symbol.toUpperCase().replaceAll(RegExp(r'[^A-Z0-9]'), '');
    for (final q in ['FDUSD','TUSD','BUSD','USDT','USDC','USD','EUR','GBP','ZAR']) {
      if (s.endsWith(q) && s.length > q.length) return q;
    }
    return 'ZAR';
  }

  factory Trade.fromJson(Map<String, dynamic> json) {
    final symbol = json['symbol'] ?? '';
    return Trade(
      id: json['id'] ?? '',
      symbol: symbol,
      type: json['type'] == 'buy' ? TradeType.buy : TradeType.sell,
      quantity: (json['quantity'] ?? 0).toDouble(),
      entryPrice: (json['entryPrice'] ?? 0).toDouble(),
      currentPrice: json['currentPrice']?.toDouble(),
      takeProfit: json['takeProfit']?.toDouble(),
      stopLoss: json['stopLoss']?.toDouble(),
      status: _parseStatus(json['status']),
      openedAt: DateTime.parse(json['openedAt'] ?? DateTime.now().toString()),
      closedAt: json['closedAt'] != null ? DateTime.parse(json['closedAt']) : null,
      profit: json['profit']?.toDouble(),
      profitPercentage: json['profitPercentage']?.toDouble(),
      currency: _inferCurrency(symbol, json['currency']?.toString() ?? json['account_currency']?.toString()),
    );
  }

  static TradeStatus _parseStatus(String? status) {
    switch (status?.toLowerCase()) {
      case 'open':
        return TradeStatus.open;
      case 'closed':
        return TradeStatus.closed;
      case 'pending':
        return TradeStatus.pending;
      default:
        return TradeStatus.pending;
    }
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'symbol': symbol,
      'type': type == TradeType.buy ? 'buy' : 'sell',
      'quantity': quantity,
      'entryPrice': entryPrice,
      'currentPrice': currentPrice,
      'takeProfit': takeProfit,
      'stopLoss': stopLoss,
      'status': status.toString().split('.').last,
      'openedAt': openedAt.toIso8601String(),
      'closedAt': closedAt?.toIso8601String(),
      'profit': profit,
      'profitPercentage': profitPercentage,
      'currency': currency,
    };
  }

  bool get isProfit => (profit ?? 0) > 0;
}

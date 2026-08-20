import 'dart:math';

import 'package:flutter/foundation.dart';

import '../models/trading_signal.dart';

/// Result of a single indicator evaluation.
class IndicatorResult {
  final String name;
  final double value;
  final bool bullish;
  final bool bearish;
  final Map<String, dynamic> metadata;

  const IndicatorResult({
    required this.name,
    required this.value,
    this.bullish = false,
    this.bearish = false,
    this.metadata = const {},
  });
}

/// A simple bar of price data.
class PriceBar {
  final DateTime time;
  final double open;
  final double high;
  final double low;
  final double close;
  final double volume;

  const PriceBar({
    required this.time,
    required this.open,
    required this.high,
    required this.low,
    required this.close,
    this.volume = 0,
  });
}

/// Strategy engine that computes technical indicators and generates
/// [TradingSignal] objects based on configured strategies.
class StrategyEngine extends ChangeNotifier {
  final List<PriceBar> _bars = [];
  final Map<String, TradingSignal> _lastSignalsBySymbol = {};

  List<PriceBar> get bars => List.unmodifiable(_bars);
  Map<String, TradingSignal> get lastSignals =>
      Map.unmodifiable(_lastSignalsBySymbol);

  /// The symbol these bars belong to (single-symbol mode).
  String? _currentSymbol;
  String? get currentSymbol => _currentSymbol;

  void setSymbol(String symbol) {
    if (symbol != _currentSymbol) {
      _currentSymbol = symbol;
      _bars.clear();
      _lastSignalsBySymbol.clear();
    }
  }

  void addBar(PriceBar bar) {
    if (_bars.isNotEmpty && bar.time.isAfter(_bars.last.time)) {
      _bars.add(bar);
    } else if (_bars.isEmpty) {
      _bars.add(bar);
    }
    notifyListeners();
  }

  void addBars(List<PriceBar> newBars) {
    for (final bar in newBars) {
      if (_bars.isNotEmpty && bar.time.isAfter(_bars.last.time)) {
        _bars.add(bar);
      } else if (_bars.isEmpty) {
        _bars.add(bar);
      }
    }
    notifyListeners();
  }

  void clear() {
    _bars.clear();
    _lastSignalsBySymbol.clear();
    notifyListeners();
  }

  // ──────────────────────────────────────────────────────────
  // Indicator calculations
  // ──────────────────────────────────────────────────────────

  /// Simple Moving Average over [period] bars.
  double sma(int period) {
    if (_bars.length < period) return double.nan;
    final slice = _bars.sublist(_bars.length - period);
    return slice.map((b) => b.close).reduce((a, b) => a + b) / period;
  }

  /// Exponential Moving Average over [period] bars.
  double ema(int period) {
    if (_bars.length < period) return double.nan;
    final k = 2.0 / (period + 1);
    var emaVal = _bars.sublist(0, period).map((b) => b.close).reduce((a, b) => a + b) / period;
    for (var i = period; i < _bars.length; i++) {
      emaVal = _bars[i].close * k + emaVal * (1 - k);
    }
    return emaVal;
  }

  /// Relative Strength Index over [period] bars.
  double rsi(int period) {
    if (_bars.length < period + 1) return double.nan;

    var gains = 0.0;
    var losses = 0.0;
    for (var i = _bars.length - period; i < _bars.length; i++) {
      final change = _bars[i].close - _bars[i - 1].close;
      if (change > 0) {
        gains += change;
      } else {
        losses += -change;
      }
    }

    final avgGain = gains / period;
    final avgLoss = losses / period;
    if (avgLoss == 0) return 100.0;

    final rs = avgGain / avgLoss;
    return 100.0 - (100.0 / (1 + rs));
  }

  /// MACD histogram value.
  /// [fastPeriod] and [slowPeriod] define the EMA windows;
  /// [signalPeriod] is the EMA of the MACD line.
  double macd({
    int fastPeriod = 12,
    int slowPeriod = 26,
    int signalPeriod = 9,
  }) {
    if (_bars.length < slowPeriod + signalPeriod) return double.nan;

    final fastEMA = _emaSeries(fastPeriod);
    final slowEMA = _emaSeries(slowPeriod);
    final macdLineLength = min(fastEMA.length, slowEMA.length);
    if (macdLineLength == 0) return double.nan;

    final macdLine = <double>[];
    for (var i = 0; i < macdLineLength; i++) {
      macdLine.add(fastEMA[i] - slowEMA[i]);
    }

    final signalEMA = _emaOfSeries(macdLine, signalPeriod);
    if (signalEMA.isEmpty) return double.nan;

    return macdLine.last - signalEMA.last;
  }

  /// Bollinger Bands — returns (upper, middle, lower) as a list.
  List<double> bollingerBands({
    int period = 20,
    double stdDevMultiplier = 2.0,
  }) {
    if (_bars.length < period) return [double.nan, double.nan, double.nan];

    final slice = _bars.sublist(_bars.length - period);
    final avg = slice.map((b) => b.close).reduce((a, b) => a + b) / period;

    var sumSqDiff = 0.0;
    for (final bar in slice) {
      final diff = bar.close - avg;
      sumSqDiff += diff * diff;
    }
    final stdDev = sqrt(sumSqDiff / period);

    return [avg + stdDev * stdDevMultiplier, avg, avg - stdDev * stdDevMultiplier];
  }

  /// Average True Range over [period] bars.
  double atr(int period) {
    if (_bars.length < period + 1) return double.nan;

    var sum = 0.0;
    for (var i = _bars.length - period; i < _bars.length; i++) {
      final tr = _trueRange(_bars[i], _bars[i - 1]);
      sum += tr;
    }
    return sum / period;
  }

  double _trueRange(PriceBar current, PriceBar previous) {
    final diff1 = current.high - current.low;
    final diff2 = (current.high - previous.close).abs();
    final diff3 = (current.low - previous.close).abs();
    return [diff1, diff2, diff3].reduce(max);
  }

  List<double> _emaSeries(int period) {
    if (_bars.length < period) return [];

    final k = 2.0 / (period + 1);
    final series = <double>[];
    var emaVal = _bars.sublist(0, period).map((b) => b.close).reduce((a, b) => a + b) / period;
    series.add(emaVal);

    for (var i = period; i < _bars.length; i++) {
      emaVal = _bars[i].close * k + emaVal * (1 - k);
      series.add(emaVal);
    }
    return series;
  }

  List<double> _emaOfSeries(List<double> values, int period) {
    if (values.length < period) return [];

    final k = 2.0 / (period + 1);
    final series = <double>[];
    var emaVal = values.sublist(0, period).reduce((a, b) => a + b) / period;
    series.add(emaVal);

    for (var i = period; i < values.length; i++) {
      emaVal = values[i] * k + emaVal * (1 - k);
      series.add(emaVal);
    }
    return series;
  }

  // ──────────────────────────────────────────────────────────
  // Strategy evaluators
  // ──────────────────────────────────────────────────────────

  /// Trend-following strategy: generates BUY when short EMA crosses above
  /// long EMA and RSI is not overbought; SELL on the reverse.
  TradingSignal? evaluateTrendFollowing({
    int fastPeriod = 9,
    int slowPeriod = 21,
    int rsiPeriod = 14,
  }) {
    if (_currentSymbol == null) return null;
    if (_bars.length < max(fastPeriod, slowPeriod) + rsiPeriod) return null;

    final fast = ema(fastPeriod);
    final slow = ema(slowPeriod);
    final rsiVal = rsi(rsiPeriod);

    if (fast.isNaN || slow.isNaN || rsiVal.isNaN) return null;

    final prevBars = _bars.sublist(0, _bars.length - 1);
    final engine = StrategyEngine().._bars.addAll(prevBars);
    final prevFast = engine.ema(fastPeriod);
    final prevSlow = engine.ema(slowPeriod);
    if (prevFast.isNaN || prevSlow.isNaN) return null;

    final crossUp = prevFast <= prevSlow && fast > slow;
    final crossDown = prevFast >= prevSlow && fast < slow;

    if (crossUp && rsiVal < 70) {
      return _buildSignal(SignalType.buy, 'Trend Following', confidence: 0.65, metadata: {
        'fastEMA': fast, 'slowEMA': slow, 'rsi': rsiVal,
      });
    }
    if (crossDown && rsiVal > 30) {
      return _buildSignal(SignalType.sell, 'Trend Following', confidence: 0.65, metadata: {
        'fastEMA': fast, 'slowEMA': slow, 'rsi': rsiVal,
      });
    }
    return null;
  }

  /// EMA Pullback strategy: BUY on a pullback below the EMA followed by a
  /// close back above it; SELL on a bounce above EMA followed by close below.
  TradingSignal? evaluateEmaPullback({
    int emaPeriod = 20,
  }) {
    if (_currentSymbol == null) return null;
    if (_bars.length < emaPeriod + 1) return null;

    final emaVal = ema(emaPeriod);
    if (emaVal.isNaN) return null;

    final prevBar = _bars[_bars.length - 2];
    final currBar = _bars.last;

    // Pullback: prev close below EMA, current close above EMA
    if (prevBar.close < emaVal && currBar.close > emaVal) {
      return _buildSignal(SignalType.buy, 'EMA Pullback', confidence: 0.7,
          metadata: {'ema': emaVal, 'pullbackLow': prevBar.low});
    }
    // Reverse pullback: prev close above EMA, current close below EMA
    if (prevBar.close > emaVal && currBar.close < emaVal) {
      return _buildSignal(SignalType.sell, 'EMA Pullback', confidence: 0.7,
          metadata: {'ema': emaVal, 'pullbackHigh': prevBar.high});
    }
    return null;
  }

  /// Bollinger Bands mean-reversion: BUY when price touches lower band
  /// and RSI < 30; SELL when price touches upper band and RSI > 70.
  TradingSignal? evaluateBollingerMeanReversion({
    int period = 20,
    double stdDevMultiplier = 2.0,
    int rsiPeriod = 14,
  }) {
    if (_currentSymbol == null) return null;
    if (_bars.length < max(period, rsiPeriod) + 1) return null;

    final bands = bollingerBands(period: period, stdDevMultiplier: stdDevMultiplier);
    if (bands.any((v) => v.isNaN)) return null;

    final upper = bands[0];
    final lower = bands[2];
    final rsiVal = rsi(rsiPeriod);
    if (rsiVal.isNaN) return null;

    final currClose = _bars.last.close;

    if (currClose <= lower && rsiVal < 30) {
      return _buildSignal(SignalType.buy, 'Bollinger Mean Reversion',
          confidence: 0.6,
          metadata: {'upper': upper, 'middle': bands[1], 'lower': lower, 'rsi': rsiVal});
    }
    if (currClose >= upper && rsiVal > 70) {
      return _buildSignal(SignalType.sell, 'Bollinger Mean Reversion',
          confidence: 0.6,
          metadata: {'upper': upper, 'middle': bands[1], 'lower': lower, 'rsi': rsiVal});
    }
    return null;
  }

  /// MACD momentum strategy: BUY on positive histogram crossover;
  /// SELL on negative crossover.
  TradingSignal? evaluateMacdMomentum({
    int fastPeriod = 12,
    int slowPeriod = 26,
    int signalPeriod = 9,
  }) {
    if (_currentSymbol == null) return null;
    if (_bars.length < slowPeriod + signalPeriod + 1) return null;

    final macdHist = macd(
      fastPeriod: fastPeriod,
      slowPeriod: slowPeriod,
      signalPeriod: signalPeriod,
    );
    if (macdHist.isNaN) return null;

    // Previous bar MACD
    final prevBars = _bars.sublist(0, _bars.length - 1);
    final prevEngine = StrategyEngine().._bars.addAll(prevBars);
    final prevMacd = prevEngine.macd(
      fastPeriod: fastPeriod,
      slowPeriod: slowPeriod,
      signalPeriod: signalPeriod,
    );
    if (prevMacd.isNaN) return null;

    // Cross from negative → positive (bullish) or positive → negative (bearish)
    if (prevMacd <= 0 && macdHist > 0) {
      return _buildSignal(SignalType.buy, 'MACD Momentum', confidence: 0.75,
          metadata: {'macdHist': macdHist, 'prevMacdHist': prevMacd});
    }
    if (prevMacd >= 0 && macdHist < 0) {
      return _buildSignal(SignalType.sell, 'MACD Momentum', confidence: 0.75,
          metadata: {'macdHist': macdHist, 'prevMacdHist': prevMacd});
    }
    return null;
  }

  /// Run all configured strategies and return the strongest signal.
  TradingSignal? evaluateAll() {
    if (_currentSymbol == null) return null;

    final candidates = [
      if (_bars.length >= 22) evaluateTrendFollowing(),
      if (_bars.length >= 22) evaluateEmaPullback(),
      if (_bars.length >= 22) evaluateBollingerMeanReversion(),
      if (_bars.length >= 36) evaluateMacdMomentum(),
    ].whereType<TradingSignal>().toList();

    if (candidates.isEmpty) return null;

    // Pick the signal with the highest confidence, then newest.
    candidates.sort((a, b) {
      final confCmp = (b.confidence ?? 0).compareTo(a.confidence ?? 0);
      if (confCmp != 0) return confCmp;
      return b.timestamp.compareTo(a.timestamp);
    });

    final best = candidates.first;
    _lastSignalsBySymbol[_currentSymbol!] = best;
    return best;
  }

  TradingSignal _buildSignal(
    SignalType type,
    String strategyName, {
    required double confidence,
    Map<String, dynamic>? metadata,
  }) {
    final price = _bars.last.close;
    final range = _bars.length >= 2 ? (_bars.last.high - _bars.last.low).abs() : 0.0;

    double? stopLoss;
    double? takeProfit;
    double? rr;

    if (range > 0) {
      if (type == SignalType.buy) {
        stopLoss = price - range;
        takeProfit = price + range * 1.5;
      } else if (type == SignalType.sell) {
        stopLoss = price + range;
        takeProfit = price - range * 1.5;
      }
      rr = 1.5;
    }

    return TradingSignal(
      symbol: _currentSymbol!,
      type: type,
      source: SignalSource.technical,
      price: price,
      confidence: confidence,
      strategyName: strategyName,
      metadata: metadata,
      positionSize: 1.0,
      stopLoss: stopLoss,
      takeProfit: takeProfit,
      riskRewardRatio: rr,
    );
  }

  Map<String, IndicatorResult> lastIndicatorResults() {
    final results = <String, IndicatorResult>{};

    if (_bars.length >= 20) {
      final ema20 = ema(20);
      results['EMA20'] = IndicatorResult(name: 'EMA20', value: ema20);
    }

    if (_bars.length >= 14) {
      final rsi14 = rsi(14);
      results['RSI14'] = IndicatorResult(
        name: 'RSI14',
        value: rsi14,
        bullish: rsi14 < 30,
        bearish: rsi14 > 70,
      );
    }

    if (_bars.length >= 26) {
      final hist = macd();
      if (!hist.isNaN) {
        results['MACD'] = IndicatorResult(
          name: 'MACD',
          value: hist,
          bullish: hist > 0,
          bearish: hist < 0,
        );
      }
    }

    return results;
  }
}

final strategyEngine = StrategyEngine();

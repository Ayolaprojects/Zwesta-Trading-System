import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:zwesta_trading/models/user.dart';
import 'package:zwesta_trading/models/trading_signal.dart';
import 'package:zwesta_trading/models/trade.dart';
import 'package:zwesta_trading/services/auth_service.dart';
import 'package:zwesta_trading/services/risk_management_service.dart';
import 'package:zwesta_trading/services/strategy_engine.dart';

void main() {
  group('AuthService Tests', () {
    late AuthService authService;

    setUp(() async {
      // Setup shared preferences for testing
      SharedPreferences.setMockInitialValues({});
      authService = AuthService();
    });

    test('Initial state should be unauthenticated', () {
      expect(authService.isAuthenticated, false);
      expect(authService.currentUser, null);
      expect(authService.token, null);
    });

    test('Login with valid credentials should succeed', () async {
      final success = await authService.login('demo', 'demo123');
      
      expect(success, true);
      expect(authService.isAuthenticated, true);
      expect(authService.currentUser, isNotNull);
      expect(authService.currentUser?.username, 'demo');
      expect(authService.token, isNotNull);
    });

    test('Login with empty credentials should fail', () async {
      final success = await authService.login('', '');
      
      expect(success, false);
      expect(authService.isAuthenticated, false);
      expect(authService.errorMessage, isNotNull);
    });

    test('Register with valid data should succeed', () async {
      final success = await authService.register(
        'testuser',
        'test@example.com',
        'password123',
        'John',
        'Doe',
      );

      expect(success, true);
      expect(authService.isAuthenticated, true);
      expect(authService.currentUser, isNotNull);
      expect(authService.currentUser?.email, 'test@example.com');
      expect(authService.currentUser?.firstName, 'John');
      expect(authService.currentUser?.lastName, 'Doe');
    });

    test('Register with empty fields should fail', () async {
      final success = await authService.register(
        '',
        '',
        '',
        '',
        '',
      );

      expect(success, false);
      expect(authService.isAuthenticated, false);
      expect(authService.errorMessage, isNotNull);
    });

    test('Logout should clear user data', () async {
      // Login first
      await authService.login('demo', 'demo123');
      expect(authService.isAuthenticated, true);

      // Logout
      await authService.logout();
      
      expect(authService.isAuthenticated, false);
      expect(authService.currentUser, null);
      expect(authService.token, null);
    });

    test('Update profile should modify user data', () async {
      // Login first
      await authService.login('demo', 'demo123');
      
      final success = await authService.updateProfile(
        'Jane',
        'Smith',
        'jane@example.com',
      );

      expect(success, true);
      expect(authService.currentUser?.firstName, 'Jane');
      expect(authService.currentUser?.lastName, 'Smith');
      expect(authService.currentUser?.email, 'jane@example.com');
    });

    test('Change password should succeed', () async {
      // Login first
      await authService.login('demo', 'demo123');
      
      final success = await authService.changePassword(
        'demo123',
        'newpassword123',
      );

      expect(success, true);
      expect(authService.errorMessage, null);
    });

    test('Clear error message should remove error', () {
      authService.clearErrorMessage();
      expect(authService.errorMessage, null);
    });
  });

  group('User Model Tests', () {
    test('User model should be created correctly', () {
      final user = User(
        id: '1',
        username: 'testuser',
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        accountType: 'Premium',
      );

      expect(user.id, '1');
      expect(user.username, 'testuser');
      expect(user.email, 'test@example.com');
      expect(user.fullName, 'Test User');
      expect(user.accountType, 'Premium');
    });

    test('User.fromJson should create user from JSON', () {
      final json = {
        'id': '123',
        'username': 'john',
        'email': 'john@example.com',
        'firstName': 'John',
        'lastName': 'Doe',
        'accountType': 'Standard',
      };

      final user = User.fromJson(json);

      expect(user.id, '123');
      expect(user.username, 'john');
      expect(user.fullName, 'John Doe');
    });

    test('User.toJson should convert user to JSON', () {
      final user = User(
        id: '1',
        username: 'test',
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
      );

      final json = user.toJson();

      expect(json['id'], '1');
      expect(json['username'], 'test');
      expect(json['email'], 'test@example.com');
      expect(json['firstName'], 'Test');
    });
  });

  group('TradingSignal Tests', () {
    test('TradingSignal should be created with correct defaults', () {
      final signal = TradingSignal(
        symbol: 'BTCUSD',
        type: SignalType.buy,
        price: 65000.0,
      );

      expect(signal.symbol, 'BTCUSD');
      expect(signal.type, SignalType.buy);
      expect(signal.price, 65000.0);
      expect(signal.source, SignalSource.technical);
      expect(signal.confidence, isNull);
      expect(signal.isBuySignal, true);
      expect(signal.isSellSignal, false);
    });

    test('TradingSignal.toJson should serialize correctly', () {
      final signal = TradingSignal(
        symbol: 'ETHUSD',
        type: SignalType.sell,
        price: 3500.0,
        confidence: 0.8,
        strategyName: 'Trend Following',
        source: SignalSource.machineLearning,
      );

      final json = signal.toJson();

      expect(json['symbol'], 'ETHUSD');
      expect(json['type'], 'sell');
      expect(json['source'], 'machineLearning');
      expect(json['confidence'], 0.8);
      expect(json['strategyName'], 'Trend Following');
    });

    test('TradingSignal.fromJson should deserialize correctly', () {
      final json = {
        'id': 'test-1',
        'symbol': 'BTCUSD',
        'type': 'buy',
        'source': 'economic_news',
        'price': 50000.0,
        'takeProfit': 52000.0,
        'stopLoss': 49000.0,
        'confidence': 0.9,
        'strategyName': 'Scalping',
        'timestamp': '2026-01-01T12:00:00.000',
        'riskRewardRatio': 2.0,
      };

      final signal = TradingSignal.fromJson(json);

      expect(signal.id, 'test-1');
      expect(signal.symbol, 'BTCUSD');
      expect(signal.type, SignalType.buy);
      expect(signal.source, SignalSource.economicNews);
      expect(signal.price, 50000.0);
      expect(signal.takeProfit, 52000.0);
      expect(signal.stopLoss, 49000.0);
      expect(signal.confidence, 0.9);
      expect(signal.riskRewardRatio, 2.0);
    });

    test('TradingSignal copyWith should create modified copy', () {
      final signal = TradingSignal(
        symbol: 'BTCUSD',
        type: SignalType.buy,
        price: 50000.0,
      );

      final copied = signal.copyWith(price: 55000.0, confidence: 0.7);

      expect(copied.symbol, 'BTCUSD');
      expect(copied.price, 55000.0);
      expect(copied.confidence, 0.7);
      expect(copied.type, SignalType.buy);
    });
  });

  group('RiskManagementService Tests', () {
    test('RiskLimits should have correct defaults', () {
      const limits = RiskLimits();
      expect(limits.maxContractsPerSymbol, 5);
      expect(limits.maxDailyLoss, 500.0);
      expect(limits.maxOpenPositions, 10);
      expect(limits.maxExposurePerSymbol, 5000.0);
      expect(limits.minAccountEquity, 100.0);
      expect(limits.minPositionSize, 0.01);
      expect(limits.maxPositionSize, 1.0);
    });

    test('RiskCheckFlags.anyTriggered should be false when no flags set', () {
      const flags = RiskCheckFlags();
      expect(flags.anyTriggered, false);
    });

    test('RiskCheckFlags.anyTriggered should be true when any flag set', () {
      const flags = RiskCheckFlags(dailyLossLimit: true);
      expect(flags.anyTriggered, true);
    });

    test('MarketHours.isMarketOpen should return true during open hours', () {
      final market = MarketHours(
        symbolPattern: 'TEST',
        openHourUtc: 10,
        openMinuteUtc: 0,
        closeHourUtc: 14,
        closeMinuteUtc: 0,
      );

      final during = market.isMarketOpen(DateTime.utc(2026, 1, 1, 12, 0, 0, 0));
      expect(during, true);

      final before = market.isMarketOpen(DateTime.utc(2026, 1, 1, 8, 0, 0, 0));
      expect(before, false);
    });

    test('RiskManagementService.isMarketOpen should return true for unknown symbols', () {
      final service = RiskManagementService();
      expect(service.isMarketOpen('UNKNOWN'), true);
    });

    test('validateSignal should allow add-on when under max contracts per symbol', () {
      final service = RiskManagementService();
      final signal = TradingSignal(
        symbol: 'BTCUSD',
        type: SignalType.buy,
        price: 50.0,
        positionSize: 1.0,
      );

      final existingTrades = [
        Trade(
          id: 't1',
          symbol: 'BTCUSD',
          type: TradeType.buy,
          quantity: 1.0,
          entryPrice: 49000.0,
          status: TradeStatus.open,
          openedAt: DateTime.now(),
        ),
      ];

      final result = service.validateSignal(
        signal,
        activeTrades: existingTrades,
        account: null,
      );

      expect(result.approved, true);
    });

    test('validateSignal should reject when max contracts per symbol reached', () {
      final service = RiskManagementService();
      final signal = TradingSignal(
        symbol: 'BTCUSD',
        type: SignalType.buy,
        price: 50.0,
        positionSize: 1.0,
      );

      // Create 5 existing open trades (maxContractsPerSymbol default is 5)
      final existingTrades = List.generate(5, (i) => Trade(
        id: 't$i',
        symbol: 'BTCUSD',
        type: TradeType.buy,
        quantity: 1.0,
        entryPrice: 49000.0,
        status: TradeStatus.open,
        openedAt: DateTime.now(),
      ));

      final result = service.validateSignal(
        signal,
        activeTrades: existingTrades,
        account: null,
      );

      expect(result.approved, false);
      expect(result.rejectionReason, contains('Max contracts per symbol'));
    });

    test('validateSignal should reject when exposure exceeds limit', () {
      final service = RiskManagementService();
      final signal = TradingSignal(
        symbol: 'BTCUSD',
        type: SignalType.buy,
        price: 10000.0,
        positionSize: 10.0,
      );

      final result = service.validateSignal(
        signal,
        activeTrades: [],
        account: null,
      );

      expect(result.approved, false);
      expect(result.flags.exposureLimit, true);
    });

    test('validateSignal should approve valid signal', () {
      final service = RiskManagementService();
      final signal = TradingSignal(
        symbol: 'BTCUSD',
        type: SignalType.buy,
        price: 500.0,
        positionSize: 1.0,
      );

      final result = service.validateSignal(
        signal,
        activeTrades: [],
        account: null,
      );

      expect(result.approved, true);
      expect(result.flags.anyTriggered, false);
    });

    test('isSymbolBlocked should block XPDUSD and ZAR pairs', () {
      final service = RiskManagementService();
      // XPDUSD (always losing)
      expect(service.isSymbolBlocked('XPDUSD'), true);
      expect(service.isSymbolBlocked('XPDUSDm'), true);
      expect(service.isSymbolBlocked('xpdusd'), true);
      // ZAR-linked forex
      expect(service.isSymbolBlocked('GBPZAR'), true);
      expect(service.isSymbolBlocked('USDZAR'), true);
      expect(service.isSymbolBlocked('ZARJPY'), true);
      // Non-blocked symbols should pass
      expect(service.isSymbolBlocked('BTCUSD'), false);
      expect(service.isSymbolBlocked('US30'), false);
      expect(service.isSymbolBlocked('EURUSD'), false);
    });

    test('calculatePositionSize should scale with equity and win streaks', () {
      final result = RiskManagementService.calculatePositionSize(
        baseSize: 0.1,
        minSize: 0.01,
        maxSize: 1.0,
        totalTrades: 10,
        totalProfit: 2000.0,
        peakProfit: 3000.0,
        maxDrawdown: 0.0,
        winStreak: 0,
        lossStreak: 0,
        performanceMultiplier: 1.0,
        volatilityLevel: 'Medium',
        managementProfile: 'balanced',
        accountBalance: 5000.0,
      );
      // $2000 profit → equity multiplier 1 + 2000/1000 = 3.0 → capped at 1.5x
      // baseSize 0.1 * 1.5 = 0.15, within min/max
      expect(result, greaterThan(0.1));
    });

    test('calculatePositionSize should shrink on loss streak', () {
      final result = RiskManagementService.calculatePositionSize(
        baseSize: 0.1,
        minSize: 0.01,
        maxSize: 1.0,
        totalTrades: 10,
        totalProfit: -50.0,
        peakProfit: 0.0,
        maxDrawdown: 0.0,
        winStreak: 0,
        lossStreak: 3,
        performanceMultiplier: 1.0,
        volatilityLevel: 'Medium',
        managementProfile: 'balanced',
        accountBalance: 5000.0,
      );
      // Loss streak 3 → 1.0 - 0.45 = 0.55 → 0.1 * 0.55 = 0.055
      expect(result, lessThan(0.1));
    });

    test('calculateScaledPositionSize should apply profit-tier boost', () {
      final size = RiskManagementService.calculateScaledPositionSize(
        baseSize: 0.1,
        minSize: 0.01,
        maxSize: 5.0,
        totalTrades: 10,
        totalProfit: 1000.0,
        peakProfit: 1500.0,
        maxDrawdown: 0.0,
        winStreak: 0,
        lossStreak: 0,
        performanceMultiplier: 1.0,
        volatilityLevel: 'Medium',
        managementProfile: 'balanced',
        accountBalance: 5000.0,
        symbol: 'US30',
        realizedPnL: 1000.0,
        symbolPnL: 50.0,
      );
      // $1000 PnL / $5000 balance = 20% → tier multiplier 5.0x
      // Should be significantly boosted above base 0.1
      expect(size, greaterThan(0.1));
    });
  });

  group('StrategyEngine Tests', () {
    test('StrategyEngine should add bars and compute SMA', () {
      final engine = StrategyEngine()..setSymbol('TEST');

      for (var i = 1; i <= 20; i++) {
        engine.addBar(PriceBar(
          time: DateTime(2026, 1, 1, i),
          open: i.toDouble(),
          high: i.toDouble() + 1,
          low: i.toDouble() - 1,
          close: i.toDouble(),
        ));
      }

      final sma = engine.sma(20);
      expect(sma.isNaN, false);
      expect(sma, closeTo(10.5, 0.001));
    });

    test('StrategyEngine.sma should return NaN for insufficient bars', () {
      final engine = StrategyEngine()..setSymbol('TEST');
      engine.addBar(PriceBar(
        time: DateTime(2026, 1, 1),
        open: 1, high: 2, low: 0, close: 1,
      ));

      final sma = engine.sma(20);
      expect(sma.isNaN, true);
    });

    test('StrategyEngine.rsi should return valid value for sufficient bars', () {
      final engine = StrategyEngine()..setSymbol('TEST');

      var price = 100.0;
      for (var i = 0; i < 20; i++) {
        price += 1.0;
        engine.addBar(PriceBar(
          time: DateTime(2026, 1, 1, i),
          open: price - 0.5,
          high: price + 1,
          low: price - 1,
          close: price,
        ));
      }

      final rsi = engine.rsi(14);
      expect(rsi.isNaN, false);
      expect(rsi, inInclusiveRange(0, 100));
    });

    test('StrategyEngine.evaluateEmaPullback should generate buy signal on pullback recovery', () {
      final engine = StrategyEngine()..setSymbol('TEST');

      // First 20 bars: prices above EMA (uptrend)
      for (var i = 0; i < 20; i++) {
        final price = 100.0 + i;
        engine.addBar(PriceBar(
          time: DateTime(2026, 1, 1, i),
          open: price - 0.5,
          high: price + 1,
          low: price - 1,
          close: price,
        ));
      }

       // Bar 21: pullback below EMA (deep pullback to 102, well below EMA ~110)
      engine.addBar(PriceBar(
        time: DateTime(2026, 1, 1, 21),
        open: 119, high: 119, low: 100, close: 102,
      ));

      // Bar 22: close back above EMA (buy signal)
      engine.addBar(PriceBar(
        time: DateTime(2026, 1, 1, 22),
        open: 103, high: 122, low: 101, close: 120,
      ));

      final signal = engine.evaluateEmaPullback();
      expect(signal, isNotNull);
      expect(signal!.type, SignalType.buy);
      expect(signal.symbol, 'TEST');
      expect(signal.confidence, greaterThan(0));
    });

    test('StrategyEngine.evaluateAll should return a signal or null', () {
      final engine = StrategyEngine()..setSymbol('TEST');

      for (var i = 0; i < 40; i++) {
        final price = 100.0 + (i % 10);
        engine.addBar(PriceBar(
          time: DateTime(2026, 1, 1, i),
          open: price - 0.5,
          high: price + 2,
          low: price - 2,
          close: price + (i % 2 == 0 ? 1 : -1),
        ));
      }

      final signal = engine.evaluateAll();
      expect(signal, anyOf(isNull, isA<TradingSignal>()));
    });
  });
}

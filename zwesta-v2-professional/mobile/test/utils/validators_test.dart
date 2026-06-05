import 'package:flutter_test/flutter_test.dart';
import 'package:zwesta/utils/validators.dart';

void main() {
  group('Validators Tests', () {
    // ==================== USERNAME VALIDATION ====================
    group('Username Validation', () {
      test('Accepts valid username', () {
        expect(Validators.validateUsername('john_doe'), isNull);
        expect(Validators.validateUsername('user123'), isNull);
        expect(Validators.validateUsername('alice.smith'), isNull);
      });

      test('Rejects empty username', () {
        expect(Validators.validateUsername(''), isNotNull);
        expect(Validators.validateUsername(null), isNotNull);
      });

      test('Rejects username too short', () {
        expect(Validators.validateUsername('ab'), isNotNull);
      });

      test('Rejects username too long', () {
        expect(Validators.validateUsername('a' * 21), isNotNull);
      });

      test('Rejects special characters', () {
        expect(Validators.validateUsername('user@name'), isNotNull);
        expect(Validators.validateUsername('user#123'), isNotNull);
        expect(Validators.validateUsername('user$'), isNotNull);
      });

      test('Rejects username starting with special char', () {
        expect(Validators.validateUsername('-username'), isNotNull);
        expect(Validators.validateUsername('.username'), isNotNull);
        expect(Validators.validateUsername('_username'), isNotNull);
      });

      test('Rejects username ending with special char', () {
        expect(Validators.validateUsername('username-'), isNotNull);
        expect(Validators.validateUsername('username.'), isNotNull);
      });
    });

    // ==================== EMAIL VALIDATION ====================
    group('Email Validation', () {
      test('Accepts valid emails', () {
        expect(Validators.validateEmail('user@example.com'), isNull);
        expect(Validators.validateEmail('test.user@domain.co.uk'), isNull);
        expect(Validators.validateEmail('name+tag@company.org'), isNull);
      });

      test('Rejects empty email', () {
        expect(Validators.validateEmail(''), isNotNull);
        expect(Validators.validateEmail(null), isNotNull);
      });

      test('Rejects invalid email format', () {
        expect(Validators.validateEmail('notanemail'), isNotNull);
        expect(Validators.validateEmail('user@'), isNotNull);
        expect(Validators.validateEmail('@example.com'), isNotNull);
        expect(Validators.validateEmail('user@.com'), isNotNull);
      });

      test('Rejects email with spaces', () {
        expect(Validators.validateEmail('user @example.com'), isNotNull);
      });
    });

    // ==================== PASSWORD VALIDATION ====================
    group('Password Validation (NIST Compliant)', () {
      test('Accepts strong password', () {
        expect(Validators.validatePassword('StrongPass123!'), isNull);
        expect(Validators.validatePassword('MyPassword@2026'), isNull);
        expect(Validators.validatePassword('SecurePass#2026'), isNull);
      });

      test('Rejects empty password', () {
        expect(Validators.validatePassword(''), isNotNull);
        expect(Validators.validatePassword(null), isNotNull);
      });

      test('Rejects password too short', () {
        expect(Validators.validatePassword('Pass1!'), isNotNull);
      });

      test('Rejects password without uppercase', () {
        expect(Validators.validatePassword('password123!'), isNotNull);
      });

      test('Rejects password without lowercase', () {
        expect(Validators.validatePassword('PASSWORD123!'), isNotNull);
      });

      test('Rejects password without digit', () {
        expect(Validators.validatePassword('Password!'), isNotNull);
      });

      test('Rejects password without special character', () {
        expect(Validators.validatePassword('Password123'), isNotNull);
      });

      test('Accepts various special characters', () {
        expect(Validators.validatePassword('Pass123!'), isNull);
        expect(Validators.validatePassword('Pass123@'), isNull);
        expect(Validators.validatePassword('Pass123#'), isNull);
        expect(Validators.validatePassword('Pass123$'), isNull);
        expect(Validators.validatePassword('Pass123%'), isNull);
        expect(Validators.validatePassword('Pass123^'), isNull);
        expect(Validators.validatePassword('Pass123&'), isNull);
        expect(Validators.validatePassword('Pass123*'), isNull);
      });
    });

    // ==================== PASSWORD CONFIRMATION ====================
    group('Password Confirmation', () {
      test('Accepts matching passwords', () {
        expect(
            Validators.validatePasswordConfirmation('Pass123!', 'Pass123!'),
            isNull);
      });

      test('Rejects mismatched passwords', () {
        expect(
            Validators.validatePasswordConfirmation('Pass123!', 'Pass456!'),
            isNotNull);
      });

      test('Rejects empty confirmation', () {
        expect(
            Validators.validatePasswordConfirmation('Pass123!', ''),
            isNotNull);
      });
    });

    // ==================== AMOUNT VALIDATION ====================
    group('Amount Validation', () {
      test('Accepts valid amounts', () {
        expect(Validators.validateAmount('100'), isNull);
        expect(Validators.validateAmount('1000.50'), isNull);
        expect(Validators.validateAmount('50000.99'), isNull);
      });

      test('Rejects zero or negative amounts', () {
        expect(Validators.validateAmount('0'), isNotNull);
        expect(Validators.validateAmount('-100'), isNotNull);
      });

      test('Rejects non-numeric amounts', () {
        expect(Validators.validateAmount('abc'), isNotNull);
        expect(Validators.validateAmount('100abc'), isNotNull);
      });

      test('Respects minimum amount', () {
        expect(Validators.validateAmount('50', min: 100), isNotNull);
        expect(Validators.validateAmount('100', min: 100), isNull);
      });

      test('Respects maximum amount', () {
        expect(Validators.validateAmount('50000', max: 10000), isNotNull);
        expect(Validators.validateAmount('5000', max: 10000), isNull);
      });

      test('Enforces decimal places limit', () {
        expect(Validators.validateAmount('100.999'), isNotNull);
        expect(Validators.validateAmount('100.99'), isNull);
      });
    });

    // ==================== PERCENTAGE VALIDATION ====================
    group('Percentage Validation', () {
      test('Accepts valid percentages', () {
        expect(Validators.validatePercentage('0'), isNull);
        expect(Validators.validatePercentage('50'), isNull);
        expect(Validators.validatePercentage('100'), isNull);
        expect(Validators.validatePercentage('50.5'), isNull);
      });

      test('Rejects percentages out of range', () {
        expect(Validators.validatePercentage('-1'), isNotNull);
        expect(Validators.validatePercentage('101'), isNotNull);
      });

      test('Rejects non-numeric input', () {
        expect(Validators.validatePercentage('fifty'), isNotNull);
      });
    });

    // ==================== SYMBOL VALIDATION ====================
    group('Symbol Validation', () {
      test('Accepts valid trading symbols', () {
        expect(Validators.validateSymbol('EURUSD'), isNull);
        expect(Validators.validateSymbol('BTCUSDT'), isNull);
        expect(Validators.validateSymbol('AAPL'), isNull);
      });

      test('Rejects empty symbol', () {
        expect(Validators.validateSymbol(''), isNotNull);
        expect(Validators.validateSymbol(null), isNotNull);
      });

      test('Rejects symbol too short', () {
        expect(Validators.validateSymbol('AB'), isNotNull);
      });

      test('Rejects symbol too long', () {
        expect(Validators.validateSymbol('A' * 11), isNotNull);
      });

      test('Rejects non-alphanumeric symbols', () {
        expect(Validators.validateSymbol('EUR-USD'), isNotNull);
        expect(Validators.validateSymbol('BTC.USDT'), isNotNull);
      });

      test('Case insensitive', () {
        expect(Validators.validateSymbol('eurusd'), isNull);
        expect(Validators.validateSymbol('EurUsd'), isNull);
      });
    });

    // ==================== PRICE LEVEL VALIDATION ====================
    group('Price Level Validation', () {
      test('Accepts valid price levels', () {
        expect(Validators.validatePriceLevel('100', label: 'Entry'), isNull);
        expect(Validators.validatePriceLevel('1.2345', label: 'SL'), isNull);
      });

      test('Rejects empty price', () {
        expect(Validators.validatePriceLevel('', label: 'Entry'), isNotNull);
      });

      test('Rejects zero or negative price', () {
        expect(Validators.validatePriceLevel('0', label: 'Entry'), isNotNull);
        expect(Validators.validatePriceLevel('-50', label: 'Entry'), isNotNull);
      });

      test('Uses custom label in error message', () {
        final error = Validators.validatePriceLevel('', label: 'Entry Price');
        expect(error, contains('Entry Price'));
      });
    });

    // ==================== STOP LOSS VALIDATION ====================
    group('Stop Loss Validation', () {
      test('SL below entry for BUY orders', () {
        expect(
            Validators.validateStopLoss('100', '95', direction: 'buy'),
            isNull);
      });

      test('SL above entry for SELL orders', () {
        expect(
            Validators.validateStopLoss('100', '105', direction: 'sell'),
            isNull);
      });

      test('Rejects SL above entry for BUY', () {
        expect(
            Validators.validateStopLoss('100', '105', direction: 'buy'),
            isNotNull);
      });

      test('Rejects SL below entry for SELL', () {
        expect(
            Validators.validateStopLoss('100', '95', direction: 'sell'),
            isNotNull);
      });

      test('Case insensitive direction', () {
        expect(
            Validators.validateStopLoss('100', '95', direction: 'BUY'),
            isNull);
        expect(
            Validators.validateStopLoss('100', '105', direction: 'SELL'),
            isNull);
      });
    });

    // ==================== RISK/REWARD VALIDATION ====================
    group('Risk/Reward Ratio Validation', () {
      test('Accepts good risk/reward ratio', () {
        // Entry: 100, SL: 90 (risk 10), TP: 120 (reward 20) = 2:1
        expect(
            Validators.validateRiskRewardRatio('100', '90', '120', minRatio: 1.0),
            isNull);
      });

      test('Rejects poor risk/reward ratio', () {
        // Entry: 100, SL: 95 (risk 5), TP: 105 (reward 5) = 1:1 ratio
        expect(
            Validators.validateRiskRewardRatio('100', '95', '105', minRatio: 2.0),
            isNotNull);
      });

      test('Respects minimum ratio requirement', () {
        // Entry: 100, SL: 90 (risk 10), TP: 130 (reward 30) = 3:1
        expect(
            Validators.validateRiskRewardRatio('100', '90', '130', minRatio: 2.5),
            isNull);

        expect(
            Validators.validateRiskRewardRatio('100', '90', '130', minRatio: 3.5),
            isNotNull);
      });
    });

    // ==================== DATE VALIDATION ====================
    group('Date Validation', () {
      test('Accepts valid dates', () {
        expect(Validators.validateDate('2026-06-05'), isNull);
        expect(Validators.validateDate('2025-12-31'), isNull);
      });

      test('Rejects invalid date format', () {
        expect(Validators.validateDate('06/05/2026'), isNotNull);
        expect(Validators.validateDate('2026-13-01'), isNotNull);
      });

      test('Rejects empty date', () {
        expect(Validators.validateDate(''), isNotNull);
      });
    });

    // ==================== TIME VALIDATION ====================
    group('Time Validation', () {
      test('Accepts valid times', () {
        expect(Validators.validateTime('09:30'), isNull);
        expect(Validators.validateTime('23:59'), isNull);
        expect(Validators.validateTime('00:00'), isNull);
      });

      test('Rejects invalid time format', () {
        expect(Validators.validateTime('9:30'), isNotNull);
        expect(Validators.validateTime('25:00'), isNotNull);
        expect(Validators.validateTime('09:60'), isNotNull);
      });

      test('Rejects empty time', () {
        expect(Validators.validateTime(''), isNotNull);
      });
    });

    // ==================== GENERIC VALIDATORS ====================
    group('Generic Validators', () {
      test('validateRequired works', () {
        expect(Validators.validateRequired('value'), isNull);
        expect(Validators.validateRequired(''), isNotNull);
        expect(Validators.validateRequired(null), isNotNull);
      });

      test('validateMinLength works', () {
        expect(Validators.validateMinLength('hello', 3), isNull);
        expect(Validators.validateMinLength('hi', 5), isNotNull);
      });

      test('validateMaxLength works', () {
        expect(Validators.validateMaxLength('hello', 10), isNull);
        expect(Validators.validateMaxLength('hello', 3), isNotNull);
      });
    });
  });
}

import 'package:intl/intl.dart';

/// Input validators for all user inputs
/// Prevents injection attacks, data corruption, and improves UX
class Validators {
  // Username validation
  static String? validateUsername(String? value) {
    if (value == null || value.isEmpty) {
      return 'Username is required';
    }
    
    value = value.trim();
    
    if (value.length < 3) {
      return 'Username must be at least 3 characters';
    }
    
    if (value.length > 20) {
      return 'Username must be less than 20 characters';
    }
    
    // Only alphanumeric, dots, hyphens, and underscores
    if (!RegExp(r'^[a-zA-Z0-9._-]+$').hasMatch(value)) {
      return 'Username can only contain letters, numbers, dots, hyphens, and underscores';
    }
    
    // Cannot start or end with special characters
    if (!RegExp(r'^[a-zA-Z0-9]').hasMatch(value) || 
        !RegExp(r'[a-zA-Z0-9]$').hasMatch(value)) {
      return 'Username must start and end with alphanumeric characters';
    }
    
    return null;
  }
  
  // Email validation
  static String? validateEmail(String? value) {
    if (value == null || value.isEmpty) {
      return 'Email is required';
    }
    
    value = value.trim().toLowerCase();
    
    // RFC 5322 simplified pattern
    final emailRegex = RegExp(
      r'^[a-zA-Z0-9.!#$%&''*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$',
    );
    
    if (!emailRegex.hasMatch(value)) {
      return 'Please enter a valid email address';
    }
    
    return null;
  }
  
  // Password validation - NIST guidelines
  static String? validatePassword(String? value) {
    if (value == null || value.isEmpty) {
      return 'Password is required';
    }
    
    if (value.length < 8) {
      return 'Password must be at least 8 characters';
    }
    
    if (value.length > 128) {
      return 'Password must be less than 128 characters';
    }
    
    // At least one uppercase letter
    if (!RegExp(r'[A-Z]').hasMatch(value)) {
      return 'Password must contain at least one uppercase letter';
    }
    
    // At least one lowercase letter
    if (!RegExp(r'[a-z]').hasMatch(value)) {
      return 'Password must contain at least one lowercase letter';
    }
    
    // At least one digit
    if (!RegExp(r'[0-9]').hasMatch(value)) {
      return 'Password must contain at least one digit';
    }
    
    // At least one special character
    if (!RegExp(r'[!@#$%^&*()_+\-=\[\]{};:"\\|,.<>\/?]').hasMatch(value)) {
      return 'Password must contain at least one special character (!@#$%^&*)';
    }
    
    return null;
  }
  
  // Confirm password
  static String? validatePasswordConfirmation(
    String? password,
    String? confirmation,
  ) {
    if (confirmation == null || confirmation.isEmpty) {
      return 'Please confirm your password';
    }
    
    if (password != confirmation) {
      return 'Passwords do not match';
    }
    
    return null;
  }
  
  // Amount/Number validation
  static String? validateAmount(String? value, {double? min, double? max}) {
    if (value == null || value.isEmpty) {
      return 'Amount is required';
    }
    
    final amount = double.tryParse(value);
    
    if (amount == null) {
      return 'Please enter a valid number';
    }
    
    if (amount <= 0) {
      return 'Amount must be greater than 0';
    }
    
    if (min != null && amount < min) {
      return 'Minimum amount is \$$min';
    }
    
    if (max != null && amount > max) {
      return 'Maximum amount is \$$max';
    }
    
    // Check decimal places (max 2 for USD)
    if ((amount * 100).toStringAsFixed(0) != (amount * 100).toString()) {
      return 'Maximum 2 decimal places allowed';
    }
    
    return null;
  }
  
  // Percentage validation (0-100)
  static String? validatePercentage(String? value) {
    if (value == null || value.isEmpty) {
      return 'Percentage is required';
    }
    
    final percentage = double.tryParse(value);
    
    if (percentage == null) {
      return 'Please enter a valid number';
    }
    
    if (percentage < 0 || percentage > 100) {
      return 'Percentage must be between 0 and 100';
    }
    
    return null;
  }
  
  // Symbol validation (trading symbols like EURUSD, BTCUSDT)
  static String? validateSymbol(String? value) {
    if (value == null || value.isEmpty) {
      return 'Symbol is required';
    }
    
    value = value.trim().toUpperCase();
    
    // 3-10 characters, alphanumeric only
    if (!RegExp(r'^[A-Z0-9]{3,10}$').hasMatch(value)) {
      return 'Invalid symbol format (e.g., EURUSD)';
    }
    
    return null;
  }
  
  // Account number validation
  static String? validateAccountNumber(String? value) {
    if (value == null || value.isEmpty) {
      return 'Account number is required';
    }
    
    value = value.trim();
    
    // Usually 6-10 digits
    if (!RegExp(r'^[0-9]{6,10}$').hasMatch(value)) {
      return 'Invalid account number';
    }
    
    return null;
  }
  
  // Leverage validation (common: 1x, 2x, 5x, 10x, 20x, 50x, 100x, 500x)
  static String? validateLeverage(String? value) {
    if (value == null || value.isEmpty) {
      return 'Leverage is required';
    }
    
    final leverage = int.tryParse(value);
    
    if (leverage == null) {
      return 'Leverage must be a whole number';
    }
    
    if (leverage < 1 || leverage > 500) {
      return 'Leverage must be between 1 and 500';
    }
    
    // Common leverage values: 1, 2, 5, 10, 20, 50, 100, 500
    final validLeverages = [1, 2, 5, 10, 20, 50, 100, 500];
    if (!validLeverages.contains(leverage)) {
      return 'Invalid leverage value. Use: ${validLeverages.join(', ')}';
    }
    
    return null;
  }
  
  // Stop loss / Take profit validation
  static String? validatePriceLevel(String? value, {required String label}) {
    if (value == null || value.isEmpty) {
      return '$label is required';
    }
    
    final price = double.tryParse(value);
    
    if (price == null) {
      return 'Please enter a valid price';
    }
    
    if (price <= 0) {
      return '$label must be greater than 0';
    }
    
    return null;
  }
  
  // Validate stop loss vs entry price
  static String? validateStopLoss(
    String? entryPrice,
    String? stopLoss, {
    required String direction, // 'buy' or 'sell'
  }) {
    final entry = double.tryParse(entryPrice ?? '');
    final sl = double.tryParse(stopLoss ?? '');
    
    if (entry == null || sl == null) {
      return 'Invalid price values';
    }
    
    if (direction.toLowerCase() == 'buy' && sl >= entry) {
      return 'Stop loss must be below entry price for BUY orders';
    }
    
    if (direction.toLowerCase() == 'sell' && sl <= entry) {
      return 'Stop loss must be above entry price for SELL orders';
    }
    
    return null;
  }
  
  // Validate risk/reward ratio
  static String? validateRiskRewardRatio(
    String? entryPrice,
    String? stopLoss,
    String? takeProfit, {
    double minRatio = 1.0,
  }) {
    final entry = double.tryParse(entryPrice ?? '');
    final sl = double.tryParse(stopLoss ?? '');
    final tp = double.tryParse(takeProfit ?? '');
    
    if (entry == null || sl == null || tp == null) {
      return 'Invalid price values';
    }
    
    final risk = (entry - sl).abs();
    final reward = (tp - entry).abs();
    
    if (risk == 0) {
      return 'Risk cannot be zero';
    }
    
    final ratio = reward / risk;
    
    if (ratio < minRatio) {
      return 'Risk/Reward ratio must be at least $minRatio:1 (current: ${ratio.toStringAsFixed(2)}:1)';
    }
    
    return null;
  }
  
  // Date validation
  static String? validateDate(String? value) {
    if (value == null || value.isEmpty) {
      return 'Date is required';
    }
    
    try {
      DateFormat('yyyy-MM-dd').parseStrict(value);
      return null;
    } catch (e) {
      return 'Please enter a valid date (yyyy-MM-dd)';
    }
  }
  
  // Time validation (HH:mm)
  static String? validateTime(String? value) {
    if (value == null || value.isEmpty) {
      return 'Time is required';
    }
    
    if (!RegExp(r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$').hasMatch(value)) {
      return 'Please enter a valid time (HH:mm)';
    }
    
    return null;
  }
  
  // Generic required field validator
  static String? validateRequired(String? value, {String? fieldName}) {
    if (value == null || value.trim().isEmpty) {
      return '${fieldName ?? "This field"} is required';
    }
    return null;
  }
  
  // Generic min length validator
  static String? validateMinLength(String? value, int minLength) {
    if (value == null || value.length < minLength) {
      return 'Must be at least $minLength characters';
    }
    return null;
  }
  
  // Generic max length validator
  static String? validateMaxLength(String? value, int maxLength) {
    if (value == null || value.length > maxLength) {
      return 'Must be at most $maxLength characters';
    }
    return null;
  }
}

// USAGE EXAMPLES:
/*
// In your TextField or Form
TextFormField(
  validator: (value) => Validators.validateUsername(value),
  decoration: InputDecoration(labelText: 'Username'),
),

TextFormField(
  validator: (value) => Validators.validatePassword(value),
  decoration: InputDecoration(labelText: 'Password'),
  obscureText: true,
),

TextFormField(
  validator: (value) => Validators.validateAmount(value, min: 100, max: 100000),
  decoration: InputDecoration(labelText: 'Investment Amount'),
  keyboardType: TextInputType.number,
),

TextFormField(
  validator: (value) => Validators.validateSymbol(value),
  decoration: InputDecoration(labelText: 'Trading Symbol'),
),

// Custom validation with dependencies
Form(
  key: _formKey,
  child: Column(
    children: [
      TextFormField(
        controller: _entryController,
        validator: (value) => Validators.validateRequired(value, fieldName: 'Entry Price'),
      ),
      TextFormField(
        controller: _slController,
        validator: (value) => Validators.validateStopLoss(
          _entryController.text,
          value,
          direction: 'buy',
        ),
      ),
      TextFormField(
        controller: _tpController,
        validator: (value) => Validators.validateRiskRewardRatio(
          _entryController.text,
          _slController.text,
          value,
          minRatio: 2.0,
        ),
      ),
    ],
  ),
)
*/

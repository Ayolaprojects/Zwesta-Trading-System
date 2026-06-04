import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:http/http.dart' as http;

import '../services/auth_service.dart';
import '../utils/constants.dart';
import '../utils/environment_config.dart';

/// Multi-step Exness onboarding wizard.
///
/// Step 1 — Account identity: enter 9-digit MT5 account number, choose demo/live,
///           check slot availability.
/// Step 2 — Password & verify: enter password, test MT5 connection, save credential.
/// Step 3 — Bot setup: choose symbols/strategy, create a ready-to-start bot.
/// Step 4 — Done: show success summary with a "Start Bot" button.
class ExnessSetupWizardScreen extends StatefulWidget {
  const ExnessSetupWizardScreen({Key? key}) : super(key: key);

  @override
  State<ExnessSetupWizardScreen> createState() =>
      _ExnessSetupWizardScreenState();
}

class _ExnessSetupWizardScreenState extends State<ExnessSetupWizardScreen> {
  int _currentStep = 0; // 0-based internally, shown as Step 1-4

  // Step 1 state
  final _accountController = TextEditingController();
  bool _isLive = false;

  // Step 2 state
  final _passwordController = TextEditingController();
  final _labelController = TextEditingController();
  final _terminalPathController = TextEditingController();
  bool _obscurePassword = true;

  // Step 3 state
  final List<String> _availableSymbols = [
    'EURUSD',
    'GBPUSD',
    'XAUUSD',
    'USDJPY',
    'AUDUSD',
    'USDCAD',
    'NZDUSD',
    'GBPJPY',
    'EURJPY',
    'EURGBP',
  ];
  final List<String> _selectedSymbols = ['EURUSD', 'GBPUSD', 'XAUUSD'];
  String _strategy = 'Trend Following';
  double _riskPerTrade = 20;
  double _maxDailyLoss = 60;

  // Results from API calls
  Map<String, dynamic>? _step1Result;
  Map<String, dynamic>? _step2Result;

  bool _loading = false;
  String? _errorMessage;

  // Completed values
  String? _credentialId;
  String? _botId;

  @override
  void dispose() {
    _accountController.dispose();
    _passwordController.dispose();
    _labelController.dispose();
    _terminalPathController.dispose();
    super.dispose();
  }

  String get _sessionToken {
    final auth = Provider.of<AuthService>(context, listen: false);
    return auth.token ?? '';
  }

  Future<Map<String, dynamic>> _callWizard(Map<String, dynamic> body) async {
    final response = await http
        .post(
          Uri.parse('${EnvironmentConfig.apiUrl}/api/broker/exness/onboard'),
          headers: {
            'Content-Type': 'application/json',
            'X-Session-Token': _sessionToken,
          },
          body: jsonEncode(body),
        )
        .timeout(const Duration(seconds: 30));
    final decoded = jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode < 200 || response.statusCode >= 300) {
      return {
        ...decoded,
        'success': false,
        'http_status': response.statusCode,
      };
    }
    return decoded;
  }

  // ── Step 1: validate account number + check capacity ─────────────────
  Future<void> _submitStep1() async {
    final account = _accountController.text.trim();
    if (account.isEmpty ||
        account.length != 9 ||
        int.tryParse(account) == null) {
      setState(() =>
          _errorMessage = 'Enter your 9-digit Exness MT5 account number.');
      return;
    }
    setState(() {
      _loading = true;
      _errorMessage = null;
    });
    try {
      final result = await _callWizard({
        'step': '1',
        'account_number': account,
        'is_live': _isLive,
      });
      if (result['success'] == true) {
        if (result['at_capacity'] == true) {
          setState(() {
            _errorMessage = 'Exness is full (${result['slots_max']} users). '
                'Contact support to join the waitlist.';
          });
          return;
        }
        setState(() {
          _step1Result = result;
          _currentStep = 1;
        });
      } else {
        setState(() => _errorMessage = result['error'] ?? 'Step 1 failed.');
      }
    } catch (e) {
      setState(() => _errorMessage = 'Network error: $e');
    } finally {
      setState(() => _loading = false);
    }
  }

  // ── Step 2: test MT5 connection + save credential ─────────────────────
  Future<void> _submitStep2() async {
    final password = _passwordController.text.trim();
    if (password.isEmpty) {
      setState(() => _errorMessage = 'Password required.');
      return;
    }
    setState(() {
      _loading = true;
      _errorMessage = null;
    });
    try {
      final result = await _callWizard({
        'step': '2',
        'account_number': _accountController.text.trim(),
        'password': password,
        'is_live': _isLive,
        'label': _labelController.text.trim().isEmpty
            ? null
            : _labelController.text.trim(),
        'mt5_terminal_path': _terminalPathController.text.trim().isEmpty
            ? null
            : _terminalPathController.text.trim(),
      });
      if (result['success'] == true) {
        setState(() {
          _step2Result = result;
          _credentialId = result['credential_id'];
          _currentStep = 2;
        });
      } else {
        setState(() => _errorMessage = result['error'] ?? 'Step 2 failed.');
      }
    } catch (e) {
      setState(() => _errorMessage = 'Network error: $e');
    } finally {
      setState(() => _loading = false);
    }
  }

  // ── Step 3: create bot ────────────────────────────────────────────────
  Future<void> _submitStep3() async {
    if (_selectedSymbols.isEmpty) {
      setState(() => _errorMessage = 'Select at least one trading symbol.');
      return;
    }
    setState(() {
      _loading = true;
      _errorMessage = null;
    });
    try {
      final result = await _callWizard({
        'step': '3',
        'credential_id': _credentialId,
        'symbols': _selectedSymbols,
        'strategy': _strategy,
        'risk_per_trade': _riskPerTrade,
        'max_daily_loss': _maxDailyLoss,
      });
      if (result['success'] == true) {
        setState(() {
          _botId = result['bot_id'];
          _currentStep = 3;
        });
      } else {
        setState(
            () => _errorMessage = result['error'] ?? 'Bot creation failed.');
      }
    } catch (e) {
      setState(() => _errorMessage = 'Network error: $e');
    } finally {
      setState(() => _loading = false);
    }
  }

  // ── Start the bot via the standard endpoint ───────────────────────────
  Future<void> _startBot() async {
    if (_botId == null) return;
    setState(() {
      _loading = true;
      _errorMessage = null;
    });
    try {
      final response = await http
          .post(
            Uri.parse('${EnvironmentConfig.apiUrl}/api/bot/start'),
            headers: {
              'Content-Type': 'application/json',
              'X-Session-Token': _sessionToken,
            },
            body: jsonEncode({'botId': _botId}),
          )
          .timeout(const Duration(seconds: 45));
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      if (data['success'] == true || data['status'] == 'RUNNING') {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Bot started! Exness is now trading.'),
              backgroundColor: Colors.green,
            ),
          );
          Navigator.of(context).pop({'botStarted': true, 'botId': _botId});
        }
      } else {
        setState(() => _errorMessage = data['error'] ?? 'Failed to start bot.');
      }
    } catch (e) {
      setState(() => _errorMessage = 'Error starting bot: $e');
    } finally {
      setState(() => _loading = false);
    }
  }

  // ── UI ────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0E21),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0D1117),
        foregroundColor: Colors.white,
        title: const Text('Connect Exness Account'),
        centerTitle: true,
        elevation: 0,
      ),
      body: Column(
        children: [
          _buildStepIndicator(),
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: _buildCurrentStep(),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStepIndicator() {
    const labels = ['Account', 'Password', 'Bot Setup', 'Done'];
    return Container(
      color: const Color(0xFF0D1117),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(
        children: List.generate(labels.length, (i) {
          final isDone = i < _currentStep;
          final isActive = i == _currentStep;
          return Expanded(
            child: Row(
              children: [
                Expanded(
                  child: Column(
                    children: [
                      Container(
                        width: 32,
                        height: 32,
                        decoration: BoxDecoration(
                          color: isDone
                              ? Colors.green
                              : isActive
                                  ? AppColors.primaryColor
                                  : const Color(0xFF1A1F3A),
                          shape: BoxShape.circle,
                          border: Border.all(
                            color: isActive
                                ? AppColors.primaryColor
                                : Colors.transparent,
                            width: 2,
                          ),
                        ),
                        child: Center(
                          child: isDone
                              ? const Icon(Icons.check,
                                  color: Colors.white, size: 16)
                              : Text(
                                  '${i + 1}',
                                  style: TextStyle(
                                    color:
                                        isActive ? Colors.white : Colors.grey,
                                    fontWeight: FontWeight.bold,
                                    fontSize: 13,
                                  ),
                                ),
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        labels[i],
                        style: TextStyle(
                          color: isActive ? Colors.white : Colors.grey,
                          fontSize: 10,
                          fontWeight:
                              isActive ? FontWeight.bold : FontWeight.normal,
                        ),
                      ),
                    ],
                  ),
                ),
                if (i < labels.length - 1)
                  Expanded(
                    child: Container(
                      height: 2,
                      color: isDone ? Colors.green : const Color(0xFF1A1F3A),
                      margin: const EdgeInsets.only(bottom: 20),
                    ),
                  ),
              ],
            ),
          );
        }),
      ),
    );
  }

  Widget _buildCurrentStep() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (_errorMessage != null) _buildError(_errorMessage!),
        if (_currentStep == 0) _buildStep1(),
        if (_currentStep == 1) _buildStep2(),
        if (_currentStep == 2) _buildStep3(),
        if (_currentStep == 3) _buildStep4Done(),
      ],
    );
  }

  // ── Step 1 ────────────────────────────────────────────────────────────
  Widget _buildStep1() => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _sectionTitle('Your Exness MT5 Account'),
          const SizedBox(height: 8),
          _hint(
            'Open Exness → My Accounts and copy your 9-digit MT5 account number (e.g. 295677214).',
          ),
          const SizedBox(height: 20),
          _label('MT5 Account Number'),
          _field(
            controller: _accountController,
            hint: '295677214',
            keyboardType: TextInputType.number,
            maxLength: 9,
          ),
          const SizedBox(height: 16),
          _label('Account Type'),
          _modeToggle(),
          const SizedBox(height: 8),
          _hint(_isLive
              ? '⚡ Live — real money trading. Slots: limited to ${10} users.'
              : '🧪 Demo — practice trading with virtual funds.'),
          const SizedBox(height: 28),
          _primaryButton('Next', _loading ? null : _submitStep1),
          if (_loading) const SizedBox(height: 12),
          if (_loading) const LinearProgressIndicator(),
        ],
      );

  // ── Step 2 ────────────────────────────────────────────────────────────
  Widget _buildStep2() {
    final acct =
        _step1Result?['account_number'] ?? _accountController.text.trim();
    final mode = _isLive ? 'Live' : 'Demo';
    final server = _step1Result?['server'] ?? 'Exness-MT5';
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _sectionTitle('Verify Your Password'),
        const SizedBox(height: 8),
        _infoCard([
          _infoRow('Account', acct),
          _infoRow('Mode', mode),
          _infoRow('Server', server),
        ]),
        const SizedBox(height: 20),
        _label('MT5 Password'),
        _passwordField(),
        const SizedBox(height: 16),
        _label('Dedicated MT5 Terminal Path (optional)'),
        _field(
          controller: _terminalPathController,
          hint: 'C:\\Program Files\\MetaTrader 5 EXNESS\\terminal64.exe',
        ),
        const SizedBox(height: 8),
        _hint(
            'Leave blank to use the shared Exness default terminal. Fill this in when this user must run on a separate MT5 installation.'),
        const SizedBox(height: 16),
        _label('Label (optional)'),
        _field(
          controller: _labelController,
          hint: 'e.g. My Exness Live',
        ),
        const SizedBox(height: 8),
        _hint(
            'The system will test your credentials against Exness MT5. This takes ~15 seconds.'),
        const SizedBox(height: 28),
        Row(children: [
          Expanded(
              child: _outlineButton(
                  'Back',
                  _loading
                      ? null
                      : () => setState(() {
                            _currentStep = 0;
                            _errorMessage = null;
                          }))),
          const SizedBox(width: 12),
          Expanded(
              child: _primaryButton('Connect', _loading ? null : _submitStep2)),
        ]),
        if (_loading) ...[
          const SizedBox(height: 12),
          const LinearProgressIndicator()
        ],
      ],
    );
  }

  // ── Step 3 ────────────────────────────────────────────────────────────
  Widget _buildStep3() {
    final balance = (_step2Result?['balance'] as num?)?.toDouble() ?? 0.0;
    final currency = _step2Result?['currency'] ?? 'USD';
    final verified = _step2Result?['verified'] == true;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _sectionTitle('Configure Your Bot'),
        const SizedBox(height: 8),
        _infoCard([
          _infoRow('Account', _step2Result?['account_number'] ?? ''),
          _infoRow('Mode', _isLive ? 'Live' : 'Demo'),
          if (verified)
            _infoRow('Balance', '${balance.toStringAsFixed(2)} $currency'),
          if (!verified) _infoRow('Status', 'Saved (verification deferred)'),
        ]),
        const SizedBox(height: 20),
        _label('Trading Symbols'),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: _availableSymbols.map((sym) {
            final selected = _selectedSymbols.contains(sym);
            return FilterChip(
              label: Text(sym,
                  style: TextStyle(
                      fontSize: 12,
                      color: selected ? Colors.white : Colors.grey)),
              selected: selected,
              onSelected: (val) => setState(() {
                if (val) {
                  _selectedSymbols.add(sym);
                } else {
                  _selectedSymbols.remove(sym);
                }
              }),
              selectedColor: AppColors.primaryColor,
              backgroundColor: const Color(0xFF1A1F3A),
              checkmarkColor: Colors.white,
              side: BorderSide(
                color: selected ? AppColors.primaryColor : Colors.grey.shade700,
              ),
            );
          }).toList(),
        ),
        const SizedBox(height: 20),
        _label('Strategy'),
        _dropdown(
          value: _strategy,
          items: [
            'Trend Following',
            'EMA Pullback ML',
            'Scalping',
            'Swing Trading',
            'Conservative'
          ],
          onChanged: (v) => setState(() => _strategy = v!),
        ),
        const SizedBox(height: 20),
        _label('Risk Per Trade: ${_riskPerTrade.toStringAsFixed(0)}%'),
        Slider(
          value: _riskPerTrade,
          min: 5,
          max: 50,
          divisions: 9,
          activeColor: AppColors.primaryColor,
          inactiveColor: const Color(0xFF1A1F3A),
          label: '${_riskPerTrade.toStringAsFixed(0)}%',
          onChanged: (v) => setState(() => _riskPerTrade = v),
        ),
        _label('Max Daily Loss: ${_maxDailyLoss.toStringAsFixed(0)}%'),
        Slider(
          value: _maxDailyLoss,
          min: 20,
          max: 90,
          divisions: 7,
          activeColor: Colors.orange,
          inactiveColor: const Color(0xFF1A1F3A),
          label: '${_maxDailyLoss.toStringAsFixed(0)}%',
          onChanged: (v) => setState(() => _maxDailyLoss = v),
        ),
        const SizedBox(height: 28),
        Row(children: [
          Expanded(
              child: _outlineButton(
                  'Back',
                  _loading
                      ? null
                      : () => setState(() {
                            _currentStep = 1;
                            _errorMessage = null;
                          }))),
          const SizedBox(width: 12),
          Expanded(
              child:
                  _primaryButton('Create Bot', _loading ? null : _submitStep3)),
        ]),
        if (_loading) ...[
          const SizedBox(height: 12),
          const LinearProgressIndicator()
        ],
      ],
    );
  }

  // ── Step 4: Done ─────────────────────────────────────────────────────
  Widget _buildStep4Done() => Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          const SizedBox(height: 24),
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: Colors.green.withOpacity(0.15),
              shape: BoxShape.circle,
              border: Border.all(color: Colors.green, width: 2),
            ),
            child: const Icon(Icons.check_circle_outline,
                color: Colors.green, size: 56),
          ),
          const SizedBox(height: 20),
          Text(
            'Exness Account Connected!',
            style: const TextStyle(
                color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          Text(
            'Your ${_isLive ? "live" : "demo"} account ${_accountController.text.trim()} is set up and ready.',
            style: TextStyle(color: Colors.grey[400], fontSize: 14),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 24),
          _infoCard([
            _infoRow('Bot ID', _botId ?? '—'),
            _infoRow('Symbols', _selectedSymbols.join(', ')),
            _infoRow('Strategy', _strategy),
            if ((_step2Result?['terminal_path'] ?? '').toString().isNotEmpty)
              _infoRow('MT5 Path',
                  (_step2Result?['terminal_path'] ?? '').toString()),
            _infoRow('Risk/trade', '${_riskPerTrade.toStringAsFixed(0)}%'),
            _infoRow('Max daily loss', '${_maxDailyLoss.toStringAsFixed(0)}%'),
          ]),
          const SizedBox(height: 28),
          _primaryButton('Start Trading Now', _loading ? null : _startBot),
          const SizedBox(height: 12),
          _outlineButton(
              'Do It Later',
              () => Navigator.of(context).pop(
                  {'botStarted': false, 'botId': _botId, 'bot_id': _botId})),
          if (_loading) ...[
            const SizedBox(height: 12),
            const LinearProgressIndicator()
          ],
          const SizedBox(height: 20),
        ],
      );

  // ── Shared widgets ────────────────────────────────────────────────────

  Widget _buildError(String msg) => Container(
        margin: const EdgeInsets.only(bottom: 16),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Colors.red.withOpacity(0.1),
          border: Border.all(color: Colors.red.shade400),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          children: [
            const Icon(Icons.error_outline, color: Colors.red, size: 18),
            const SizedBox(width: 8),
            Expanded(
                child: Text(msg,
                    style: const TextStyle(color: Colors.red, fontSize: 13))),
          ],
        ),
      );

  Widget _sectionTitle(String t) => Text(
        t,
        style: const TextStyle(
            color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
      );

  Widget _hint(String t) =>
      Text(t, style: TextStyle(color: Colors.grey[500], fontSize: 13));

  Widget _label(String t) => Padding(
        padding: const EdgeInsets.only(bottom: 6),
        child: Text(t,
            style: const TextStyle(
                color: Colors.white70,
                fontSize: 13,
                fontWeight: FontWeight.w500)),
      );

  Widget _field({
    required TextEditingController controller,
    String? hint,
    TextInputType? keyboardType,
    int? maxLength,
  }) =>
      TextField(
        controller: controller,
        keyboardType: keyboardType,
        maxLength: maxLength,
        style: const TextStyle(color: Colors.white),
        decoration: InputDecoration(
          hintText: hint,
          hintStyle: const TextStyle(color: Colors.grey),
          counterText: '',
          filled: true,
          fillColor: const Color(0xFF1A1F3A),
          border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
              borderSide: BorderSide.none),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(8),
            borderSide: const BorderSide(color: Color(0xFF1E88E5)),
          ),
        ),
      );

  Widget _passwordField() => TextField(
        controller: _passwordController,
        obscureText: _obscurePassword,
        style: const TextStyle(color: Colors.white),
        decoration: InputDecoration(
          hintText: 'MT5 password',
          hintStyle: const TextStyle(color: Colors.grey),
          filled: true,
          fillColor: const Color(0xFF1A1F3A),
          border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
              borderSide: BorderSide.none),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(8),
            borderSide: const BorderSide(color: Color(0xFF1E88E5)),
          ),
          suffixIcon: IconButton(
            icon: Icon(
                _obscurePassword ? Icons.visibility_off : Icons.visibility,
                color: Colors.grey),
            onPressed: () =>
                setState(() => _obscurePassword = !_obscurePassword),
          ),
        ),
      );

  Widget _modeToggle() => Row(
        children: [
          Expanded(
            child: GestureDetector(
              onTap: () => setState(() => _isLive = false),
              child: Container(
                padding: const EdgeInsets.symmetric(vertical: 12),
                decoration: BoxDecoration(
                  color: !_isLive
                      ? AppColors.primaryColor
                      : const Color(0xFF1A1F3A),
                  borderRadius:
                      const BorderRadius.horizontal(left: Radius.circular(8)),
                  border: Border.all(
                      color: !_isLive
                          ? AppColors.primaryColor
                          : Colors.grey.shade700),
                ),
                child: Text('Demo',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                        color: !_isLive ? Colors.white : Colors.grey,
                        fontWeight: FontWeight.bold)),
              ),
            ),
          ),
          Expanded(
            child: GestureDetector(
              onTap: () => setState(() => _isLive = true),
              child: Container(
                padding: const EdgeInsets.symmetric(vertical: 12),
                decoration: BoxDecoration(
                  color:
                      _isLive ? Colors.green.shade700 : const Color(0xFF1A1F3A),
                  borderRadius:
                      const BorderRadius.horizontal(right: Radius.circular(8)),
                  border: Border.all(
                      color: _isLive ? Colors.green : Colors.grey.shade700),
                ),
                child: Text('Live',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                        color: _isLive ? Colors.white : Colors.grey,
                        fontWeight: FontWeight.bold)),
              ),
            ),
          ),
        ],
      );

  Widget _dropdown({
    required String value,
    required List<String> items,
    required void Function(String?) onChanged,
  }) =>
      DropdownButtonFormField<String>(
        value: value,
        dropdownColor: const Color(0xFF1A1F3A),
        style: const TextStyle(color: Colors.white),
        decoration: InputDecoration(
          filled: true,
          fillColor: const Color(0xFF1A1F3A),
          border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
              borderSide: BorderSide.none),
        ),
        items: items
            .map((s) => DropdownMenuItem(
                value: s,
                child: Text(s, style: const TextStyle(color: Colors.white))))
            .toList(),
        onChanged: onChanged,
      );

  Widget _infoCard(List<Widget> rows) => Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: const Color(0xFF1A1F3A),
          borderRadius: BorderRadius.circular(10),
        ),
        child: Column(children: rows),
      );

  Widget _infoRow(String label, String value) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 4),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label,
                style: const TextStyle(color: Colors.grey, fontSize: 13)),
            Text(value,
                style: const TextStyle(
                    color: Colors.white,
                    fontSize: 13,
                    fontWeight: FontWeight.w600)),
          ],
        ),
      );

  Widget _primaryButton(String label, VoidCallback? onPressed) => SizedBox(
        width: double.infinity,
        height: 48,
        child: ElevatedButton(
          onPressed: onPressed,
          style: ElevatedButton.styleFrom(
            backgroundColor: AppColors.primaryColor,
            disabledBackgroundColor: Colors.grey.shade800,
            shape:
                RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          ),
          child: Text(label,
              style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 15)),
        ),
      );

  Widget _outlineButton(String label, VoidCallback? onPressed) => SizedBox(
        width: double.infinity,
        height: 48,
        child: OutlinedButton(
          onPressed: onPressed,
          style: OutlinedButton.styleFrom(
            side: BorderSide(color: Colors.grey.shade600),
            shape:
                RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          ),
          child: Text(label,
              style: TextStyle(
                  color: Colors.grey.shade400,
                  fontWeight: FontWeight.bold,
                  fontSize: 15)),
        ),
      );
}

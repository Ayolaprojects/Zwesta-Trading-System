import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'dashboard_screen.dart';

/// Onboarding screen shown to first-time users
/// Introduces Zwesta Trading System, Mr. Zwelihle Mathe's vision,
/// and the platform's capabilities
class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({Key? key}) : super(key: key);

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final PageController _pageController = PageController();
  int _currentPage = 0;

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  Future<void> _completeOnboarding() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('onboarding_complete', true);
    if (mounted) {
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => const DashboardScreen()),
      );
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        body: Container(
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                Color(0xFF0A0E21),
                Color(0xFF1A1F3A),
                Color(0xFF0A0E21),
              ],
            ),
          ),
          child: SafeArea(
            child: Column(
              children: [
                // Skip button
                Align(
                  alignment: Alignment.topRight,
                  child: TextButton(
                    onPressed: _completeOnboarding,
                    child: Text(
                      'Skip',
                      style: GoogleFonts.poppins(
                        color: Colors.white70,
                        fontSize: 14,
                      ),
                    ),
                  ),
                ),

                // PageView
                Expanded(
                  child: PageView(
                    controller: _pageController,
                    onPageChanged: (index) {
                      setState(() => _currentPage = index);
                    },
                    children: [
                      _buildPage1(),
                      _buildPage2(),
                      _buildPage3(),
                      _buildPage4(),
                      _buildPage5(),
                    ],
                  ),
                ),

                // Page Indicators
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: List.generate(
                    5,
                    (index) => Container(
                      margin: const EdgeInsets.symmetric(horizontal: 4),
                      width: _currentPage == index ? 24 : 8,
                      height: 8,
                      decoration: BoxDecoration(
                        color: _currentPage == index
                            ? const Color(0xFF00E5FF)
                            : Colors.white30,
                        borderRadius: BorderRadius.circular(4),
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 24),

                // Next/Get Started button
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 32),
                  child: SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: () {
                        if (_currentPage < 4) {
                          _pageController.nextPage(
                            duration: const Duration(milliseconds: 300),
                            curve: Curves.easeInOut,
                          );
                        } else {
                          _completeOnboarding();
                        }
                      },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF00E5FF),
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                      child: Text(
                        _currentPage < 4 ? 'Next' : 'Get Started',
                        style: GoogleFonts.poppins(
                          color: const Color(0xFF0A0E21),
                          fontSize: 16,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 32),
              ],
            ),
          ),
        ),
      );

  Widget _buildPage1() => Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Logo/Icon
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: const Color(0xFF00E5FF).withOpacity(0.15),
                shape: BoxShape.circle,
                border: Border.all(
                  color: const Color(0xFF00E5FF),
                  width: 2,
                ),
              ),
              child: const Icon(
                Icons.trending_up,
                size: 64,
                color: Color(0xFF00E5FF),
              ),
            ),
            const SizedBox(height: 32),

            Text(
              'Welcome to Zwesta',
              textAlign: TextAlign.center,
              style: GoogleFonts.poppins(
                color: Colors.white,
                fontSize: 32,
                fontWeight: FontWeight.w700,
                height: 1.2,
              ),
            ),
            const SizedBox(height: 16),

            Text(
              'Building Africa\'s Next-Generation\nFintech Success Story',
              textAlign: TextAlign.center,
              style: GoogleFonts.poppins(
                color: const Color(0xFF69F0AE),
                fontSize: 16,
                fontWeight: FontWeight.w600,
                height: 1.4,
              ),
            ),
            const SizedBox(height: 24),

            Text(
              'Founded by Mr. Zwelihle Mathe, Zwesta is an enterprise-grade automated trading platform serving clients from South Africa to Europe with 1,000+ user capacity.',
              textAlign: TextAlign.center,
              style: GoogleFonts.poppins(
                color: Colors.white70,
                fontSize: 14,
                height: 1.5,
              ),
            ),
          ],
        ),
      );

  Widget _buildPage2() => Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: const Color(0xFFF3BA2F).withOpacity(0.15),
                shape: BoxShape.circle,
                border: Border.all(
                  color: const Color(0xFFF3BA2F),
                  width: 2,
                ),
              ),
              child: const Icon(
                Icons.smart_toy,
                size: 64,
                color: Color(0xFFF3BA2F),
              ),
            ),
            const SizedBox(height: 32),

            Text(
              'Automated Trading Bots',
              textAlign: TextAlign.center,
              style: GoogleFonts.poppins(
                color: Colors.white,
                fontSize: 28,
                fontWeight: FontWeight.w700,
                height: 1.2,
              ),
            ),
            const SizedBox(height: 16),

            Text(
              'Set up once, trade 24/7',
              textAlign: TextAlign.center,
              style: GoogleFonts.poppins(
                color: const Color(0xFF00E5FF),
                fontSize: 16,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 24),

            ...[
              _buildFeature(
                Icons.auto_awesome,
                'AI-Powered Signals',
                'Advanced algorithms analyze market conditions and generate high-probability trading opportunities',
                const Color(0xFF69F0AE),
              ),
              const SizedBox(height: 16),
              _buildFeature(
                Icons.shield,
                'Adaptive Risk Management',
                'Intelligent position sizing and auto-demotion of losing strategies',
                const Color(0xFFFF8A80),
              ),
              const SizedBox(height: 16),
              _buildFeature(
                Icons.trending_up,
                'Multi-Broker Support',
                'Trade across Binance, Exness MT5, and more brokers simultaneously',
                const Color(0xFFFFA726),
              ),
            ],
          ],
        ),
      );

  Widget _buildPage3() => Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: const Color(0xFF7C4DFF).withOpacity(0.15),
                shape: BoxShape.circle,
                border: Border.all(
                  color: const Color(0xFF7C4DFF),
                  width: 2,
                ),
              ),
              child: const Icon(
                Icons.account_balance_wallet,
                size: 64,
                color: Color(0xFF7C4DFF),
              ),
            ),
            const SizedBox(height: 32),

            Text(
              'Multi-Asset Trading',
              textAlign: TextAlign.center,
              style: GoogleFonts.poppins(
                color: Colors.white,
                fontSize: 28,
                fontWeight: FontWeight.w700,
                height: 1.2,
              ),
            ),
            const SizedBox(height: 16),

            Text(
              'Diversify across asset classes',
              textAlign: TextAlign.center,
              style: GoogleFonts.poppins(
                color: const Color(0xFF00E5FF),
                fontSize: 16,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 32),

            _buildAssetCard('₿', 'Cryptocurrency', 'BTC, ETH, altcoins', const Color(0xFFF3BA2F)),
            const SizedBox(height: 16),
            _buildAssetCard('€', 'Forex Majors', 'EUR/USD, GBP/USD, USD/CAD', const Color(0xFF69F0AE)),
            const SizedBox(height: 16),
            _buildAssetCard('⚡', 'Commodities', 'Gold (XAU), Oil, Silver', const Color(0xFFFFD600)),
          ],
        ),
      );

  Widget _buildPage4() => Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: const Color(0xFF69F0AE).withOpacity(0.15),
                shape: BoxShape.circle,
                border: Border.all(
                  color: const Color(0xFF69F0AE),
                  width: 2,
                ),
              ),
              child: const Icon(
                Icons.security,
                size: 64,
                color: Color(0xFF69F0AE),
              ),
            ),
            const SizedBox(height: 32),

            Text(
              'Enterprise-Grade\nInfrastructure',
              textAlign: TextAlign.center,
              style: GoogleFonts.poppins(
                color: Colors.white,
                fontSize: 28,
                fontWeight: FontWeight.w700,
                height: 1.2,
              ),
            ),
            const SizedBox(height: 24),

            _buildInfraFeature(
              '🗄️',
              'PostgreSQL Database',
              '1,000+ user capacity',
            ),
            _buildInfraFeature(
              '🔐',
              'Encrypted Credentials',
              'AES-256 encryption',
            ),
            _buildInfraFeature(
              '📊',
              'Real-Time Analytics',
              'Live P&L tracking',
            ),
            _buildInfraFeature(
              '🌍',
              'Global Reach',
              'South Africa to Europe',
            ),
          ],
        ),
      );

  Widget _buildPage5() => Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: const Color(0xFF00E5FF).withOpacity(0.15),
                shape: BoxShape.circle,
                border: Border.all(
                  color: const Color(0xFF00E5FF),
                  width: 2,
                ),
              ),
              child: const Icon(
                Icons.rocket_launch,
                size: 64,
                color: Color(0xFF00E5FF),
              ),
            ),
            const SizedBox(height: 32),

            Text(
              'Ready to Start?',
              textAlign: TextAlign.center,
              style: GoogleFonts.poppins(
                color: Colors.white,
                fontSize: 32,
                fontWeight: FontWeight.w700,
                height: 1.2,
              ),
            ),
            const SizedBox(height: 16),

            Text(
              'Join 1,000+ users trading with Zwesta',
              textAlign: TextAlign.center,
              style: GoogleFonts.poppins(
                color: const Color(0xFF69F0AE),
                fontSize: 16,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 32),

            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.05),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(
                  color: Colors.white.withOpacity(0.1),
                ),
              ),
              child: Column(
                children: [
                  _buildChecklistItem('✅', 'Create your first trading bot'),
                  _buildChecklistItem('✅', 'Connect broker credentials'),
                  _buildChecklistItem('✅', 'Start with DEMO mode'),
                  _buildChecklistItem('✅', 'Monitor performance 24/7'),
                  _buildChecklistItem('✅', 'Scale to LIVE when ready'),
                ],
              ),
            ),
            const SizedBox(height: 24),

            Text(
              'Tap "Get Started" to begin your journey',
              textAlign: TextAlign.center,
              style: GoogleFonts.poppins(
                color: Colors.white60,
                fontSize: 13,
                fontStyle: FontStyle.italic,
              ),
            ),
          ],
        ),
      );

  Widget _buildFeature(IconData icon, String title, String description, Color color) =>
      Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: color.withOpacity(0.15),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, color: color, size: 24),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: GoogleFonts.poppins(
                    color: Colors.white,
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  description,
                  style: GoogleFonts.poppins(
                    color: Colors.white60,
                    fontSize: 12,
                    height: 1.3,
                  ),
                ),
              ],
            ),
          ),
        ],
      );

  Widget _buildAssetCard(String emoji, String title, String examples, Color color) =>
      Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: color.withOpacity(0.1),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: color.withOpacity(0.3),
          ),
        ),
        child: Row(
          children: [
            Text(
              emoji,
              style: const TextStyle(fontSize: 32),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: GoogleFonts.poppins(
                      color: Colors.white,
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  Text(
                    examples,
                    style: GoogleFonts.poppins(
                      color: Colors.white60,
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      );

  Widget _buildInfraFeature(String emoji, String title, String subtitle) =>
      Padding(
        padding: const EdgeInsets.symmetric(vertical: 12),
        child: Row(
          children: [
            Text(
              emoji,
              style: const TextStyle(fontSize: 28),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: GoogleFonts.poppins(
                      color: Colors.white,
                      fontSize: 15,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  Text(
                    subtitle,
                    style: GoogleFonts.poppins(
                      color: const Color(0xFF69F0AE),
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      );

  Widget _buildChecklistItem(String emoji, String text) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 6),
        child: Row(
          children: [
            Text(
              emoji,
              style: const TextStyle(fontSize: 18),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                text,
                style: GoogleFonts.poppins(
                  color: Colors.white,
                  fontSize: 13,
                ),
              ),
            ),
          ],
        ),
      );
}

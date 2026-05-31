import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Semantic colors for trade P&L, status badges, and risk indicators.
/// Use via `Theme.of(context).extension<AppSemanticColors>()` or
/// the `context.semantic` shortcut below.
class AppSemanticColors extends ThemeExtension<AppSemanticColors> {
  final Color success;
  final Color danger;
  final Color warning;
  final Color info;
  final Color profit;
  final Color loss;
  final Color neutral;

  const AppSemanticColors({
    required this.success,
    required this.danger,
    required this.warning,
    required this.info,
    required this.profit,
    required this.loss,
    required this.neutral,
  });

  static const light = AppSemanticColors(
    success: Color(0xFF2E7D32),
    danger: Color(0xFFC62828),
    warning: Color(0xFFEF6C00),
    info: Color(0xFF1565C0),
    profit: Color(0xFF2E7D32),
    loss: Color(0xFFC62828),
    neutral: Color(0xFF616161),
  );

  static const dark = AppSemanticColors(
    success: Color(0xFF4CAF50),
    danger: Color(0xFFFF5252),
    warning: Color(0xFFFFB74D),
    info: Color(0xFF64B5F6),
    profit: Color(0xFF4CAF50),
    loss: Color(0xFFFF5252),
    neutral: Color(0xFFB0BEC5),
  );

  @override
  AppSemanticColors copyWith({
    Color? success,
    Color? danger,
    Color? warning,
    Color? info,
    Color? profit,
    Color? loss,
    Color? neutral,
  }) {
    return AppSemanticColors(
      success: success ?? this.success,
      danger: danger ?? this.danger,
      warning: warning ?? this.warning,
      info: info ?? this.info,
      profit: profit ?? this.profit,
      loss: loss ?? this.loss,
      neutral: neutral ?? this.neutral,
    );
  }

  @override
  AppSemanticColors lerp(ThemeExtension<AppSemanticColors>? other, double t) {
    if (other is! AppSemanticColors) return this;
    return AppSemanticColors(
      success: Color.lerp(success, other.success, t)!,
      danger: Color.lerp(danger, other.danger, t)!,
      warning: Color.lerp(warning, other.warning, t)!,
      info: Color.lerp(info, other.info, t)!,
      profit: Color.lerp(profit, other.profit, t)!,
      loss: Color.lerp(loss, other.loss, t)!,
      neutral: Color.lerp(neutral, other.neutral, t)!,
    );
  }
}

extension AppSemanticColorsX on BuildContext {
  AppSemanticColors get semantic =>
      Theme.of(this).extension<AppSemanticColors>() ?? AppSemanticColors.dark;
}

class AppTheme {
  static const _primary = Color(0xFF1E88E5);
  static const _secondary = Color(0xFFFF6B6B);
  static const _darkBg = Color(0xFF0A0E21);
  static const _darkSurface = Color(0xFF1A1F3A);

  static const _pageTransitions = PageTransitionsTheme(
    builders: {
      TargetPlatform.android: PredictiveBackPageTransitionsBuilder(),
      TargetPlatform.iOS: CupertinoPageTransitionsBuilder(),
      TargetPlatform.windows: FadeUpwardsPageTransitionsBuilder(),
      TargetPlatform.macOS: CupertinoPageTransitionsBuilder(),
      TargetPlatform.linux: FadeUpwardsPageTransitionsBuilder(),
    },
  );

  static ThemeData lightTheme = ThemeData(
    brightness: Brightness.light,
    primaryColor: _primary,
    colorScheme: const ColorScheme.light(
      primary: _primary,
      secondary: _secondary,
      surface: Colors.white,
      onPrimary: Colors.white,
      onSecondary: Colors.white,
      onSurface: Colors.black,
      error: Color(0xFFC62828),
    ),
    extensions: const [AppSemanticColors.light],
    scaffoldBackgroundColor: Colors.white,
    pageTransitionsTheme: _pageTransitions,
    appBarTheme: const AppBarTheme(
      backgroundColor: Colors.transparent,
      elevation: 0,
      iconTheme: IconThemeData(color: _primary),
      titleTextStyle: TextStyle(
        color: _primary,
        fontWeight: FontWeight.bold,
        fontSize: 20,
      ),
    ),
    textTheme: GoogleFonts.poppinsTextTheme().copyWith(
      bodyLarge: GoogleFonts.poppins(fontSize: 16, color: Colors.black),
      bodyMedium: GoogleFonts.poppins(fontSize: 14, color: Colors.black87),
      titleLarge: GoogleFonts.poppins(
          fontSize: 20, fontWeight: FontWeight.bold, color: _primary),
      titleMedium: GoogleFonts.poppins(
          fontSize: 16, fontWeight: FontWeight.w600, color: _primary),
      labelLarge: GoogleFonts.poppins(
          fontSize: 14, fontWeight: FontWeight.w600, color: _primary),
    ),
    cardTheme: CardThemeData(
      color: Colors.white,
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
    ),
    chipTheme: ChipThemeData(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      labelStyle: GoogleFonts.poppins(fontSize: 12),
    ),
    progressIndicatorTheme: const ProgressIndicatorThemeData(
      color: _primary,
      linearTrackColor: Color(0x331E88E5),
    ),
    inputDecorationTheme: InputDecorationTheme(
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
      filled: true,
      fillColor: Colors.white,
      contentPadding:
          const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
    ),
    snackBarTheme: SnackBarThemeData(
      behavior: SnackBarBehavior.floating,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
    ),
    buttonTheme: const ButtonThemeData(
      buttonColor: _primary,
      textTheme: ButtonTextTheme.primary,
    ),
  );

  static ThemeData darkTheme = ThemeData(
    brightness: Brightness.dark,
    primaryColor: _primary,
    colorScheme: const ColorScheme.dark(
      primary: _primary,
      secondary: _secondary,
      surface: _darkSurface,
      onPrimary: Colors.white,
      onSecondary: Colors.white,
      onSurface: Colors.white,
      error: Color(0xFFFF5252),
    ),
    extensions: const [AppSemanticColors.dark],
    scaffoldBackgroundColor: _darkBg,
    pageTransitionsTheme: _pageTransitions,
    appBarTheme: const AppBarTheme(
      backgroundColor: _darkBg,
      elevation: 0,
      iconTheme: IconThemeData(color: Colors.white),
      titleTextStyle: TextStyle(
        color: Colors.white,
        fontWeight: FontWeight.bold,
        fontSize: 20,
      ),
    ),
    textTheme: GoogleFonts.poppinsTextTheme().copyWith(
      bodyLarge: GoogleFonts.poppins(fontSize: 16, color: Colors.white),
      bodyMedium: GoogleFonts.poppins(fontSize: 14, color: Colors.white70),
      titleLarge: GoogleFonts.poppins(
          fontSize: 20, fontWeight: FontWeight.bold, color: Colors.white),
      titleMedium: GoogleFonts.poppins(
          fontSize: 16, fontWeight: FontWeight.w600, color: Colors.white),
      labelLarge: GoogleFonts.poppins(
          fontSize: 14, fontWeight: FontWeight.w600, color: Colors.white),
    ),
    cardTheme: CardThemeData(
      color: _darkSurface.withValues(alpha: 0.8),
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      shadowColor: Colors.black.withValues(alpha: 0.3),
    ),
    chipTheme: ChipThemeData(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      backgroundColor: _darkSurface.withValues(alpha: 0.6),
      labelStyle: GoogleFonts.poppins(fontSize: 12, color: Colors.white),
      side: BorderSide(color: Colors.white.withValues(alpha: 0.12)),
    ),
    progressIndicatorTheme: const ProgressIndicatorThemeData(
      color: _primary,
      linearTrackColor: Color(0x331E88E5),
    ),
    inputDecorationTheme: InputDecorationTheme(
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.2)),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.2)),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: _primary),
      ),
      filled: true,
      fillColor: _darkSurface.withValues(alpha: 0.6),
      contentPadding:
          const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      labelStyle: GoogleFonts.poppins(color: Colors.white70),
      hintStyle: GoogleFonts.poppins(color: Colors.white54),
    ),
    buttonTheme: const ButtonThemeData(
      buttonColor: _primary,
      textTheme: ButtonTextTheme.primary,
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: _primary,
        foregroundColor: Colors.white,
        elevation: 4,
        shadowColor: Colors.black.withValues(alpha: 0.3),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(foregroundColor: _primary),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: Colors.white,
        side: BorderSide(color: Colors.white.withValues(alpha: 0.3)),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    ),
    dialogTheme: DialogThemeData(
      backgroundColor: _darkSurface,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
    ),
    bottomSheetTheme: const BottomSheetThemeData(
      backgroundColor: _darkSurface,
    ),
    snackBarTheme: SnackBarThemeData(
      backgroundColor: _darkSurface,
      contentTextStyle: GoogleFonts.poppins(color: Colors.white),
      actionTextColor: _primary,
      behavior: SnackBarBehavior.floating,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
    ),
  );
}

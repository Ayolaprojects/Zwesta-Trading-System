import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'app_theme.dart';

class AppStyles {
  AppStyles._();

  static TextStyle heading(BuildContext context) {
    final semantic = context.semantic;
    return GoogleFonts.poppins(
      fontSize: 22,
      fontWeight: FontWeight.w700,
      color: Theme.of(context).colorScheme.onSurface,
      height: 1.3,
    );
  }

  static TextStyle title(BuildContext context) {
    return GoogleFonts.poppins(
      fontSize: 18,
      fontWeight: FontWeight.w600,
      color: Theme.of(context).colorScheme.onSurface,
      height: 1.3,
    );
  }

  static TextStyle subtitle(BuildContext context) {
    return GoogleFonts.poppins(
      fontSize: 15,
      fontWeight: FontWeight.w500,
      color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.85),
      height: 1.3,
    );
  }

  static TextStyle body(BuildContext context) {
    return GoogleFonts.poppins(
      fontSize: 14,
      fontWeight: FontWeight.w400,
      color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.85),
      height: 1.5,
    );
  }

  static TextStyle caption(BuildContext context) {
    return GoogleFonts.poppins(
      fontSize: 12,
      fontWeight: FontWeight.w400,
      color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.65),
      height: 1.4,
    );
  }

  static TextStyle overline(BuildContext context) {
    return GoogleFonts.poppins(
      fontSize: 11,
      fontWeight: FontWeight.w600,
      color: Theme.of(context).colorScheme.primary,
      letterSpacing: 1.2,
      height: 1.4,
    );
  }

  static TextStyle profit(BuildContext context) {
    return GoogleFonts.poppins(
      fontSize: 16,
      fontWeight: FontWeight.w700,
      color: context.semantic.profit,
      height: 1.3,
    );
  }

  static TextStyle loss(BuildContext context) {
    return GoogleFonts.poppins(
      fontSize: 16,
      fontWeight: FontWeight.w700,
      color: context.semantic.loss,
      height: 1.3,
    );
  }

  static TextStyle badge(BuildContext context) {
    return GoogleFonts.poppins(
      fontSize: 12,
      fontWeight: FontWeight.w600,
      color: Theme.of(context).colorScheme.onPrimary,
      height: 1.2,
    );
  }
}

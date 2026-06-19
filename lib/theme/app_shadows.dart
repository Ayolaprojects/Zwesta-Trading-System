import 'package:flutter/material.dart';

class AppShadows {
  AppShadows._();

  static const double blurXs = 4;
  static const double blurSm = 8;
  static const double blurMd = 12;
  static const double blurLg = 16;
  static const Offset offsetXs = Offset(0, 1);
  static const Offset offsetSm = Offset(0, 2);
  static const Offset offsetMd = Offset(0, 4);
  static const Offset offsetLg = Offset(0, 6);

  static List<BoxShadow> get xs => [
    BoxShadow(color: Colors.black.withValues(alpha: 0.06), blurRadius: blurXs, offset: offsetXs),
  ];

  static List<BoxShadow> get sm => [
    BoxShadow(color: Colors.black.withValues(alpha: 0.08), blurRadius: blurSm, offset: offsetSm),
  ];

  static List<BoxShadow> get md => [
    BoxShadow(color: Colors.black.withValues(alpha: 0.10), blurRadius: blurMd, offset: offsetMd),
  ];

  static List<BoxShadow> get lg => [
    BoxShadow(color: Colors.black.withValues(alpha: 0.12), blurRadius: blurLg, offset: offsetLg),
  ];

  static List<BoxShadow> get coloredMd => [
    BoxShadow(color: const Color(0xFF1E88E5).withValues(alpha: 0.25), blurRadius: blurMd, offset: offsetMd),
  ];
  
  static List<BoxShadow> get errorMd => [
    BoxShadow(color: Colors.red.withValues(alpha: 0.25), blurRadius: blurMd, offset: offsetMd),
  ];
  
  static List<BoxShadow> get successMd => [
    BoxShadow(color: Colors.green.withValues(alpha: 0.25), blurRadius: blurMd, offset: offsetMd),
  ];
}

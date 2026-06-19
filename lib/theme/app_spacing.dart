import 'package:flutter/material.dart';

class AppSpacing {
  AppSpacing._();

  static const double xs = 4.0;
  static const double sm = 8.0;
  static const double md = 12.0;
  static const double lg = 16.0;
  static const double xl = 24.0;
  static const double xxl = 32.0;

  static const EdgeInsetsGeometry paddingAllXs = EdgeInsets.all(xs);
  static const EdgeInsetsGeometry paddingAllSm = EdgeInsets.all(sm);
  static const EdgeInsetsGeometry paddingAllMd = EdgeInsets.all(md);
  static const EdgeInsetsGeometry paddingAllLg = EdgeInsets.all(lg);
  static const EdgeInsetsGeometry paddingAllXl = EdgeInsets.all(xl);

  static const EdgeInsetsGeometry paddingSymmetricXs = EdgeInsets.symmetric(horizontal: xs, vertical: xs);
  static const EdgeInsetsGeometry paddingSymmetricSm = EdgeInsets.symmetric(horizontal: sm, vertical: sm);
  static const EdgeInsetsGeometry paddingSymmetricMd = EdgeInsets.symmetric(horizontal: md, vertical: md);
  static const EdgeInsetsGeometry paddingSymmetricLg = EdgeInsets.symmetric(horizontal: lg, vertical: lg);

  static const EdgeInsetsGeometry paddingVerticalXs = EdgeInsets.symmetric(vertical: xs);
  static const EdgeInsetsGeometry paddingVerticalSm = EdgeInsets.symmetric(vertical: sm);
  static const EdgeInsetsGeometry paddingVerticalMd = EdgeInsets.symmetric(vertical: md);
  static const EdgeInsetsGeometry paddingVerticalLg = EdgeInsets.symmetric(vertical: lg);

  static const EdgeInsetsGeometry paddingHorizontalSm = EdgeInsets.symmetric(horizontal: sm);
  static const EdgeInsetsGeometry paddingHorizontalMd = EdgeInsets.symmetric(horizontal: md);
  static const EdgeInsetsGeometry paddingHorizontalLg = EdgeInsets.symmetric(horizontal: lg);

  static const SizedBox spaceXs = SizedBox(height: xs, width: xs);
  static const SizedBox spaceSm = SizedBox(height: sm, width: sm);
  static const SizedBox spaceMd = SizedBox(height: md, width: md);
  static const SizedBox spaceLg = SizedBox(height: lg, width: lg);
  static const SizedBox spaceXl = SizedBox(height: xl, width: xl);
}

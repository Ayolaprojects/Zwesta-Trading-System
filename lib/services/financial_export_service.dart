import 'dart:io';

import 'package:cross_file/cross_file.dart';
import 'package:intl/intl.dart';
import 'package:path_provider/path_provider.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import 'package:permission_handler/permission_handler.dart';
import 'package:share_plus/share_plus.dart';

import '../models/account.dart';
import '../models/financial_statement.dart';
import '../models/trade.dart';

class FinancialExportService {
  static Future<String> saveCsv(String filename, String csvContent) async {
    final directory = await getApplicationDocumentsDirectory();
    final file = File('${directory.path}/$filename');
    await file.writeAsString(csvContent, flush: true);
    return file.path;
  }

  static Future<String> savePdf(String filename, pw.Document pdf) async {
    final directory = await getApplicationDocumentsDirectory();
    final file = File('${directory.path}/$filename');
    final bytes = await pdf.save();
    await file.writeAsBytes(bytes, flush: true);
    return file.path;
  }

  static Future<String?> saveCsvToDownloads(String filename, String csvContent) async {
    // Request storage permission on Android
    try {
      if (Platform.isAndroid) {
        final status = await Permission.storage.request();
        if (!status.isGranted) return null;
      }

      final dirs = await getExternalStorageDirectories(type: StorageDirectory.downloads);
      String dirPath;
      if (dirs != null && dirs.isNotEmpty) {
        dirPath = dirs.first.path;
      } else {
        final fallback = await getApplicationDocumentsDirectory();
        dirPath = fallback.path;
      }
      final file = File('$dirPath/$filename');
      await file.writeAsString(csvContent, flush: true);
      return file.path;
    } catch (e) {
      return null;
    }
  }

  static Future<String?> saveCsvToDirectory(String directoryPath, String filename, String csvContent) async {
    try {
      final dir = Directory(directoryPath);
      if (!await dir.exists()) {
        await dir.create(recursive: true);
      }
      final file = File('${dir.path}/$filename');
      await file.writeAsString(csvContent, flush: true);
      return file.path;
    } catch (e) {
      return null;
    }
  }

  static Future<String?> savePdfToDirectory(String directoryPath, String filename, pw.Document pdf) async {
    try {
      final dir = Directory(directoryPath);
      if (!await dir.exists()) {
        await dir.create(recursive: true);
      }
      final file = File('${dir.path}/$filename');
      final bytes = await pdf.save();
      await file.writeAsBytes(bytes, flush: true);
      return file.path;
    } catch (e) {
      return null;
    }
  }

  static String buildFinancialStatementCsv(
    FinancialStatement statement,
    List<Trade> trades,
  ) {
    final buffer = StringBuffer();
    final dateFormat = DateFormat('yyyy-MM-dd');

    buffer.writeln('Zwesta Trading Financial Analytics');
    buffer.writeln('Account ID,${statement.accountId}');
    buffer.writeln('Currency,${statement.currency}');
    buffer.writeln('Period,${dateFormat.format(statement.startDate)} to ${dateFormat.format(statement.endDate)}');
    buffer.writeln('Generated At,${DateFormat('yyyy-MM-dd HH:mm:ss').format(statement.generatedAt)}');
    buffer.writeln();

    buffer.writeln('Summary');
    buffer.writeln('Metric,Value');
    buffer.writeln('Capital Invested,${statement.capitalInvested}');
    buffer.writeln('Additional Investments,${statement.additionalInvestments}');
    buffer.writeln('Total Capital,${statement.totalCapital}');
    buffer.writeln('Trading Profit,${statement.tradingProfit}');
    buffer.writeln('Dividends,${statement.dividends}');
    buffer.writeln('Interest,${statement.interest}');
    buffer.writeln('Other Income,${statement.otherIncome}');
    buffer.writeln('Total Revenue,${statement.totalRevenue}');
    buffer.writeln('Commissions,${statement.commissions}');
    buffer.writeln('Spreads,${statement.spreads}');
    buffer.writeln('Platform Fees,${statement.platformFees}');
    buffer.writeln('Withdrawal Fees,${statement.withdrawalFees}');
    buffer.writeln('Other Costs,${statement.otherCosts}');
    buffer.writeln('Total Costs,${statement.totalCosts}');
    buffer.writeln('Gross Profit,${statement.grossProfit}');
    buffer.writeln('Operating Profit,${statement.operatingProfit}');
    buffer.writeln('Net Profit,${statement.netProfit}');
    buffer.writeln('Profit Margin,${statement.profitMargin}');
    buffer.writeln('ROI,${statement.ROI}');
    buffer.writeln('Opening Balance,${statement.openingBalance}');
    buffer.writeln('Closing Balance,${statement.closingBalance}');
    buffer.writeln('Balance Change,${statement.balanceChange}');
    buffer.writeln();

    buffer.writeln('Trade Details');
    buffer.writeln(
      'Trade ID,Symbol,Type,Quantity,Entry Price,Exit Price,Profit,Profit %,Opened At,Closed At,Status,Currency',
    );
    for (final trade in trades) {
      buffer.writeln(
        '${_escapeCsvValue(trade.id)},${_escapeCsvValue(trade.symbol)},${trade.type == TradeType.buy ? 'BUY' : 'SELL'},'
        '${trade.quantity},${trade.entryPrice},${trade.currentPrice ?? ''},${trade.profit ?? ''},'
        '${trade.profitPercentage ?? ''},${trade.openedAt.toIso8601String()},'
        '${trade.closedAt?.toIso8601String() ?? ''},${trade.status.toString().split('.').last},${trade.currency}',
      );
    }

    return buffer.toString();
  }

  static String _escapeCsvValue(String value) {
    final escaped = value.replaceAll('"', '""');
    if (escaped.contains(',') || escaped.contains('\n') || escaped.contains('"')) {
      return '"$escaped"';
    }
    return escaped;
  }

  static Future<pw.Document> generateFinancialStatementPdf(
    FinancialStatement statement,
    Account account,
    List<Trade> trades,
  ) async {
    final pdf = pw.Document();
    final dateFormat = DateFormat('MMMM dd, yyyy');
    final currencyFormat = NumberFormat.currency(symbol: '${account.currency} ');

    pdf.addPage(
      pw.MultiPage(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.all(32),
        build: (context) => [
          _buildPdfHeader(statement, dateFormat),
          pw.SizedBox(height: 16),
          _buildPdfAccountInfo(account, statement, currencyFormat),
          pw.SizedBox(height: 20),
          _buildPdfSummarySection(statement, currencyFormat),
          pw.SizedBox(height: 20),
          _buildPdfPerformanceSection(statement, currencyFormat),
          pw.SizedBox(height: 20),
          if (trades.isNotEmpty) _buildPdfTradeSection(trades, currencyFormat),
        ],
        footer: (context) => pw.Container(
          alignment: pw.Alignment.centerRight,
          margin: const pw.EdgeInsets.only(top: 12),
          child: pw.Text(
            'Page ${context.pageNumber} / ${context.pagesCount}',
            style: pw.TextStyle(fontSize: 8, color: PdfColors.grey),
          ),
        ),
      ),
    );

    return pdf;
  }

  static pw.Widget _buildPdfHeader(FinancialStatement statement, DateFormat dateFormat) {
    return pw.Column(
      crossAxisAlignment: pw.CrossAxisAlignment.start,
      children: [
        pw.Text('ZWESTA TRADING', style: pw.TextStyle(fontSize: 24, fontWeight: pw.FontWeight.bold)),
        pw.SizedBox(height: 6),
        pw.Text('Financial Analytics Report', style: pw.TextStyle(fontSize: 16, color: PdfColors.blue)),
        pw.SizedBox(height: 10),
        pw.Text('Period: ${dateFormat.format(statement.startDate)} - ${dateFormat.format(statement.endDate)}'),
        pw.Text('Generated: ${dateFormat.format(statement.generatedAt)}'),
        pw.Divider(color: PdfColors.grey400),
      ],
    );
  }

  static pw.Widget _buildPdfAccountInfo(
    Account account,
    FinancialStatement statement,
    NumberFormat currencyFormat,
  ) {
    return pw.Table(
      border: pw.TableBorder.all(color: PdfColors.grey300, width: 0.5),
      children: [
        pw.TableRow(
          decoration: const pw.BoxDecoration(color: PdfColors.blue50),
          children: [
            _pdfTableCell('Account Number', isHeader: true),
            _pdfTableCell('Currency', isHeader: true),
            _pdfTableCell('Status', isHeader: true),
            _pdfTableCell('Opening Balance', isHeader: true),
          ],
        ),
        pw.TableRow(
          children: [
            _pdfTableCell(account.accountNumber),
            _pdfTableCell(account.currency),
            _pdfTableCell(account.status.toUpperCase()),
            _pdfTableCell(currencyFormat.format(statement.openingBalance)),
          ],
        ),
      ],
    );
  }

  static pw.Widget _buildPdfSummarySection(FinancialStatement statement, NumberFormat currencyFormat) {
    return pw.Column(
      crossAxisAlignment: pw.CrossAxisAlignment.start,
      children: [
        pw.Text('Summary', style: pw.TextStyle(fontSize: 14, fontWeight: pw.FontWeight.bold)),
        pw.SizedBox(height: 8),
        pw.Table(
          border: pw.TableBorder.all(color: PdfColors.grey300, width: 0.5),
          children: [
            _pdfTableRow('Trading Profit', currencyFormat.format(statement.tradingProfit)),
            _pdfTableRow('Total Revenue', currencyFormat.format(statement.totalRevenue)),
            _pdfTableRow('Total Costs', currencyFormat.format(statement.totalCosts)),
            _pdfTableRow('Net Profit', currencyFormat.format(statement.netProfit)),
            _pdfTableRow('Net Cash Flow', currencyFormat.format(statement.netCashFlow)),
            _pdfTableRow('Balance Change', currencyFormat.format(statement.balanceChange)),
          ],
        ),
      ],
    );
  }

  static pw.Widget _buildPdfPerformanceSection(FinancialStatement statement, NumberFormat currencyFormat) {
    return pw.Column(
      crossAxisAlignment: pw.CrossAxisAlignment.start,
      children: [
        pw.Text('Performance Metrics', style: pw.TextStyle(fontSize: 14, fontWeight: pw.FontWeight.bold)),
        pw.SizedBox(height: 8),
        pw.Table(
          border: pw.TableBorder.all(color: PdfColors.grey300, width: 0.5),
          children: [
            _pdfTableRow('Profit Margin', '${statement.profitMargin.toStringAsFixed(2)}%'),
            _pdfTableRow('ROI', '${statement.ROI.toStringAsFixed(2)}%'),
            _pdfTableRow('Total Expenses', currencyFormat.format(statement.totalCosts)),
            _pdfTableRow('Total Cash In', currencyFormat.format(statement.totalCashIn)),
            _pdfTableRow('Total Cash Out', currencyFormat.format(statement.totalCashOut)),
          ],
        ),
      ],
    );
  }

  static pw.Widget _buildPdfTradeSection(List<Trade> trades, NumberFormat currencyFormat) {
    return pw.Column(
      crossAxisAlignment: pw.CrossAxisAlignment.start,
      children: [
        pw.Text('Trade Results', style: pw.TextStyle(fontSize: 14, fontWeight: pw.FontWeight.bold)),
        pw.SizedBox(height: 8),
        pw.Table(
          border: pw.TableBorder.all(color: PdfColors.grey300, width: 0.5),
          columnWidths: {
            0: const pw.FlexColumnWidth(2),
            1: const pw.FlexColumnWidth(1.5),
            2: const pw.FlexColumnWidth(1.5),
            3: const pw.FlexColumnWidth(1.5),
            4: const pw.FlexColumnWidth(1.5),
            5: const pw.FlexColumnWidth(1.5),
          },
          children: [
            pw.TableRow(
              decoration: const pw.BoxDecoration(color: PdfColors.blue50),
              children: [
                _pdfTableCell('Symbol', isHeader: true),
                _pdfTableCell('Type', isHeader: true),
                _pdfTableCell('Profit', isHeader: true),
                _pdfTableCell('P/L %', isHeader: true),
                _pdfTableCell('Open', isHeader: true),
                _pdfTableCell('Close', isHeader: true),
              ],
            ),
            ...trades.map(
              (trade) => pw.TableRow(
                children: [
                  _pdfTableCell(trade.symbol),
                  _pdfTableCell(trade.type == TradeType.buy ? 'BUY' : 'SELL'),
                  _pdfTableCell(currencyFormat.format(trade.profit ?? 0.0)),
                  _pdfTableCell('${(trade.profitPercentage ?? 0.0).toStringAsFixed(2)}%'),
                  _pdfTableCell(trade.openedAt.toIso8601String()),
                  _pdfTableCell(trade.closedAt?.toIso8601String() ?? ''),
                ],
              ),
            ),
          ],
        ),
      ],
    );
  }

  static pw.TableRow _pdfTableRow(String label, String value) {
    return pw.TableRow(
      children: [
        _pdfTableCell(label, isHeader: true),
        _pdfTableCell(value),
      ],
    );
  }

  static pw.Widget _pdfTableCell(String text, {bool isHeader = false}) {
    return pw.Padding(
      padding: const pw.EdgeInsets.all(8),
      child: pw.Text(
        text,
        style: pw.TextStyle(
          fontSize: 10,
          fontWeight: isHeader ? pw.FontWeight.bold : pw.FontWeight.normal,
        ),
      ),
    );
  }

  // ==================== TRADES REPORT PDF ====================

  static Future<pw.Document> generateTradesPdf({
    required List<Trade> trades,
    String? brokerName,
    String? accountNumber,
  }) async {
    final dateFormat = DateFormat('MMM dd, yyyy – hh:mm a');
    final currencyFormat = NumberFormat.currency(symbol: r'$');
    final pdf = pw.Document();

    final openTrades = trades.where((t) => t.status == TradeStatus.open).toList();
    final closedTrades = trades.where((t) => t.status == TradeStatus.closed).toList();
    final totalRealizedProfit = closedTrades.fold<double>(
        0.0, (sum, t) => sum + (t.profit ?? 0.0));
    final totalOpenProfit = openTrades.fold<double>(
        0.0, (sum, t) => sum + (t.profit ?? 0.0));
    final winningTrades = closedTrades.where((t) => (t.profit ?? 0) > 0).length;
    final losingTrades = closedTrades.where((t) => (t.profit ?? 0) <= 0).length;
    final winRate = closedTrades.isNotEmpty
        ? (winningTrades / closedTrades.length * 100)
        : 0.0;

    pdf.addPage(
      pw.MultiPage(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.all(40),
        build: (context) => [
          pw.Column(
            crossAxisAlignment: pw.CrossAxisAlignment.start,
            children: [
              pw.Row(
                mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
                children: [
                  pw.Column(
                    crossAxisAlignment: pw.CrossAxisAlignment.start,
                    children: [
                      pw.Text('ZWESTA TRADING',
                          style: pw.TextStyle(
                              fontSize: 24, fontWeight: pw.FontWeight.bold)),
                      pw.SizedBox(height: 4),
                      pw.Text('Trading Analytics Report',
                          style: pw.TextStyle(
                              fontSize: 16,
                              fontWeight: pw.FontWeight.bold,
                              color: PdfColors.blue)),
                    ],
                  ),
                  pw.Column(
                    crossAxisAlignment: pw.CrossAxisAlignment.end,
                    children: [
                      pw.Text('Report Generated',
                          style: const pw.TextStyle(fontSize: 10)),
                      pw.Text(dateFormat.format(DateTime.now()),
                          style: pw.TextStyle(
                              fontSize: 12, fontWeight: pw.FontWeight.bold)),
                    ],
                  ),
                ],
              ),
              if (brokerName != null)
                pw.Table(
                  border: pw.TableBorder.all(color: PdfColors.grey300, width: 0.5),
                  columnWidths: {0: const pw.FlexColumnWidth(1), 1: const pw.FlexColumnWidth(2)},
                  children: [
                    _pdfTableRow('Broker', brokerName),
                    if (accountNumber != null)
                      _pdfTableRow('Account #', accountNumber),
                  ],
                ),
              pw.Divider(height: 30),
            ],
          ),
          pw.Column(
            crossAxisAlignment: pw.CrossAxisAlignment.start,
            children: [
              pw.Text('Summary',
                  style: pw.TextStyle(
                      fontSize: 14, fontWeight: pw.FontWeight.bold)),
              pw.SizedBox(height: 12),
              pw.Table(
                border: pw.TableBorder.all(color: PdfColors.grey300, width: 0.5),
                columnWidths: {0: const pw.FlexColumnWidth(2), 1: const pw.FlexColumnWidth(2)},
                children: [
                  _perfRow('Total Trades', '${trades.length}', isBold: true),
                  _perfRow('Open Trades', '${openTrades.length}', isBold: true),
                  _perfRow('Closed Trades', '${closedTrades.length}', isBold: true),
                  _perfRow('Winning Trades', '$winningTrades', isBold: true),
                  _perfRow('Losing Trades', '$losingTrades', isBold: true),
                  _perfRow('Win Rate', '${winRate.toStringAsFixed(1)}%', isBold: true),
                  _perfRow('Realized P&L', currencyFormat.format(totalRealizedProfit), isBold: true),
                  _perfRow('Unrealized P&L', currencyFormat.format(totalOpenProfit), isBold: true),
                ],
              ),
              pw.SizedBox(height: 24),
            ],
          ),
          if (closedTrades.isNotEmpty)
            pw.Column(
              crossAxisAlignment: pw.CrossAxisAlignment.start,
              children: [
                pw.Text('Closed Trades',
                    style: pw.TextStyle(
                        fontSize: 14, fontWeight: pw.FontWeight.bold)),
                pw.SizedBox(height: 12),
                pw.Table(
                  border:
                      pw.TableBorder.all(color: PdfColors.grey300, width: 0.5),
                  columnWidths: {
                    0: const pw.FlexColumnWidth(1.2),
                    1: const pw.FlexColumnWidth(1),
                    2: const pw.FlexColumnWidth(1),
                    3: const pw.FlexColumnWidth(1),
                    4: const pw.FlexColumnWidth(1.2),
                    5: const pw.FlexColumnWidth(1),
                    6: const pw.FlexColumnWidth(1.2),
                  },
                  children: [
                    pw.TableRow(
                      decoration: const pw.BoxDecoration(color: PdfColors.blue50),
                      children: [
                        _pdfTableCell('Symbol', isHeader: true),
                        _pdfTableCell('Type', isHeader: true),
                        _pdfTableCell('Qty', isHeader: true),
                        _pdfTableCell('Entry', isHeader: true),
                        _pdfTableCell('Exit', isHeader: true),
                        _pdfTableCell('P&L %', isHeader: true),
                        _pdfTableCell('Open Time', isHeader: true),
                      ],
                    ),
                    ...closedTrades.take(100).map((trade) {
                      final profitColor =
                          (trade.profit ?? 0) >= 0 ? PdfColors.green : PdfColors.red;
                      return pw.TableRow(children: [
                        _pdfTableCell(trade.symbol),
                        _pdfTableCell(
                            trade.type == TradeType.buy ? 'BUY' : 'SELL'),
                        _pdfTableCell(trade.quantity.toStringAsFixed(4)),
                        _pdfTableCell(trade.entryPrice.toStringAsFixed(2)),
                        _pdfTableCell(
                            (trade.currentPrice ?? 0).toStringAsFixed(2)),
                        pw.Container(
                          padding: const pw.EdgeInsets.all(8),
                          child: pw.Text(
                            '${(trade.profitPercentage ?? 0).toStringAsFixed(2)}%',
                            style: pw.TextStyle(
                                fontSize: 10, color: profitColor),
                            textAlign: pw.TextAlign.right,
                          ),
                        ),
                        _pdfTableCell(
                            dateFormat.format(trade.openedAt.toLocal())),
                      ]);
                    }),
                  ],
                ),
                pw.SizedBox(height: 24),
              ],
            ),
          if (openTrades.isNotEmpty)
            pw.Column(
              crossAxisAlignment: pw.CrossAxisAlignment.start,
              children: [
                pw.Text('Open Positions',
                    style: pw.TextStyle(
                        fontSize: 14, fontWeight: pw.FontWeight.bold)),
                pw.SizedBox(height: 12),
                pw.Table(
                  border:
                      pw.TableBorder.all(color: PdfColors.grey300, width: 0.5),
                  columnWidths: {
                    0: const pw.FlexColumnWidth(1.2),
                    1: const pw.FlexColumnWidth(1),
                    2: const pw.FlexColumnWidth(1),
                    3: const pw.FlexColumnWidth(1),
                    4: const pw.FlexColumnWidth(1.2),
                    5: const pw.FlexColumnWidth(1),
                  },
                  children: [
                    pw.TableRow(
                      decoration: const pw.BoxDecoration(color: PdfColors.blue50),
                      children: [
                        _pdfTableCell('Symbol', isHeader: true),
                        _pdfTableCell('Type', isHeader: true),
                        _pdfTableCell('Qty', isHeader: true),
                        _pdfTableCell('Entry', isHeader: true),
                        _pdfTableCell('Current', isHeader: true),
                        _pdfTableCell('Unrealized P&L', isHeader: true),
                      ],
                    ),
                    ...openTrades.take(100).map((trade) {
                      final profitColor =
                          (trade.unrealizedProfit ?? 0) >= 0
                              ? PdfColors.green
                              : PdfColors.red;
                      return pw.TableRow(children: [
                        _pdfTableCell(trade.symbol),
                        _pdfTableCell(
                            trade.type == TradeType.buy ? 'BUY' : 'SELL'),
                        _pdfTableCell(trade.quantity.toStringAsFixed(4)),
                        _pdfTableCell(trade.entryPrice.toStringAsFixed(2)),
                        _pdfTableCell(
                            (trade.currentPrice ?? 0).toStringAsFixed(2)),
                        pw.Container(
                          padding: const pw.EdgeInsets.all(8),
                          child: pw.Text(
                            currencyFormat.format(
                                trade.unrealizedProfit ?? 0),
                            style: pw.TextStyle(
                                fontSize: 10, color: profitColor),
                            textAlign: pw.TextAlign.right,
                          ),
                        ),
                      ]);
                    }),
                  ],
                ),
                pw.SizedBox(height: 24),
              ],
            ),
        ],
        footer: (context) => pw.Column(
          children: [
            pw.Divider(),
            pw.Row(
              mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
              children: [
                pw.Text('Zwesta Trading System',
                    style: const pw.TextStyle(fontSize: 8)),
                pw.Text('Page ${context.pageNumber} of ${context.pagesCount}',
                    style: const pw.TextStyle(fontSize: 8)),
              ],
            ),
          ],
        ),
      ),
    );

    return pdf;
  }

  // ==================== BOT REPORT PDF ====================

  static Future<pw.Document> generateBotReportPdf({
    required Map<String, dynamic> bot,
    required List<dynamic> tradeHistory,
    required List<dynamic> openPositions,
  }) async {
    final dateFormat = DateFormat('MMM dd, yyyy – hh:mm a');
    final currencyFormat = NumberFormat.currency(symbol: '\$');
    final pdf = pw.Document();

    final botId = bot['botId']?.toString() ?? '—';
    final botName = bot['name']?.toString() ?? bot['botName']?.toString() ?? 'Bot';
    final broker = bot['brokerName']?.toString() ?? bot['broker_type']?.toString() ?? 'MT5';
    final symbols = bot['symbols'] is List
        ? (bot['symbols'] as List).join(', ')
        : bot['symbols']?.toString() ?? 'N/A';
    final strategy = bot['strategy']?.toString() ?? 'Auto';
    final mode = bot['mode']?.toString() ?? 'demo';
    final totalTrades = int.tryParse(bot['totalTrades']?.toString() ?? '0') ?? 0;
    final winningTrades = int.tryParse(bot['winningTrades']?.toString() ?? '0') ?? 0;
    final winRate = totalTrades > 0 ? (winningTrades / totalTrades * 100) : 0;
    final totalProfit = double.tryParse(bot['totalProfit']?.toString() ?? '0') ?? 0;
    final sessionProfit = double.tryParse(bot['sessionProfit']?.toString() ??
        bot['currentProfit']?.toString() ?? '0') ?? 0;
    final accountBalance = double.tryParse(bot['accountBalance']?.toString() ?? '0') ?? 0;
    final accountEquity = double.tryParse(bot['accountEquity']?.toString() ?? '0') ?? 0;
    final createdAt = bot['createdAt']?.toString() ?? DateTime.now().toIso8601String();

    pdf.addPage(
      pw.MultiPage(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.all(40),
        build: (context) => [
          // Header
          pw.Column(
            crossAxisAlignment: pw.CrossAxisAlignment.start,
            children: [
              pw.Row(
                mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
                children: [
                  pw.Column(
                    crossAxisAlignment: pw.CrossAxisAlignment.start,
                    children: [
                      pw.Text('ZWESTA TRADING', style: pw.TextStyle(fontSize: 24, fontWeight: pw.FontWeight.bold)),
                      pw.SizedBox(height: 4),
                      pw.Text('Bot Activity Report', style: pw.TextStyle(fontSize: 16, fontWeight: pw.FontWeight.bold, color: PdfColors.blue)),
                    ],
                  ),
                  pw.Column(
                    crossAxisAlignment: pw.CrossAxisAlignment.end,
                    children: [
                      pw.Text('Report Generated', style: const pw.TextStyle(fontSize: 10)),
                      pw.Text(dateFormat.format(DateTime.now()), style: pw.TextStyle(fontSize: 12, fontWeight: pw.FontWeight.bold)),
                    ],
                  ),
                ],
              ),
              pw.Divider(height: 30),
            ],
          ),

          // Bot Info Section
          pw.Column(
            crossAxisAlignment: pw.CrossAxisAlignment.start,
            children: [
              pw.Text('Bot Information', style: pw.TextStyle(fontSize: 14, fontWeight: pw.FontWeight.bold)),
              pw.SizedBox(height: 12),
              pw.Table(
                border: pw.TableBorder.all(color: PdfColors.grey300, width: 0.5),
                columnWidths: {0: const pw.FlexColumnWidth(1), 1: const pw.FlexColumnWidth(2)},
                children: [
                  _botInfoRow('Bot ID', botId, isBold: true),
                  _botInfoRow('Name', botName),
                  _botInfoRow('Broker', broker),
                  _botInfoRow('Mode', mode.toUpperCase()),
                  _botInfoRow('Strategy', strategy),
                  _botInfoRow('Symbols', symbols),
                  _botInfoRow('Created', createdAt),
                ],
              ),
              pw.SizedBox(height: 24),
            ],
          ),

          // Performance Summary
          pw.Column(
            crossAxisAlignment: pw.CrossAxisAlignment.start,
            children: [
              pw.Text('Performance Summary', style: pw.TextStyle(fontSize: 14, fontWeight: pw.FontWeight.bold)),
              pw.SizedBox(height: 12),
              pw.Table(
                border: pw.TableBorder.all(color: PdfColors.grey300, width: 0.5),
                columnWidths: {0: const pw.FlexColumnWidth(2), 1: const pw.FlexColumnWidth(2)},
                children: [
                  _perfRow('Total Trades', '$totalTrades', isBold: true),
                  _perfRow('Winning Trades', '$winningTrades', isBold: true),
                  _perfRow('Win Rate', '${winRate.toStringAsFixed(1)}%', isBold: true),
                  _perfRow('Total Profit', currencyFormat.format(totalProfit), isBold: true),
                  _perfRow('Session Profit', currencyFormat.format(sessionProfit), isBold: true),
                  _perfRow('Account Balance', currencyFormat.format(accountBalance), isBold: true),
                  _perfRow('Account Equity', currencyFormat.format(accountEquity), isBold: true),
                ],
              ),
              pw.SizedBox(height: 24),
            ],
          ),

          // Open Positions
          if (openPositions.isNotEmpty)
            pw.Column(
              crossAxisAlignment: pw.CrossAxisAlignment.start,
              children: [
                pw.Text('Open Positions', style: pw.TextStyle(fontSize: 14, fontWeight: pw.FontWeight.bold)),
                pw.SizedBox(height: 12),
                pw.Table(
                  border: pw.TableBorder.all(color: PdfColors.grey300, width: 0.5),
                  columnWidths: {
                    0: const pw.FlexColumnWidth(1.2),
                    1: const pw.FlexColumnWidth(1),
                    2: const pw.FlexColumnWidth(1),
                    3: const pw.FlexColumnWidth(1),
                    4: const pw.FlexColumnWidth(1),
                  },
                  children: [
                    pw.TableRow(
                      decoration: const pw.BoxDecoration(color: PdfColors.blue50),
                      children: [
                        _pdfTableCell('Symbol', isHeader: true),
                        _pdfTableCell('Type', isHeader: true),
                        _pdfTableCell('Volume', isHeader: true),
                        _pdfTableCell('Entry Price', isHeader: true),
                        _pdfTableCell('Profit', isHeader: true),
                      ],
                    ),
                    ...openPositions.map((pos) => pw.TableRow(
                      children: [
                        _pdfTableCell((pos['symbol'] ?? '—').toString()),
                        _pdfTableCell((pos['type'] ?? '—').toString().toUpperCase()),
                        _pdfTableCell((pos['volume'] ?? pos['size'] ?? '0').toString()),
                        _pdfTableCell((pos['entryPrice'] ?? pos['level'] ?? '0').toString()),
                        _pdfTableCell(currencyFormat.format(double.tryParse(pos['profit']?.toString() ?? '0') ?? 0)),
                      ],
                    )),
                  ],
                ),
                pw.SizedBox(height: 24),
              ],
            ),

          // Trade History
          if (tradeHistory.isNotEmpty)
            pw.Column(
              crossAxisAlignment: pw.CrossAxisAlignment.start,
              children: [
                pw.Text('Trade History', style: pw.TextStyle(fontSize: 14, fontWeight: pw.FontWeight.bold)),
                pw.SizedBox(height: 12),
                pw.Table(
                  border: pw.TableBorder.all(color: PdfColors.grey300, width: 0.5),
                  columnWidths: {
                    0: const pw.FlexColumnWidth(1.2),
                    1: const pw.FlexColumnWidth(1),
                    2: const pw.FlexColumnWidth(1),
                    3: const pw.FlexColumnWidth(1.2),
                    4: const pw.FlexColumnWidth(1),
                  },
                  children: [
                    pw.TableRow(
                      decoration: const pw.BoxDecoration(color: PdfColors.blue50),
                      children: [
                        _pdfTableCell('Symbol', isHeader: true),
                        _pdfTableCell('Type', isHeader: true),
                        _pdfTableCell('Profit', isHeader: true),
                        _pdfTableCell('Open Time', isHeader: true),
                        _pdfTableCell('Status', isHeader: true),
                      ],
                    ),
                    ...tradeHistory.take(50).map((trade) {
                      final profit = double.tryParse(trade['profit']?.toString() ?? '0') ?? 0;
                      final profitColor = profit >= 0 ? PdfColors.green : PdfColors.red;
                      return pw.TableRow(
                        children: [
                          _pdfTableCell((trade['symbol'] ?? '—').toString()),
                          _pdfTableCell((trade['type'] ?? '—').toString().toUpperCase()),
                          pw.Container(
                            padding: const pw.EdgeInsets.all(8),
                            child: pw.Text(
                              currencyFormat.format(profit),
                              style: pw.TextStyle(fontSize: 10, color: profitColor),
                              textAlign: pw.TextAlign.right,
                            ),
                          ),
                          _pdfTableCell((trade['time_open'] ?? trade['time'] ?? '—').toString()),
                          _pdfTableCell((trade['status'] ?? 'closed').toString().toUpperCase()),
                        ],
                      );
                    }),
                  ],
                ),
              ],
            ),
        ],
        footer: (context) => pw.Column(
          children: [
            pw.Divider(),
            pw.Row(
              mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
              children: [
                pw.Text('Zwesta Trading System', style: const pw.TextStyle(fontSize: 8)),
                pw.Text('Page ${context.pageNumber} of ${context.pagesCount}', style: const pw.TextStyle(fontSize: 8)),
              ],
            ),
          ],
        ),
      ),
    );

    return pdf;
  }

  static pw.TableRow _botInfoRow(String label, String value, {bool isBold = false}) {
    return pw.TableRow(
      children: [
        pw.Container(
          padding: const pw.EdgeInsets.all(8),
          child: pw.Text(label, style: pw.TextStyle(fontSize: 10, fontWeight: isBold ? pw.FontWeight.bold : pw.FontWeight.normal)),
        ),
        pw.Container(
          padding: const pw.EdgeInsets.all(8),
          child: pw.Text(value, style: pw.TextStyle(fontSize: 10, fontWeight: isBold ? pw.FontWeight.bold : pw.FontWeight.normal)),
        ),
      ],
    );
  }

  static pw.TableRow _perfRow(String label, String value, {bool isBold = false}) {
    return pw.TableRow(
      children: [
        pw.Container(
          padding: const pw.EdgeInsets.all(8),
          child: pw.Text(label, style: pw.TextStyle(fontSize: 10, fontWeight: isBold ? pw.FontWeight.bold : pw.FontWeight.normal)),
        ),
        pw.Container(
          padding: const pw.EdgeInsets.all(8),
          child: pw.Text(value, style: pw.TextStyle(fontSize: 10, fontWeight: isBold ? pw.FontWeight.bold : pw.FontWeight.normal), textAlign: pw.TextAlign.right),
        ),
      ],
    );
  }

  // ==================== CONSOLIDATED REPORTS PDF ====================

  static Future<pw.Document> generateReportsPdf({
    required List<Map<String, dynamic>> reports,
    required String mode,
  }) async {
    final dateFormat = DateFormat('MMM dd, yyyy – hh:mm a');
    final currencyFormat = NumberFormat.currency(symbol: '\$');
    final pdf = pw.Document();

    pdf.addPage(
      pw.MultiPage(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.all(40),
        build: (context) => [
          pw.Column(
            crossAxisAlignment: pw.CrossAxisAlignment.start,
            children: [
              pw.Text('ZWESTA TRADING', style: pw.TextStyle(fontSize: 24, fontWeight: pw.FontWeight.bold)),
              pw.SizedBox(height: 4),
              pw.Text('Consolidated Reports', style: pw.TextStyle(fontSize: 16, fontWeight: pw.FontWeight.bold, color: PdfColors.blue)),
            ],
          ),
          pw.Divider(height: 30),
          ...reports.map((report) => _buildReportPage(report, currencyFormat, dateFormat, mode)).expand((w) => [w, pw.SizedBox(height: 24)]),
        ],
        footer: (context) => pw.Column(
          children: [
            pw.Divider(),
            pw.Row(
              mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
              children: [
                pw.Text('Zwesta Trading System', style: const pw.TextStyle(fontSize: 8)),
                pw.Text('Page ${context.pageNumber} of ${context.pagesCount}', style: const pw.TextStyle(fontSize: 8)),
              ],
            ),
          ],
        ),
      ),
    );

    return pdf;
  }

  static pw.Widget _buildReportPage(
    Map<String, dynamic> report,
    NumberFormat currencyFormat,
    DateFormat dateFormat,
    String mode,
  ) {
    final broker = (report['broker'] ?? 'Unknown').toString();
    final accountNumber = (report['accountNumber'] ?? 'N/A').toString();
    final currency = (report['currency'] ?? 'USD').toString();
    final balance = double.tryParse(report['balance']?.toString() ?? '0') ?? 0.0;
    final equity = double.tryParse(report['equity']?.toString() ?? '0') ?? 0.0;
    final profit = double.tryParse(report['netProfit']?.toString() ?? '0') ?? 0.0;
    final winRate = double.tryParse(report['winRate']?.toString() ?? '0') ?? 0.0;
    final totalTrades = int.tryParse(report['totalTrades']?.toString() ?? '0') ?? 0;

    return pw.Column(
      crossAxisAlignment: pw.CrossAxisAlignment.start,
      children: [
        pw.Text('$broker • $accountNumber', style: pw.TextStyle(fontSize: 16, fontWeight: pw.FontWeight.bold)),
        pw.SizedBox(height: 8),
        pw.Text('Mode: $mode  |  Generated: ${dateFormat.format(DateTime.now())}', style: pw.TextStyle(fontSize: 10, color: PdfColors.grey600)),
        pw.SizedBox(height: 16),
        pw.Table(
          border: pw.TableBorder.all(color: PdfColors.grey300, width: 0.5),
          children: [
            _pdfTableRow('Balance', currencyFormat.format(balance)),
            _pdfTableRow('Equity', currencyFormat.format(equity)),
            _pdfTableRow('Net Profit', currencyFormat.format(profit)),
            _pdfTableRow('Total Trades', '$totalTrades'),
            _pdfTableRow('Win Rate', '${winRate.toStringAsFixed(1)}%'),
          ],
        ),
      ],
    );
  }

  static Future<String?> savePdfToDirectoryGeneric(String directoryPath, String filename, pw.Document pdf) async {
    try {
      final dir = Directory(directoryPath);
      if (!await dir.exists()) {
        await dir.create(recursive: true);
      }
      final file = File('${dir.path}/$filename');
      final bytes = await pdf.save();
      await file.writeAsBytes(bytes, flush: true);
      return file.path;
    } catch (e) {
      return null;
    }
  }

  // Helper to save PDF to Downloads (Android). Returns saved path or null on failure.
  static Future<String?> savePdfToDownloads(String filename, pw.Document pdf) async {
    try {
      if (Platform.isAndroid) {
        final status = await Permission.storage.request();
        if (!status.isGranted) return null;
      }
      final dirs = await getExternalStorageDirectories(type: StorageDirectory.downloads);
      String dirPath;
      if (dirs != null && dirs.isNotEmpty) {
        dirPath = dirs.first.path;
      } else {
        final fallback = await getApplicationDocumentsDirectory();
        dirPath = fallback.path;
      }
      return await savePdfToDirectoryGeneric(dirPath, filename, pdf);
    } catch (e) {
      return null;
    }
  }

  // Share a generated PDF using share_plus. Writes a temporary file then shares it.
  static Future<void> sharePdf(pw.Document pdf, String filename) async {
    final tempDir = await getTemporaryDirectory();
    final file = File('${tempDir.path}/$filename');
    final bytes = await pdf.save();
    await file.writeAsBytes(bytes, flush: true);
    await Share.shareXFiles([XFile(file.path)], text: 'Zwesta Bot Report');
  }
}

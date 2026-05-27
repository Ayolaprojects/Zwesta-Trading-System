"""Generate PDF Trading Report"""
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib import colors
from datetime import datetime
import os

# Ensure output directory exists
OUTPUT_DIR = r"C:\Users\zwexm\LPSN\ZWESTA_TRADER"
os.makedirs(OUTPUT_DIR, exist_ok=True)

OUTPUT_FILE = os.path.join(OUTPUT_DIR, f"Zwesta_Trading_Assessment_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf")

# Create PDF
doc = SimpleDocTemplate(OUTPUT_FILE, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch)
story = []
styles = getSampleStyleSheet()

# Custom styles
title_style = ParagraphStyle(
    'CustomTitle',
    parent=styles['Heading1'],
    fontSize=24,
    textColor=colors.HexColor('#1a1a1a'),
    spaceAfter=30,
    alignment=TA_CENTER
)

heading_style = ParagraphStyle(
    'CustomHeading',
    parent=styles['Heading2'],
    fontSize=16,
    textColor=colors.HexColor('#2c3e50'),
    spaceAfter=12,
    spaceBefore=20
)

normal_style = ParagraphStyle(
    'CustomNormal',
    parent=styles['Normal'],
    fontSize=10,
    leading=14
)

# Title
story.append(Paragraph("ZWESTA TRADING SYSTEM", title_style))
story.append(Paragraph("Complete Live Trade Analysis & Development Assessment", styles['Heading3']))
story.append(Spacer(1, 0.3*inch))

# Date info
info_data = [
    ["Report Date:", datetime.now().strftime("%B %d, %Y %H:%M")],
    ["Trading Period:", "April 10 - May 27, 2026 (47 days)"],
    ["Account:", "Exness 295677214 (ZAR)"],
    ["Total Trades:", "560"],
]
info_table = Table(info_data, colWidths=[2*inch, 4*inch])
info_table.setStyle(TableStyle([
    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
    ('FONTSIZE', (0, 0), (-1, -1), 10),
    ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#555555')),
    ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
    ('ALIGN', (1, 0), (1, -1), 'LEFT'),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
]))
story.append(info_table)
story.append(Spacer(1, 0.3*inch))

# Executive Summary
story.append(Paragraph("EXECUTIVE SUMMARY", heading_style))
summary_data = [
    ["Total P&L:", "-1,908.63 ZAR", "❌ LOSS"],
    ["Win Rate:", "36.4% (204W / 347L)", "❌ Below Target (45%)"],
    ["Profit Factor:", "0.55", "❌ Critical (Need 1.0+)"],
    ["Expectancy:", "-3.60 ZAR/trade", "❌ Negative"],
    ["Account Drawdown:", "-58%", "❌ Catastrophic"],
]
summary_table = Table(summary_data, colWidths=[2*inch, 2.5*inch, 1.5*inch])
summary_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 10),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
    ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
]))
story.append(summary_table)
story.append(Spacer(1, 0.2*inch))

# Performance Metrics
story.append(Paragraph("PERFORMANCE METRICS", heading_style))
metrics_data = [
    ["Total Wins:", "204 trades", "2,319.07 ZAR"],
    ["Total Losses:", "347 trades", "-4,227.70 ZAR"],
    ["Average Win:", "11.37 ZAR", ""],
    ["Average Loss:", "-12.18 ZAR", ""],
    ["Largest Win:", "254.08 ZAR", ""],
    ["Largest Loss:", "-198.81 ZAR", ""],
    ["Risk/Reward:", "0.93", "Slightly Negative"],
]
metrics_table = Table(metrics_data, colWidths=[2*inch, 2*inch, 2*inch])
metrics_table.setStyle(TableStyle([
    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
    ('FONTSIZE', (0, 0), (-1, -1), 9),
    ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
    ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
]))
story.append(metrics_table)
story.append(Spacer(1, 0.2*inch))

# Symbol Performance
story.append(Paragraph("TOP 10 TRADED SYMBOLS", heading_style))
symbols_data = [
    ["Symbol", "Trades", "P&L (ZAR)", "Win Rate"],
    ["GBPUSDm ✅", "91", "+99.08", "42%"],
    ["BTCUSDm ❌", "108", "-589.16", "36%"],
    ["AUDUSDm", "79", "-150.14", "39%"],
    ["USDJPYm", "63", "-197.21", "37%"],
    ["ETHUSDm ❌", "45", "-331.44", "24%"],
    ["XAUUSDm", "31", "-227.23", "52%"],
    ["USDCADm", "22", "-59.88", "23%"],
    ["US30m", "18", "-13.73", "39%"],
    ["UKOILm", "18", "-255.26", "44%"],
    ["EURUSDm ❌", "15", "-144.36", "13%"],
]
symbols_table = Table(symbols_data, colWidths=[1.5*inch, 1*inch, 1.5*inch, 1*inch])
symbols_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 9),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ecf0f1')]),
]))
story.append(symbols_table)
story.append(Spacer(1, 0.2*inch))

# Close Reasons
story.append(Paragraph("EXIT ANALYSIS", heading_style))
exits_data = [
    ["Manual Exit (User):", "373 trades", "66.6%"],
    ["Stop Loss Hit:", "159 trades", "28.4%"],
    ["Take Profit Hit:", "28 trades", "5.0%"],
]
exits_table = Table(exits_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
exits_table.setStyle(TableStyle([
    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
    ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
]))
story.append(exits_table)
story.append(Spacer(1, 0.3*inch))

story.append(PageBreak())

# Development Journey
story.append(Paragraph("DEVELOPMENT FIXES DEPLOYED TODAY", heading_style))
story.append(Paragraph("All fixes committed to GitHub and deployed to production at 15:17 UTC", normal_style))
story.append(Spacer(1, 0.2*inch))

fixes_data = [
    ["Fix", "Before", "After", "Status"],
    ["Bot Creation Defaults", "signalThreshold: 0.5\nmaxPositions: 8", "signalThreshold: 65\nmaxPositions: 2", "✅ Commit ad27d8c4"],
    ["Recent-Profit Guard", "5% (blocking trades)", "30% (allows 6x risk)", "✅ Commit 447fecf6"],
    ["Setup Quality Gate", "7.0/10 (70% reject)", "5.5/10 (55% reject)", "✅ Commit d30da17c"],
    ["Database Schema", "Missing closed_at", "Added + populated", "✅ Fixed"],
    ["Database Performance", "60s timeout, locks", "120s timeout, WAL", "✅ Optimized"],
]
fixes_table = Table(fixes_data, colWidths=[1.8*inch, 1.5*inch, 1.5*inch, 1.2*inch])
fixes_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 8),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#e8f8f5')]),
]))
story.append(fixes_table)
story.append(Spacer(1, 0.3*inch))

# Critical Findings
story.append(Paragraph("CRITICAL FINDINGS", heading_style))
findings = [
    "<b>⚠️ Win Rate Crisis:</b> 36.4% is well below the 45% needed for profitability with current risk/reward ratio",
    "<b>⚠️ Crypto Bleeding:</b> BTC and ETH combined loss of -920 ZAR (48% of total losses)",
    "<b>⚠️ Stop Loss Epidemic:</b> 28.4% of trades hit SL vs only 5.0% hitting TP - stops too tight or entries too early",
    "<b>⚠️ Negative Expectancy:</b> System loses R3.60 per trade on average - fundamentally unprofitable",
    "<b>⚠️ Account Drawdown:</b> Lost 58% of account value in 47 days",
    "<b>✅ GBPUSDm Success:</b> Only profitable symbol (+99 ZAR, 42% win rate) - focus area identified",
]
for finding in findings:
    story.append(Paragraph(f"• {finding}", normal_style))
    story.append(Spacer(1, 0.1*inch))

story.append(Spacer(1, 0.2*inch))

# Recommendations
story.append(Paragraph("IMMEDIATE RECOMMENDATIONS", heading_style))
recommendations = [
    "<b>1. Monitor New Backend:</b> Verify 30% profit guard is active (check logs for '30.0% of last 4 closed trades')",
    "<b>2. Disable Crypto Symbols:</b> Remove BTCUSDm and ETHUSDm from active bots (-920 ZAR combined loss)",
    "<b>3. Focus on GBPUSDm:</b> Only profitable symbol - consider increasing allocation and studying success factors",
    "<b>4. Adjust Stop Losses:</b> Reduce SL hit rate from 28% to under 20% with wider stops or better entries",
    "<b>5. Improve Take Profits:</b> Increase TP hits from 5% to 15%+ with trailing stops or partial exits",
    "<b>6. Target Win Rate:</b> Need 45%+ win rate for profitability - more selective entries required",
    "<b>7. Consider Demo Mode:</b> Test strategy improvements before risking more live capital",
]
for rec in recommendations:
    story.append(Paragraph(rec, normal_style))
    story.append(Spacer(1, 0.12*inch))

story.append(Spacer(1, 0.3*inch))

# Final Assessment
story.append(Paragraph("FINAL ASSESSMENT", heading_style))
assessment_text = """
<b>System Status:</b> TECHNICALLY FIXED but FUNDAMENTALLY UNPROFITABLE<br/><br/>

<b>What Today's Fixes Solved:</b><br/>
✅ Backend blocking issues preventing trade execution<br/>
✅ Database errors and performance problems<br/>
✅ Future bot creation defaults (new bots will be safe)<br/>
✅ Trade execution capability restored<br/><br/>

<b>What Fixes DON'T Solve:</b><br/>
❌ Core trading strategy remains unprofitable (negative expectancy)<br/>
❌ Poor symbol selection (crypto losses dominate)<br/>
❌ Stop loss management issues (too many SL hits)<br/>
❌ Low win rate requires fundamental strategy improvements<br/><br/>

<b>Bottom Line:</b> The system infrastructure is now solid, but the trading strategy needs a complete overhaul. 
Today's technical fixes enable proper execution, but won't change the -58% account loss without addressing the 
core strategy problems: symbol selection, entry/exit timing, and risk management.
"""
story.append(Paragraph(assessment_text, normal_style))

# Build PDF
doc.build(story)

print(f"✅ PDF Report Generated Successfully!")
print(f"📄 Location: {OUTPUT_FILE}")
print(f"📊 File size: {os.path.getsize(OUTPUT_FILE) / 1024:.1f} KB")

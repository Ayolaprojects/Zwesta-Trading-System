#!/usr/bin/env python3

import argparse
import ast
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

BOT_ID = 'bot_1779229018996'
TARGET_SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT']
TARGET_MAX_OPEN_POSITIONS = len(TARGET_SYMBOLS)
TARGET_RUNTIME_UPDATES = {
    'managementMode': 'manual',
    'signalThresholdMode': 'manual',
    'managementProfile': 'small_account',
    'managementState': 'manual',
    'consecutiveLosses': 0,
    'signalThreshold': 24,
    'effectiveSignalThreshold': 24,
    'maxOpenPositions': TARGET_MAX_OPEN_POSITIONS,
    'effectiveMaxOpenPositions': TARGET_MAX_OPEN_POSITIONS,
    'maxPositionsPerSymbol': 1,
    'effectiveMaxPositionsPerSymbol': 1,
    'symbols': TARGET_SYMBOLS,
    'effectivePositionSizeMultiplier': 1.0,
    'effectiveScannerCapitalMultiplier': 1.0,
    'intelligentScanner': True,
    'allowedVolatility': ['Very Low', 'Low', 'Medium'],
    'effectiveAllowedVolatility': ['Very Low', 'Low', 'Medium'],
    'autoSwitch': False,
    'autoAdaptationEnabled': False,
    'allowAdaptiveRawFallback': False,
    'binanceFuturesAutoLeverage': True,
    'binanceFuturesBaseLeverage': 20,
    'binanceFuturesPeakLeverage': 20,
    'effectiveBinanceFuturesLeverage': 20,
    'binanceFuturesMarginType': 'ISOLATED',
}


def norm(value: str) -> str:
    return ''.join(ch for ch in str(value).lower() if ch.isalnum())


def parse_jsonish(value):
    if value is None:
        return {}
    if isinstance(value, dict):
        return dict(value)
    text = str(value).strip()
    if not text:
        return {}
    for parser in (json.loads, ast.literal_eval):
        try:
            parsed = parser(text)
        except Exception:
            continue
        if isinstance(parsed, dict):
            return dict(parsed)
    raise ValueError('runtime_state is not a JSON object')


def build_neutral_sizing_state(now_iso: str):
    return {
        'timestamp': now_iso,
        'state': 'manual',
        'multiplier': 1.0,
        'scannerCapitalMultiplier': 1.0,
        'reason': 'manual tuned override',
    }


def resolve_trade_amount(runtime_state: dict) -> float:
    for key in ('tradeAmount', 'effectiveTradeAmount'):
        try:
            value = float(runtime_state.get(key))
        except Exception:
            continue
        if value > 0:
            return value
    return 6.0


def build_trade_amount_adaptation(now_iso: str, trade_amount: float):
    return {
        'timestamp': now_iso,
        'state': 'manual',
        'multiplier': 1.0,
        'scannerCapitalMultiplier': 1.0,
        'baseTradeAmount': trade_amount,
        'adjustedTradeAmount': trade_amount,
        'dailyProfit': 0.0,
        'dailyProfitPeak': 0.0,
        'retraceRatio': 0.0,
        'reason': 'manual tuned override',
    }


def resolve_matching_row(cursor, bot_id: str):
    columns = [row[1] for row in cursor.execute('PRAGMA table_info([user_bots])').fetchall()]
    rows = cursor.execute('SELECT rowid AS __rowid__, * FROM [user_bots]').fetchall()
    id_like_columns = [col for col in columns if norm(col) in {'botid', 'bot', 'id', 'botname', 'name'}]

    matches = []
    for row in rows:
        row_dict = dict(row)
        hit_columns = [col for col in id_like_columns if row_dict.get(col) is not None and str(row_dict.get(col)) == bot_id]
        if hit_columns:
            matches.append((row_dict, hit_columns, columns))

    if len(matches) == 1:
        return matches[0]

    fallback_matches = []
    for row in rows:
        row_dict = dict(row)
        hit_columns = [col for col in columns if row_dict.get(col) is not None and str(row_dict.get(col)) == bot_id]
        if hit_columns:
            fallback_matches.append((row_dict, hit_columns, columns))

    if len(fallback_matches) != 1:
        raise SystemExit(f'Expected exactly 1 matching row for {bot_id}, found {len(fallback_matches)}')

    return fallback_matches[0]


def apply_update(db_path: Path, make_backup: bool):
    if not db_path.exists():
        raise SystemExit(f'Database not found: {db_path}')

    backup_path = None
    if make_backup:
        backup_path = db_path.with_name(f'{db_path.name}.{datetime.now().strftime("%Y%m%d_%H%M%S")}.bak')
        shutil.copy2(db_path, backup_path)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        integrity = [row[0] for row in cursor.execute('PRAGMA integrity_check').fetchall()]
        if integrity != ['ok']:
            raise SystemExit(f'Integrity check failed before update: {integrity}')

        row_dict, matched_on, columns = resolve_matching_row(cursor, BOT_ID)
        column_map = {norm(col): col for col in columns}
        runtime_col = column_map.get('runtimestate')
        symbols_col = column_map.get('symbols')
        if not runtime_col:
            raise SystemExit('runtime_state column not found in user_bots')

        runtime_state = parse_jsonish(row_dict.get(runtime_col))
        now_iso = datetime.now().isoformat()
        trade_amount = resolve_trade_amount(runtime_state)
        runtime_state.update(TARGET_RUNTIME_UPDATES)
        runtime_state['tradeAmount'] = trade_amount
        runtime_state['effectiveTradeAmount'] = trade_amount
        runtime_state['lastSizingAdjustment'] = build_neutral_sizing_state(now_iso)
        runtime_state['tradeAmountAdaptation'] = build_trade_amount_adaptation(now_iso, trade_amount)

        assignments = [f'[{runtime_col}] = ?']
        params = [json.dumps(runtime_state, ensure_ascii=True, separators=(',', ':'))]
        if symbols_col:
            assignments.append(f'[{symbols_col}] = ?')
            params.append(json.dumps(TARGET_SYMBOLS, ensure_ascii=True))
        params.append(row_dict['__rowid__'])

        cursor.execute(
            f'UPDATE [user_bots] SET {", ".join(assignments)} WHERE rowid = ?',
            params,
        )
        if cursor.rowcount != 1:
            raise SystemExit(f'Expected to update 1 row, updated {cursor.rowcount}')

        conn.commit()

        updated_row = cursor.execute(
            f'SELECT rowid AS __rowid__, * FROM [user_bots] WHERE rowid = ?',
            (row_dict['__rowid__'],),
        ).fetchone()
        updated_runtime_state = parse_jsonish(updated_row[runtime_col])
        result = {
            'database': str(db_path),
            'backup': str(backup_path) if backup_path else None,
            'bot': BOT_ID,
            'matched_on': matched_on,
            'runtime_state': {
                'managementMode': updated_runtime_state.get('managementMode'),
                'signalThresholdMode': updated_runtime_state.get('signalThresholdMode'),
                'managementProfile': updated_runtime_state.get('managementProfile'),
                'managementState': updated_runtime_state.get('managementState'),
                'consecutiveLosses': updated_runtime_state.get('consecutiveLosses'),
                'signalThreshold': updated_runtime_state.get('signalThreshold'),
                'effectiveSignalThreshold': updated_runtime_state.get('effectiveSignalThreshold'),
                'allowedVolatility': updated_runtime_state.get('allowedVolatility'),
                'effectiveAllowedVolatility': updated_runtime_state.get('effectiveAllowedVolatility'),
                'maxOpenPositions': updated_runtime_state.get('maxOpenPositions'),
                'effectiveMaxOpenPositions': updated_runtime_state.get('effectiveMaxOpenPositions'),
                'maxPositionsPerSymbol': updated_runtime_state.get('maxPositionsPerSymbol'),
                'effectiveMaxPositionsPerSymbol': updated_runtime_state.get('effectiveMaxPositionsPerSymbol'),
                'symbols': updated_runtime_state.get('symbols'),
                'tradeAmount': updated_runtime_state.get('tradeAmount'),
                'effectiveTradeAmount': updated_runtime_state.get('effectiveTradeAmount'),
                'binanceFuturesAutoLeverage': updated_runtime_state.get('binanceFuturesAutoLeverage'),
                'binanceFuturesBaseLeverage': updated_runtime_state.get('binanceFuturesBaseLeverage'),
                'binanceFuturesPeakLeverage': updated_runtime_state.get('binanceFuturesPeakLeverage'),
                'effectiveBinanceFuturesLeverage': updated_runtime_state.get('effectiveBinanceFuturesLeverage'),
                'binanceFuturesMarginType': updated_runtime_state.get('binanceFuturesMarginType'),
                'effectivePositionSizeMultiplier': updated_runtime_state.get('effectivePositionSizeMultiplier'),
                'effectiveScannerCapitalMultiplier': updated_runtime_state.get('effectiveScannerCapitalMultiplier'),
                'intelligentScanner': updated_runtime_state.get('intelligentScanner'),
                'lastSizingAdjustment': updated_runtime_state.get('lastSizingAdjustment'),
                'tradeAmountAdaptation': updated_runtime_state.get('tradeAmountAdaptation'),
            },
            'symbols_column': updated_row[symbols_col] if symbols_col else None,
        }
        print(json.dumps(result, ensure_ascii=True, indent=2))
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description='Apply tuned Binance runtime_state for bot_1779229018996 to a SQLite DB.')
    parser.add_argument(
        '--db',
        default=r'C:\backend\zwesta_trading.db',
        help='Path to the SQLite database to patch. Default: C:\\backend\\zwesta_trading.db',
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Skip creating a timestamped backup before updating the database.',
    )
    args = parser.parse_args()
    apply_update(Path(args.db), make_backup=not args.no_backup)


if __name__ == '__main__':
    main()
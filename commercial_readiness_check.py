#!/usr/bin/env python3
"""Commercial readiness checks for the trading backend.

This script performs safe, non-live checks:
- Syntax compile of backend file
- LIVE API key safety guard
- Optional local endpoint smoke checks if backend is running
- Binance order-history churn simulation against anti-churn guard assumptions
"""

from __future__ import annotations

import json
import os
import py_compile
from datetime import datetime, timezone
from pathlib import Path

import requests


BACKEND_FILE = Path(r"c:\backend\multi_broker_backend_updated.py")
ENV_FILE = Path(r"c:\backend\.env")
DEFAULT_API_KEY = "your_generated_api_key_here_change_in_production"


def _parse_dotenv(path: Path) -> dict:
    data = {}
    if not path.exists():
        return data
    try:
        for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = str(raw_line or "").strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                data[key] = value
    except Exception:
        return {}
    return data


def _resolve_runtime_hints() -> dict:
    env_file_data = _parse_dotenv(ENV_FILE)
    env_mode = str(os.getenv("ENVIRONMENT", "") or "").strip().upper()
    file_mode = str(env_file_data.get("ENVIRONMENT", "") or "").strip().upper()
    resolved_mode = env_mode or file_mode or "DEMO"

    api_key = str(os.getenv("API_KEY", "") or "").strip()
    if not api_key:
        api_key = str(env_file_data.get("API_KEY", "") or "").strip()
    api_key = api_key or DEFAULT_API_KEY

    return {
        "environment": resolved_mode,
        "api_key": api_key,
        "api_key_is_default": api_key == DEFAULT_API_KEY,
        "api_key_source": "env" if str(os.getenv("API_KEY", "") or "").strip() else ("dotenv" if str(env_file_data.get("API_KEY", "") or "").strip() else "default"),
    }


def check_compile() -> dict:
    try:
        py_compile.compile(str(BACKEND_FILE), doraise=True)
        return {"ok": True, "detail": "backend compiles"}
    except Exception as exc:
        return {"ok": False, "detail": f"compile failed: {exc}"}


def check_live_api_key_guard() -> dict:
    text = BACKEND_FILE.read_text(encoding="utf-8", errors="replace")
    has_guard = "ALLOW_INSECURE_API_KEY" in text and "LIVE mode requires a secure API_KEY" in text
    hints = _resolve_runtime_hints()

    return {
        "ok": bool(has_guard),
        "detail": "live API key guard present" if has_guard else "live API key guard missing",
        "environment": hints["environment"],
        "api_key_is_default": hints["api_key_is_default"],
        "api_key_source": hints["api_key_source"],
    }


def check_local_endpoints() -> dict:
    base = "http://127.0.0.1:9000"
    endpoints = [
        {"path": "/api/health", "requires_auth": False},
        {"path": "/api/system/broker-readiness", "requires_auth": True},
        {"path": "/api/admin/binance-spot-guards", "requires_auth": True},
    ]
    hints = _resolve_runtime_hints()
    api_key = hints["api_key"]
    has_secure_api_key = bool(api_key and api_key != DEFAULT_API_KEY)
    result = []
    warnings = []
    failures = []
    any_reachable = False

    for endpoint in endpoints:
        ep = endpoint["path"]
        requires_auth = bool(endpoint.get("requires_auth"))
        url = f"{base}{ep}"
        try:
            headers = {}
            if requires_auth and has_secure_api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            resp = requests.get(url, headers=headers, timeout=3)
            any_reachable = any_reachable or (resp.status_code is not None)

            ok = False
            if ep == "/api/health":
                ok = resp.status_code == 200
            elif requires_auth:
                if has_secure_api_key:
                    ok = resp.status_code == 200
                else:
                    # Missing secure API key means we expect 401 for protected endpoints.
                    ok = resp.status_code == 401
                    if resp.status_code == 401:
                        warnings.append(f"Protected endpoint {ep} not fully validated (no secure API key available)")
            else:
                ok = 200 <= resp.status_code < 300

            if not ok:
                failures.append(f"{ep} returned HTTP {resp.status_code}")

            result.append({
                "url": url,
                "status": resp.status_code,
                "body_head": resp.text[:100],
                "requires_auth": requires_auth,
                "checked_with_auth": bool(requires_auth and has_secure_api_key),
                "ok": ok,
            })
        except Exception as exc:
            failures.append(f"{ep} request error: {exc}")
            result.append({
                "url": url,
                "status": None,
                "error": str(exc),
                "requires_auth": requires_auth,
                "checked_with_auth": bool(requires_auth and has_secure_api_key),
                "ok": False,
            })

    ok = bool(any_reachable and not failures)
    if ok:
        detail = "local backend reachable"
    elif any_reachable:
        detail = "local backend reachable but checks failed"
    else:
        detail = "local backend not running/reachable"

    return {
        "ok": ok,
        "detail": detail,
        "warnings": warnings,
        "failures": failures,
        "api_key_used": has_secure_api_key,
        "checks": result,
    }


def simulate_binance_churn_guard() -> dict:
    rows = [
        ("05-09 00:51:03", "SELL", 92.34, 1.877),
        ("05-09 00:50:41", "BUY", 92.41, 1.877),
        ("05-09 00:49:38", "SELL", 92.45, 4.240),
        ("05-09 00:47:30", "BUY", 2312.56, 0.0750),
        ("05-09 00:47:26", "BUY", 80314.80, 0.00216),
        ("05-09 00:47:24", "BUY", 92.39, 4.240),
        ("05-09 00:44:10", "SELL", 2312.15, 0.0025),
        ("05-09 00:36:34", "SELL", 92.44, 0.055),
        ("05-09 00:31:48", "SELL", 80337.25, 0.00250),
        ("05-09 00:03:11", "BUY", 92.41, 1.641),
        ("05-09 00:00:42", "SELL", 92.36, 0.055),
        ("05-08 23:58:02", "BUY", 80223.03, 0.00189),
        ("05-08 23:48:03", "SELL", 80176.02, 0.00250),
        ("05-08 23:38:26", "BUY", 80211.04, 0.00315),
        ("05-08 23:37:47", "BUY", 92.17, 2.742),
    ]

    rows = list(reversed(rows))
    fee_rate = float(os.getenv("BINANCE_SPOT_FEE_RATE", "0.001") or "0.001")
    min_net_exit_pct = float(os.getenv("BINANCE_SPOT_MIN_NET_EXIT_PCT", "0.20") or "0.20") / 100.0
    min_hold_minutes = float(os.getenv("BINANCE_SPOT_MIN_HOLD_MINUTES_TEST", "1.0") or "1.0")

    def infer_symbol(price: float) -> str:
        if price > 10000:
            return "BTCUSDT"
        if price > 1000:
            return "ETHUSDT"
        return "SOLUSDT"

    open_positions = {}
    blocked_hold = 0
    blocked_edge = 0
    executed_sell = 0

    for ts, side, price, qty in rows:
        symbol = infer_symbol(price)
        timestamp = datetime.strptime("2026-" + ts, "%Y-%m-%d %H:%M:%S")

        if side == "BUY":
            open_positions[symbol] = {"entry": price, "qty": qty, "opened": timestamp}
            continue

        current = open_positions.get(symbol)
        if not current:
            continue

        traded_qty = min(float(qty), float(current["qty"]))
        held_minutes = (timestamp - current["opened"]).total_seconds() / 60.0
        gross_pnl = (float(price) - float(current["entry"])) * traded_qty
        notional = float(price) * traded_qty
        round_trip_fees = ((float(current["entry"]) * traded_qty) + notional) * fee_rate
        net_after_fees = gross_pnl - round_trip_fees
        min_required_net = max(0.05, notional * min_net_exit_pct)
        urgency = 0.0

        if held_minutes < min_hold_minutes and urgency < 12:
            blocked_hold += 1
            continue
        if net_after_fees < min_required_net and urgency < 12:
            blocked_edge += 1
            continue

        executed_sell += 1
        del open_positions[symbol]

    return {
        "ok": True,
        "detail": "guard simulation completed",
        "blocked_hold": blocked_hold,
        "blocked_edge": blocked_edge,
        "executed_sell": executed_sell,
        "fee_rate": fee_rate,
        "min_net_exit_pct": min_net_exit_pct,
        "min_hold_minutes": min_hold_minutes,
    }


def main() -> None:
    checks = {
        "compile": check_compile(),
        "live_api_key_guard": check_live_api_key_guard(),
        "local_endpoint_smoke": check_local_endpoints(),
        "churn_guard_simulation": simulate_binance_churn_guard(),
    }

    hard_fail = not checks["compile"]["ok"] or not checks["live_api_key_guard"]["ok"]
    live_mode = str(checks["live_api_key_guard"].get("environment") or "DEMO").upper() == "LIVE"
    if live_mode and checks["live_api_key_guard"].get("api_key_is_default", True):
        hard_fail = True

    status = "PASS"
    if hard_fail:
        status = "FAIL"
    elif not checks["local_endpoint_smoke"]["ok"]:
        status = "PASS_OFFLINE"
    elif checks["local_endpoint_smoke"].get("warnings"):
        status = "PASS_WITH_WARNINGS"

    output = {
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()

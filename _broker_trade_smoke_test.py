import json
import os
import sqlite3
import sys
from datetime import datetime

sys.path.insert(0, r"c:\backend")
import multi_broker_backend_updated as backend

DB_PATH = r"c:\backend\zwesta_trading.db"
BINANCE_CRED_ID = "e568ec38-cfc7-4b05-8033-b56ecdf304e4"
EXNESS_CRED_ID = "66838627-f045-489d-85d6-a81e829d4228"


def load_credential(credential_id: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM broker_credentials WHERE credential_id = ?", (credential_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise RuntimeError(f"Credential not found: {credential_id}")
    return backend.decrypt_credential_row(dict(row))


def _get_bool_env(name: str, default: bool = False) -> bool:
    raw_value = str(os.getenv(name, str(default)) or str(default)).strip().lower()
    return raw_value in {"1", "true", "yes", "on"}


def load_binance_trade_credentials() -> dict:
    market = str(os.getenv("BINANCE_MARKET", "futures") or "futures").strip().lower()
    if market not in {"spot", "futures"}:
        market = "futures"

    market_prefix = "BINANCE_FUTURES" if market == "futures" else "BINANCE_SPOT"
    api_key = str(
        os.getenv(f"{market_prefix}_API_KEY")
        or os.getenv("BINANCE_API_KEY")
        or ""
    ).strip()
    api_secret = str(
        os.getenv(f"{market_prefix}_API_SECRET")
        or os.getenv("BINANCE_API_SECRET")
        or ""
    ).strip()
    is_live = _get_bool_env("BINANCE_IS_LIVE", False)

    if api_key and api_secret:
        return {
            "source": "environment",
            "credential_id": None,
            "account_number": str(os.getenv("BINANCE_ACCOUNT_NUMBER", "") or "").strip() or market.upper(),
            "server": market,
            "market": market,
            "is_live": is_live,
            "api_key": api_key,
            "password": api_secret,
        }

    credential_id = str(os.getenv("BINANCE_CREDENTIAL_ID", BINANCE_CRED_ID) or BINANCE_CRED_ID).strip()
    credential = load_credential(credential_id)
    credential["source"] = "database"
    credential["credential_id"] = credential_id
    return credential


def test_binance() -> dict:
    cred = load_binance_trade_credentials()
    result = {
        "broker": "Binance",
        "credential_id": cred.get("credential_id"),
        "credential_source": cred.get("source") or "database",
        "account_number": cred.get("account_number"),
        "server": cred.get("server") or cred.get("market"),
        "is_live": bool(cred.get("is_live")),
        "started_at": datetime.now().isoformat(),
    }
    if result["is_live"] and not _get_bool_env("BINANCE_ALLOW_LIVE_TRADE_SMOKE", False):
        result["exception"] = "Refusing live Binance credential without BINANCE_ALLOW_LIVE_TRADE_SMOKE=true"
        return result

    conn = backend.BinanceConnection({
        "api_key": cred.get("api_key"),
        "api_secret": cred.get("password"),
        "account_number": cred.get("account_number"),
        "server": cred.get("server") or cred.get("market") or "spot",
        "market": cred.get("market") or cred.get("server") or "spot",
        "is_live": bool(cred.get("is_live")),
        "prefetch_account_info": False,
        "auth_timeout": 8,
        "account_info_timeout": 10,
        "time_sync_timeout": 5,
    })
    try:
        print("BINANCE step=connect:start", flush=True)
        result["connect_ok"] = conn.connect()
        print(f"BINANCE step=connect:done ok={result['connect_ok']} error={conn.last_error!r}", flush=True)
        result["connect_error"] = conn.last_error
        result["connect_error_code"] = getattr(conn, "last_error_code", None)
        if not result["connect_ok"]:
            return result

        print("BINANCE step=buy:start", flush=True)
        buy = conn.place_order("BTCUSDT", "BUY", 0.0, quote_amount=12.0)
        print(f"BINANCE step=buy:done {buy}", flush=True)
        result["buy"] = buy
        if not buy.get("success"):
            return result

        print("BINANCE step=close:start", flush=True)
        sell_qty = float(buy.get("executedQty") or 0.0)
        result["sell_quantity"] = sell_qty
        if sell_qty <= 0:
            result["close"] = {"success": False, "error": "Buy succeeded but executedQty was zero"}
        else:
            quantity_value = format(sell_qty, ".8f").rstrip("0").rstrip(".")
            sell_resp = conn._request_with_time_retry(
                "POST",
                f"{conn.base_url}/v3/order",
                headers=conn._headers(),
                params={
                    "symbol": "BTCUSDT",
                    "side": "SELL",
                    "type": "MARKET",
                    "quantity": quantity_value,
                },
                timeout=15,
            )
            result["close"] = (
                {"success": True, "status_code": sell_resp.status_code, "body": sell_resp.json() if sell_resp.content else {}}
                if sell_resp.status_code == 200
                else {"success": False, "status_code": sell_resp.status_code, "body": sell_resp.text}
            )
        print(f"BINANCE step=close:done {result['close']}", flush=True)
        return result
    finally:
        try:
            conn.disconnect()
        except Exception:
            pass


def test_exness() -> dict:
    cred = load_credential(EXNESS_CRED_ID)
    result = {
        "broker": "Exness",
        "credential_id": EXNESS_CRED_ID,
        "account_number": cred.get("account_number"),
        "server": cred.get("server"),
        "is_live": bool(cred.get("is_live")),
        "started_at": datetime.now().isoformat(),
    }
    if result["is_live"]:
        result["exception"] = "Refusing live Exness credential"
        return result

    conn = backend.MT5Connection({
        "broker_name": cred.get("broker_name") or "Exness",
        "broker": cred.get("broker_name") or "Exness",
        "account_number": cred.get("account_number"),
        "account": cred.get("account_number"),
        "password": cred.get("password"),
        "server": cred.get("server"),
        "is_live": False,
        "is_manual_test": True,
        "lock_timeout": 8,
    })
    try:
        print("EXNESS step=connect:start", flush=True)
        result["connect_ok"] = conn.connect()
        print(f"EXNESS step=connect:done ok={result['connect_ok']} error={conn.last_error!r}", flush=True)
        result["connect_error"] = conn.last_error
        result["connect_error_code"] = getattr(conn, "last_error_code", None)
        if not result["connect_ok"]:
            return result

        print("EXNESS step=account:start", flush=True)
        account_info = conn.get_account_info() or {}
        print(f"EXNESS step=account:done balance={account_info.get('balance')} currency={account_info.get('currency')}", flush=True)
        result["balance"] = account_info.get("balance")
        result["currency"] = account_info.get("currency")

        print("EXNESS step=buy:start", flush=True)
        buy = conn.place_order("EURUSDm", "BUY", 0.01, comment="CopilotTest")
        print(f"EXNESS step=buy:done {buy}", flush=True)
        result["buy"] = buy
        if not buy.get("success"):
            return result

        order_id = buy.get("orderId")
        result["order_id"] = order_id
        print("EXNESS step=close:start", flush=True)
        result["close"] = (
            conn.close_position(str(order_id))
            if order_id
            else {"success": False, "error": "No orderId returned"}
        )
        print(f"EXNESS step=close:done {result['close']}", flush=True)
        return result
    finally:
        try:
            conn.disconnect()
        except Exception:
            pass


def main() -> int:
    target = str(sys.argv[1] if len(sys.argv) > 1 else "both").strip().lower()
    summary = {"completed_at": datetime.now().isoformat()}
    if target in {"both", "binance"}:
        summary["binance"] = test_binance()
    if target in {"both", "exness"}:
        summary["exness"] = test_exness()
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

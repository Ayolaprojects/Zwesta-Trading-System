import hashlib
import hmac
import json
import os
import time
from datetime import datetime
from urllib.parse import urlencode

import requests


def _get_bool_env(name: str, default: bool = False) -> bool:
    raw_value = str(os.getenv(name, str(default)) or str(default)).strip().lower()
    return raw_value in {"1", "true", "yes", "on"}


def _resolve_credentials() -> dict:
    return {
        "api_key": str(
            os.getenv("BINANCE_FUTURES_API_KEY")
            or os.getenv("BINANCE_API_KEY")
            or ""
        ).strip(),
        "api_secret": str(
            os.getenv("BINANCE_FUTURES_API_SECRET")
            or os.getenv("BINANCE_API_SECRET")
            or ""
        ).strip(),
        "is_live": _get_bool_env("BINANCE_IS_LIVE", True),
    }


def _endpoint_candidates(is_live: bool) -> list[str]:
    if is_live:
        return ["https://fapi.binance.com/fapi"]
    return [
        "https://demo-fapi.binance.com/fapi",
        "https://testnet.binancefuture.com/fapi",
    ]


def _signed_get(base_url: str, api_key: str, api_secret: str, endpoint: str) -> tuple[requests.Response | None, str | None]:
    try:
        time_response = requests.get(f"{base_url}/v1/time", timeout=10)
        if time_response.status_code != 200:
            return None, f"Time sync failed with HTTP {time_response.status_code}"

        payload = time_response.json() if time_response.content else {}
        server_time = int(payload.get("serverTime", 0) or 0)
        if server_time <= 0:
            return None, "Time sync returned no serverTime"

        params = {
            "recvWindow": 60000,
            "timestamp": server_time,
        }
        query_string = urlencode(params)
        signature = hmac.new(
            api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature

        response = requests.get(
            f"{base_url}{endpoint}",
            headers={"X-MBX-APIKEY": api_key},
            params=params,
            timeout=15,
        )
        return response, None
    except Exception as exc:
        return None, str(exc)


def main() -> int:
    credentials = _resolve_credentials()
    result = {
        "broker": "Binance",
        "market": "futures",
        "configured_mode": "live" if credentials["is_live"] else "demo",
        "started_at": datetime.now().isoformat(),
        "success": False,
        "attempts": [],
    }

    if not credentials["api_key"] or not credentials["api_secret"]:
        result["error"] = "Missing Binance futures API credentials in environment variables."
        result["expected"] = [
            "BINANCE_FUTURES_API_KEY",
            "BINANCE_FUTURES_API_SECRET",
            "BINANCE_API_KEY",
            "BINANCE_API_SECRET",
        ]
        print(json.dumps(result, indent=2))
        return 1

    for base_url in _endpoint_candidates(credentials["is_live"]):
        response, request_error = _signed_get(base_url, credentials["api_key"], credentials["api_secret"], "/v2/account")
        if request_error:
            result["attempts"].append({"endpoint": f"{base_url}/v2/account", "error": request_error})
            continue

        payload = {}
        try:
            payload = response.json() if response.content else {}
        except Exception:
            payload = {}

        result["attempts"].append(
            {
                "endpoint": f"{base_url}/v2/account",
                "status_code": response.status_code,
                "code": payload.get("code") if isinstance(payload, dict) else None,
                "message": payload.get("msg") if isinstance(payload, dict) else None,
            }
        )

        if response.status_code == 200:
            result["success"] = True
            result["account_endpoint"] = f"{base_url}/v2/account"
            result["effective_mode"] = "live" if credentials["is_live"] else "demo"
            result["wallet_balance"] = payload.get("totalWalletBalance")
            result["available_balance"] = payload.get("availableBalance")
            result["can_trade"] = payload.get("canTrade")
            break

        result["error"] = str(payload.get("msg") or f"Binance auth failed with HTTP {response.status_code}")
        result["error_code"] = payload.get("code") if isinstance(payload, dict) else None

    print(json.dumps(result, indent=2, default=str))
    return 0 if result["success"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
#!/usr/bin/env python3
"""
Read-only Binance credential validator.

Uses environment variables and the actual Zwesta BinanceConnection path so you
can verify futures or spot credentials without placing any trades.

Supported env vars:
  BINANCE_MARKET=futures|spot          default: futures
  BINANCE_IS_LIVE=true|false           default: true
  BINANCE_ACCOUNT_NUMBER=optional

Credential precedence:
  1. BINANCE_FUTURES_API_KEY / BINANCE_FUTURES_API_SECRET for futures
  2. BINANCE_SPOT_API_KEY / BINANCE_SPOT_API_SECRET for spot
  3. BINANCE_API_KEY / BINANCE_API_SECRET as shared fallback
"""

import hashlib
import hmac
import json
import os
import time
from urllib.parse import urlencode

import requests


def _get_bool_env(name: str, default: bool) -> bool:
    raw_value = str(os.getenv(name, str(default)) or str(default)).strip().lower()
    return raw_value in {"1", "true", "yes", "on"}


def _resolve_credentials() -> dict:
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

    return {
        "market": market,
        "is_live": _get_bool_env("BINANCE_IS_LIVE", True),
        "account_number": str(os.getenv("BINANCE_ACCOUNT_NUMBER", "") or "").strip(),
        "api_key": api_key,
        "api_secret": api_secret,
    }


def _resolve_endpoint_candidates(market: str, is_live: bool) -> list[tuple[str, str]]:
    if market == "futures":
        if is_live:
            return [("https://fapi.binance.com/fapi", "/v2/account")]
        return [
            ("https://demo-fapi.binance.com/fapi", "/v2/account"),
            ("https://testnet.binancefuture.com/fapi", "/v2/account"),
        ]

    if is_live:
        return [("https://api.binance.com/api", "/v3/account")]
    return [
        ("https://demo-api.binance.com/api", "/v3/account"),
        ("https://testnet.binance.vision/api", "/v3/account"),
    ]


def _signed_get(base_url: str, market: str, endpoint: str, api_key: str, api_secret: str) -> tuple[requests.Response | None, str | None]:
    time_endpoint = "/v1/time" if market == "futures" else "/v3/time"
    try:
        time_response = requests.get(f"{base_url}{time_endpoint}", timeout=10)
        if time_response.status_code != 200:
            return None, f"Time sync failed with HTTP {time_response.status_code}"
        time_payload = time_response.json() if time_response.content else {}
        server_time = int(time_payload.get("serverTime", 0) or 0)
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


def validate_binance_credentials() -> int:
    credentials = _resolve_credentials()
    market = credentials["market"]

    if not credentials["api_key"] or not credentials["api_secret"]:
        expected_prefix = "BINANCE_FUTURES" if market == "futures" else "BINANCE_SPOT"
        print(
            json.dumps(
                {
                    "success": False,
                    "error": "Missing Binance API credentials in environment variables.",
                    "market": market,
                    "expected": [
                        f"{expected_prefix}_API_KEY",
                        f"{expected_prefix}_API_SECRET",
                        "BINANCE_API_KEY",
                        "BINANCE_API_SECRET",
                    ],
                },
                indent=2,
            )
        )
        return 1

    result = {
        "market": market,
        "configured_mode": "live" if credentials["is_live"] else "demo",
        "success": False,
        "connect_error": None,
        "connect_error_code": None,
        "attempts": [],
    }

    for base_url, endpoint in _resolve_endpoint_candidates(market, credentials["is_live"]):
        response, request_error = _signed_get(
            base_url,
            market,
            endpoint,
            credentials["api_key"],
            credentials["api_secret"],
        )
        if request_error:
            result["attempts"].append({"endpoint": f"{base_url}{endpoint}", "error": request_error})
            continue

        payload = {}
        try:
            payload = response.json() if response is not None and response.content else {}
        except Exception:
            payload = {}

        result["attempts"].append(
            {
                "endpoint": f"{base_url}{endpoint}",
                "status_code": response.status_code,
                "code": payload.get("code") if isinstance(payload, dict) else None,
                "message": payload.get("msg") if isinstance(payload, dict) else None,
            }
        )

        if response.status_code == 200:
            result["success"] = True
            result["effective_mode"] = "live" if "binance.com" in base_url and "demo-" not in base_url and "testnet" not in base_url else "demo"
            result["account_endpoint"] = f"{base_url}{endpoint}"
            if market == "futures":
                result["wallet_balance"] = payload.get("totalWalletBalance")
                result["available_balance"] = payload.get("availableBalance")
                result["can_trade"] = payload.get("canTrade")
            else:
                balances = payload.get("balances") or []
                usdt_balance = next((entry for entry in balances if str(entry.get("asset") or "").upper() == "USDT"), {})
                result["wallet_value"] = usdt_balance.get("free")
                result["liquid_stablecoin_value"] = usdt_balance.get("free")
                result["can_trade"] = payload.get("canTrade")
            break

        if isinstance(payload, dict):
            result["connect_error"] = str(payload.get("msg") or "Binance authentication failed")
            result["connect_error_code"] = payload.get("code")
        else:
            result["connect_error"] = f"Binance authentication failed with HTTP {response.status_code}"
            result["connect_error_code"] = None

    print(json.dumps(result, indent=2, default=str))
    return 0 if result["success"] else 2


if __name__ == "__main__":
    raise SystemExit(validate_binance_credentials())
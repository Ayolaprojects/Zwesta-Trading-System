import requests, json

BASE = "http://148.113.5.39:9000"
ADMIN = {"Authorization": "Bearer zwesta_live_api_key_2026_secure"}

r = requests.post(BASE + "/api/user/login",
                  json={"email": "zwexman@gmail.com", "password": "Zwesta1985"},
                  timeout=15)
token = r.json()["session_token"]
SH = {"X-Session-Token": token}

BOT_IDS = ["bot_1779185407301", "bot_1779197221415", "bot_1779201336253", "AZE BOT"]

for bot_id in BOT_IDS:
    safe_id = requests.utils.quote(bot_id)
    r = requests.get(BASE + "/api/bot/config/" + safe_id, headers=SH, timeout=15)
    if not r.ok:
        print(bot_id + ": GET failed " + str(r.status_code))
        continue

    cfg = r.json().get("config", {})
    broker = cfg.get("brokerName", "")
    effective_ta = cfg.get("effectiveTradeAmount")
    pp = cfg.get("profitProtection") or {}
    if isinstance(pp, str):
        pp = json.loads(pp)

    current_mh = pp.get("minimumHoldMinutes")
    print("\n" + bot_id + " (" + broker + "): effectiveTA=" + str(effective_ta) + ", minHold=" + str(current_mh))

    patch_payload = {}
    pp["minimumHoldMinutes"] = 20.0
    patch_payload["profitProtection"] = pp

    if bot_id == "AZE BOT":
        trade_amount = float(cfg.get("tradeAmount") or 7.02)
        patch_payload["tradeAmountAdaptation"] = {
            "state": "normal",
            "multiplier": 1.0,
            "reason": "manual_reset_futures_fix",
            "baseTradeAmount": trade_amount,
        }
        patch_payload["effectiveTradeAmount"] = trade_amount
        print("  -> Resetting AZE BOT adaptation to normal/1.0, effectiveTA=" + str(trade_amount))

    patch = requests.patch(
        BASE + "/api/admin/bot/" + requests.utils.quote(bot_id) + "/config",
        headers=ADMIN,
        json=patch_payload,
        timeout=15,
    )
    if patch.ok:
        result = patch.json()
        print("  PATCHED OK: " + str(result.get("message", ""))[:80])
    else:
        print("  FAILED " + str(patch.status_code) + ": " + patch.text[:200])

print("\nDone. Run _status_all.py to verify.")

import datetime
import json
import sqlite3

DB_PATH = r"C:\backend\zwesta_trading.db"
ACCOUNT_NUMBER = "8e0swgyYlgXkoPKGFiWwZwxlihG6u5ajA3V0g7XIEYm3RH1VATsTNv7uI821EBif"
BROKER_ACCOUNT_ID = f"Binance_{ACCOUNT_NUMBER}"


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    now = datetime.datetime.now(datetime.UTC).isoformat()

    cur.execute(
        """
        SELECT credential_id
        FROM broker_credentials
        WHERE broker_name='Binance' AND account_number=?
        """,
        (ACCOUNT_NUMBER,),
    )
    cred_row = cur.fetchone()
    if not cred_row:
        raise RuntimeError("Binance credential not found")

    credential_id = cred_row[0]
    cur.execute(
        "UPDATE broker_credentials SET is_live=1, updated_at=? WHERE credential_id=?",
        (now, credential_id),
    )

    cur.execute(
        "SELECT bot_id, runtime_state FROM user_bots WHERE enabled=1 AND broker_account_id=?",
        (BROKER_ACCOUNT_ID,),
    )
    bots = cur.fetchall()

    updated = 0
    for bot_id, runtime_state in bots:
        try:
            state = json.loads(runtime_state) if runtime_state else {}
        except json.JSONDecodeError:
            state = {}

        state["brokerName"] = "Binance"
        state["broker"] = "Binance"
        state["is_live"] = True

        cur.execute(
            "UPDATE user_bots SET is_live=1, runtime_state=?, updated_at=? WHERE bot_id=?",
            (json.dumps(state), now, bot_id),
        )
        updated += 1

    conn.commit()
    conn.close()

    print(f"Credential set to live: {credential_id}")
    print(f"Bots updated to live: {updated}")


if __name__ == "__main__":
    main()

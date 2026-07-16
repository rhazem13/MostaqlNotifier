import os

import requests

TELEGRAM_TOKEN = (os.environ.get("TELEGRAM_TOKEN") or "").strip()
CHAT_IDS = {"Hazem": "765118363"}
MESSAGE = "Hello world"


def call_telegram(endpoint, method="get", **kwargs):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/{endpoint}"
    if method == "post":
        return requests.post(url, timeout=10, **kwargs)
    return requests.get(url, timeout=10, **kwargs)


def main():
    if not TELEGRAM_TOKEN:
        print("TELEGRAM_TOKEN is missing")
        return

    try:
        me_response = call_telegram("getMe")
        print(f"Bot check: {me_response.status_code} {me_response.text}")
    except Exception as exc:
        print(f"Bot check failed: {exc}")
        return

    success_count = 0

    for name, chat_id in CHAT_IDS.items():
        try:
            chat_response = call_telegram("getChat", params={"chat_id": chat_id})
            if chat_response.status_code != 200:
                print(
                    f"Cannot access {name} ({chat_id}): {chat_response.status_code} {chat_response.text}"
                )
                continue

            payload = {"chat_id": chat_id, "text": MESSAGE}
            response = call_telegram("sendMessage", method="post", json=payload)
            if response.status_code == 200:
                print(f"Sent to {name} ({chat_id})")
                success_count += 1
            else:
                print(f"Failed for {name} ({chat_id}): {response.status_code} {response.text}")
        except Exception as exc:
            print(f"Error for {name} ({chat_id}): {exc}")

    print(f"Done. Success: {success_count}/{len(CHAT_IDS)}")


if __name__ == "__main__":
    main()

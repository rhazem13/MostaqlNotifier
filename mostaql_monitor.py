import os
import requests
import sys

def read_env_any(*keys):
    for key in keys:
        value = (os.environ.get(key) or "").strip()
        if value:
            return value
    return ""


# 1. Load Secrets
TELEGRAM_TOKEN = (os.environ.get("TELEGRAM_TOKEN") or "").strip()
# Always send to this recipient.
TELEGRAM_CHAT_IDS = ["765118363"]

HAZEM_TOKEN = read_env_any("hazemtoken", "HAZEMTOKEN")
HAZEM2_TOKEN = read_env_any("hazem2token", "HAZEM2TOKEN")

MOSTAQL_ACCOUNTS = [
    ("HazemToken", HAZEM_TOKEN),
    ("Hazem2Token", HAZEM2_TOKEN),
]

if not TELEGRAM_TOKEN:
    print("Error: TELEGRAM_TOKEN is missing!")
    sys.exit(1)

if not HAZEM_TOKEN:
    print("Error: hazemtoken is missing! Set env var hazemtoken (or HAZEMTOKEN).")
    sys.exit(1)

if not HAZEM2_TOKEN:
    print("Error: hazem2token is missing! Set env var hazem2token (or HAZEM2TOKEN).")
    sys.exit(1)

# 2. Configuration - WE USE THE API URL NOW
# This is the specific URL that returns the JSON you showed me
MOSTAQL_URL = "https://mostaql.com/ajax/notifications"

def build_headers(cookie):
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Cookie": cookie,
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",  # Critical for getting JSON
        "Referer": "https://mostaql.com/dashboard",
    }

def send_telegram_msg(text):
    token_clean = TELEGRAM_TOKEN

    url = f"https://api.telegram.org/bot{token_clean}/sendMessage"
    for chat_id in TELEGRAM_CHAT_IDS:
        payload = {"chat_id": chat_id, "text": text}

        try:
            response = requests.post(url, json=payload, timeout=10)
            print(f"Telegram API Status ({chat_id}): {response.status_code}")
            if response.status_code != 200:
                print(f"Telegram Error ({chat_id}): {response.text}")
        except Exception as e:
            print(f"Failed to send Telegram ({chat_id}): {e}")


def check_mostaql_account(cookie, account_label):
    headers = build_headers(cookie)

    print(f"--- Checking {account_label} ---")
    try:
        response = requests.get(MOSTAQL_URL, headers=headers, timeout=30)

        # 1. Check for Login Redirect (HTML instead of JSON)
        content_type = response.headers.get("Content-Type", "")
        if "text/html" in content_type or "login" in response.url:
            print(f"Cookie invalid for {account_label}. Redirected to login page.")
            send_telegram_msg(
                f"⚠️ Mostaql Alert ({account_label}): Login cookie expired. Update GitHub Secret."
            )
            return

        if response.status_code == 200:
            # 2. Parse the JSON Data
            try:
                data = response.json()

                # Extract counts directly from the keys shown in your data
                notif_count = data.get("unread_notifications_count", 0)
                msg_count = data.get("unread_messages_count", 0)

                total_unread = notif_count + msg_count

                print(f"{account_label} -> Notifications: {notif_count} | Messages: {msg_count}")
                print(f"{account_label} -> Total Unread: {total_unread}")

                # 3. Alert Logic
                if total_unread > 0:
                    msg = (
                        f"🔔 {account_label}: You have {total_unread} new alerts on Mostaql!\n"
                        f"({notif_count} Notifs, {msg_count} Msgs)\n"
                        "Check here: https://mostaql.com/dashboard"
                    )
                    print("Sending Telegram Alert...")
                    send_telegram_msg(msg)
                else:
                    print(f"{account_label} has no new notifications.")

            except ValueError:
                print(f"Error: Could not parse JSON for {account_label}. The server returned something else.")
                print(response.text[:100])

        elif response.status_code == 401:
            print(f"401 Unauthorized for {account_label}. Token expired.")
            send_telegram_msg(
                f"⚠️ Mostaql Alert ({account_label}): Token expired (401). Update GitHub Secret immediately!"
            )

        else:
            print(f"Unexpected status code for {account_label}: {response.status_code}")

    except Exception as e:
        print(f"Script error for {account_label}: {e}")


def check_mostaql():
    print("--- Starting JSON API Check ---")
    print(f"Configured Mostaql accounts: {len(MOSTAQL_ACCOUNTS)}")
    print(f"Configured Telegram receivers: {len(TELEGRAM_CHAT_IDS)}")

    for account_label, cookie in MOSTAQL_ACCOUNTS:
        check_mostaql_account(cookie, account_label)

if __name__ == "__main__":
    check_mostaql()
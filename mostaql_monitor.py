import os
import requests
import sys

# 1. Load Secrets
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
MOSTAQL_COOKIE = os.environ.get("MOSTAQL_COOKIE")

# Debug: Check if secrets exist
if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    print("DEBUG: Telegram secrets are missing.")
if not MOSTAQL_COOKIE:
    print("Error: MOSTAQL_COOKIE is missing!")
    sys.exit(1)

# 2. Configuration - WE USE THE API URL NOW
# This is the specific URL that returns the JSON you showed me
MOSTAQL_URL = "https://mostaql.com/ajax/notifications"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Cookie": MOSTAQL_COOKIE,
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest", # Critical for getting JSON
    "Referer": "https://mostaql.com/dashboard"
}

def send_telegram_msg(text):
    if TELEGRAM_TOKEN.startswith("bot"):
        # Fix common user error if they pasted "bot" in the secret
        token_clean = TELEGRAM_TOKEN
    else:
        token_clean = TELEGRAM_TOKEN

    url = f"https://api.telegram.org/bot{token_clean}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Telegram API Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Telegram Error: {response.text}")
    except Exception as e:
        print(f"Failed to send Telegram: {e}")

def check_mostaql():
    print("--- Starting JSON API Check ---")
    try:
        response = requests.get(MOSTAQL_URL, headers=HEADERS, timeout=30)
        
        # 1. Check for Login Redirect (HTML instead of JSON)
        content_type = response.headers.get('Content-Type', '')
        if "text/html" in content_type or "login" in response.url:
            print("🚨 Cookie Invalid! Redirected to Login Page.")
            send_telegram_msg("⚠️ Mostaql Alert: Login Cookie Expired. Update GitHub Secret.")
            sys.exit(1)

        if response.status_code == 200:
            # 2. Parse the JSON Data
            try:
                data = response.json()
                
                # Extract counts directly from the keys shown in your data
                notif_count = data.get("unread_notifications_count", 0)
                msg_count = data.get("unread_messages_count", 0)
                
                total_unread = notif_count + msg_count
                
                print(f"Notifications: {notif_count} | Messages: {msg_count}")
                print(f"Total Unread: {total_unread}")

                # 3. Alert Logic
                if total_unread > 0:
                    msg = f"🔔 You have {total_unread} new alerts on Mostaql!\n({notif_count} Notifs, {msg_count} Msgs)\nCheck here: https://mostaql.com/dashboard"
                    print("Sending Telegram Alert...")
                    send_telegram_msg(msg)
                else:
                    print("No new notifications.")

            except ValueError:
                print("Error: Could not parse JSON. The server returned something else.")
                print(response.text[:100])
        
        elif response.status_code == 401:
            print("🚨 401 Unauthorized! Token Expired.")
            send_telegram_msg("⚠️ Mostaql Alert: Token Expired (401). Update GitHub Secret immediately!")
        
        else:
            print(f"Unexpected Status Code: {response.status_code}")

    except Exception as e:
        print(f"Script Error: {e}")

if __name__ == "__main__":
    check_mostaql()
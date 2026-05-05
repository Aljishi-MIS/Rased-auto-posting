import os
import requests

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

REPORT_FILE = "data/weekly_report.txt"

if not BOT_TOKEN or not CHAT_ID:
    raise ValueError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")

with open(REPORT_FILE, "r", encoding="utf-8") as f:
    report = f.read()

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

payload = {
    "chat_id": CHAT_ID,
    "text": report,
    "parse_mode": "HTML"
}

response = requests.post(url, data=payload)

print(response.text)

if response.status_code != 200:
    raise Exception("Failed to send Telegram dashboard")

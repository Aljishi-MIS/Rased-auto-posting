import os
import requests

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID")

IMAGE_FILE = "data/weekly_report_card.png"

if not BOT_TOKEN or not CHAT_ID:
    raise ValueError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

with open(IMAGE_FILE, "rb") as photo:
    response = requests.post(
        url,
        data={"chat_id": CHAT_ID},
        files={"photo": photo},
        timeout=30
    )

result = response.json()
print("Telegram response:", result)

if not result.get("ok"):
    raise Exception(f"Failed to send report image: {result}")

print("✅ Weekly report image sent to Telegram")

import os
import requests

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID")

REPORT_FILE = "data/weekly_report.txt"
IMAGE_FILE  = "data/weekly_report_card.png"

if not BOT_TOKEN or not CHAT_ID:
    raise ValueError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")

with open(REPORT_FILE, "r", encoding="utf-8") as f:
    report_text = f.read()

caption = report_text[:1024]

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

try:
    with open(IMAGE_FILE, "rb") as photo:
        response = requests.post(
            url,
            data={
                "chat_id":    CHAT_ID,
                "caption":    caption,
                "parse_mode": "HTML"
            },
            files={"photo": photo},
            timeout=30
        )
    result = response.json()
    print("Telegram response:", result)

    if not result.get("ok"):
        raise Exception(f"Failed to send image: {result}")

    print("✅ Weekly report image sent to Telegram")

except FileNotFoundError:
    print("⚠️ Image not found, sending text report instead")
    url_text = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    response = requests.post(
        url_text,
        data={
            "chat_id":    CHAT_ID,
            "text":       report_text,
            "parse_mode": "HTML"
        },
        timeout=30
    )
    print(response.json())

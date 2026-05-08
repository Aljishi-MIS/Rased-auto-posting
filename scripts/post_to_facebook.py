import os
import json
import requests

GRAPH_URL = "https://graph.facebook.com/v22.0"

FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN")

IMAGE_PATH = "output.png"
DATA_PATH = "data/daily.json"


def load_daily_data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def build_caption(data):
    stock_name = data.get("stock_name", "")
    symbol = data.get("symbol", "")
    price = data.get("price", "")
    entry = data.get("entry", "")
    target1 = data.get("target1", "")
    target2 = data.get("target2", "")
    stop_loss = data.get("stop_loss", "")
    momentum = data.get("momentum", "قوي")
    note = data.get("note", "قراءة فنية تعليمية مبنية على الزخم والسيولة.")

    return f"""🚀 إشارة مضارب اليومية

📊 {stock_name} - {symbol}

💰 السعر الحالي: {price} ريال
🎯 نقطة الدخول: {entry} ريال

🟢 الهدف الأول: {target1} ريال
🟢 الهدف الثاني: {target2} ريال

🔴 وقف الخسارة: {stop_loss} ريال

⚡ الزخم: {momentum}

📌 قراءة فنية:
{note}

⚠️ محتوى تعليمي وتحليلي فقط — لا يُعد توصية استثمارية

تابعنا:
t.me/TASI_Smart
instagram.com/tasi.signals.sa
"""


def post_to_facebook():
    if not FB_PAGE_ID:
        raise ValueError("Missing FB_PAGE_ID secret")

    if not FB_PAGE_TOKEN:
        raise ValueError("Missing FB_PAGE_TOKEN secret")

    if not os.path.exists(IMAGE_PATH):
        raise FileNotFoundError("output.png not found")

    data = load_daily_data()
    caption = build_caption(data)

    response = requests.post(
        f"{GRAPH_URL}/{FB_PAGE_ID}/photos",
        data={
            "caption": caption,
            "access_token": FB_PAGE_TOKEN,
        },
        files={
            "source": open(IMAGE_PATH, "rb"),
        },
        timeout=60,
    )

    result = response.json()
    print("Facebook response:", result)

    if "id" not in result:
        raise RuntimeError(f"Facebook posting failed: {result}")

    print(f"Facebook post published successfully: {result['id']}")


if __name__ == "__main__":
    post_to_facebook()

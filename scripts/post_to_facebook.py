import os
import json
import requests

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
    note = data.get(
        "note",
        "قراءة فنية تعليمية لسهم قريب من منطقة مقاومة مع متابعة السيولة."
    )

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
"""


def post_to_facebook():
    if not FB_PAGE_ID:
        raise ValueError("Missing FB_PAGE_ID secret")

    if not FB_PAGE_TOKEN:
        raise ValueError("Missing FB_PAGE_TOKEN secret")

    if not os.path.exists(IMAGE_PATH):
        raise FileNotFoundError(f"{IMAGE_PATH} not found")

    data = load_daily_data()
    caption = build_caption(data)

    url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos"

    with open(IMAGE_PATH, "rb") as image_file:
        response = requests.post(
            url,
            data={
                "caption": caption,
                "access_token": FB_PAGE_TOKEN,
            },
            files={
                "source": image_file,
            },
            timeout=60,
        )

    print(response.text)

    if response.status_code != 200:
        raise RuntimeError("Facebook posting failed")

    result = response.json()

    if not result.get("id"):
        raise RuntimeError(f"Facebook did not return post id: {result}")

    print("Posted to Facebook successfully")
    print(f"Facebook photo id: {result.get('id')}")


if __name__ == "__main__":
    post_to_facebook()
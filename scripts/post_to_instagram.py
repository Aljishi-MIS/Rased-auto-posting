import os
import json
import time
import requests

GRAPH_URL = "https://graph.facebook.com/v22.0"

IG_USER_ID = os.getenv("IG_USER_ID")
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
IMAGE_URL = os.getenv("IMAGE_URL")

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

#تاسي #السوق_السعودي #أسهم #مضارب
"""


def create_media_container(caption):
    if not IG_USER_ID:
        raise ValueError("Missing IG_USER_ID secret")

    if not IG_ACCESS_TOKEN:
        raise ValueError("Missing IG_ACCESS_TOKEN secret")

    if not IMAGE_URL:
        raise ValueError("Missing IMAGE_URL environment variable")

    response = requests.post(
        f"{GRAPH_URL}/{IG_USER_ID}/media",
        data={
            "image_url": IMAGE_URL,
            "caption": caption,
            "access_token": IG_ACCESS_TOKEN,
        },
        timeout=60,
    )

    result = response.json()
    print("Instagram create media response:", result)

    if "id" not in result:
        raise RuntimeError(f"Instagram media container failed: {result}")

    return result["id"]


def publish_media(creation_id):
    response = requests.post(
        f"{GRAPH_URL}/{IG_USER_ID}/media_publish",
        data={
            "creation_id": creation_id,
            "access_token": IG_ACCESS_TOKEN,
        },
        timeout=60,
    )

    result = response.json()
    print("Instagram publish response:", result)

    if "id" not in result:
        raise RuntimeError(f"Instagram publish failed: {result}")

    return result["id"]


def main():
    data = load_daily_data()
    caption = build_caption(data)

    print("Creating Instagram media container...")
    creation_id = create_media_container(caption)

    time.sleep(10)

    print("Publishing Instagram media...")
    media_id = publish_media(creation_id)

    print(f"Instagram post published successfully: {media_id}")


if __name__ == "__main__":
    main()

import os
import requests
import time

FB_PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN")

IMAGE_URL = os.getenv(
    "IMAGE_URL",
    "https://raw.githubusercontent.com/Aljishi/TASI-Liquidity/main/output.png"
)

CAPTION = """
🚀 TASI SMART BOT

📈 تحليل فني وزخم لحظي
🤖 إشارات مدعومة بالذكاء الاصطناعي
🇸🇦 السوق السعودي - تاسي

⚠️ المحتوى تعليمي فقط وليس توصية استثمارية
"""

GRAPH_URL = "https://graph.facebook.com/v19.0"


def get_instagram_business_id():
    url = f"{GRAPH_URL}/me/accounts"

    response = requests.get(
        url,
        params={
            "access_token": FB_PAGE_TOKEN
        },
        timeout=60
    )

    data = response.json()

    if "data" not in data:
        raise RuntimeError(f"Failed to fetch pages: {data}")

    page_id = data["data"][0]["id"]

    ig_response = requests.get(
        f"{GRAPH_URL}/{page_id}",
        params={
            "fields": "instagram_business_account",
            "access_token": FB_PAGE_TOKEN
        },
        timeout=60
    )

    ig_data = ig_response.json()

    if "instagram_business_account" not in ig_data:
        raise RuntimeError(
            "Instagram business account not connected to page"
        )

    return ig_data["instagram_business_account"]["id"]


def create_media_container(ig_user_id):
    url = f"{GRAPH_URL}/{ig_user_id}/media"

    response = requests.post(
        url,
        data={
            "image_url": IMAGE_URL,
            "caption": CAPTION,
            "access_token": FB_PAGE_TOKEN
        },
        timeout=60
    )

    result = response.json()

    if "id" not in result:
        raise RuntimeError(f"Media container failed: {result}")

    return result["id"]


def publish_media(ig_user_id, creation_id):
    url = f"{GRAPH_URL}/{ig_user_id}/media_publish"

    response = requests.post(
        url,
        data={
            "creation_id": creation_id,
            "access_token": FB_PAGE_TOKEN
        },
        timeout=60
    )

    result = response.json()

    if "id" not in result:
        raise RuntimeError(f"Publish failed: {result}")

    return result["id"]


def main():
    print("Fetching Instagram Business ID...")
    ig_user_id = get_instagram_business_id()

    print(f"Instagram User ID: {ig_user_id}")

    print("Creating media container...")
    creation_id = create_media_container(ig_user_id)

    time.sleep(10)

    print("Publishing to Instagram...")
    media_id = publish_media(ig_user_id, creation_id)

    print("Instagram post published successfully")
    print(f"Media ID: {media_id}")


if __name__ == "__main__":
    main()
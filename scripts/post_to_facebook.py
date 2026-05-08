import os
import requests

FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN")
IMAGE_URL = os.getenv("IMAGE_URL")
CAPTION = os.getenv("CAPTION", "TASI AI Signals")

GRAPH_URL = "https://graph.facebook.com/v25.0"


def post_to_facebook():
    if not FB_PAGE_ID:
        raise RuntimeError("FB_PAGE_ID is missing")

    if not FB_PAGE_TOKEN:
        raise RuntimeError("FB_PAGE_TOKEN is missing")

    if not IMAGE_URL:
        raise RuntimeError("IMAGE_URL is missing")

    url = f"{GRAPH_URL}/{FB_PAGE_ID}/photos"

    payload = {
        "url": IMAGE_URL,
        "caption": CAPTION,
        "access_token": FB_PAGE_TOKEN,
    }

    response = requests.post(url, data=payload, timeout=60)
    result = response.json()

    print("Facebook response:", result)

    if "id" not in result and "post_id" not in result:
        raise RuntimeError(f"Facebook posting failed: {result}")

    print("Facebook post published successfully")


if __name__ == "__main__":
    post_to_facebook()

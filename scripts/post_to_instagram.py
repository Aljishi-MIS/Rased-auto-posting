import os
import requests
import time

FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN")
IMAGE_URL = os.getenv("IMAGE_URL")
CAPTION = os.getenv("CAPTION", "TASI AI Signals")

GRAPH_URL = "https://graph.facebook.com/v25.0"


def get_instagram_business_id():
    url = f"{GRAPH_URL}/{FB_PAGE_ID}"
    params = {
        "fields": "instagram_business_account",
        "access_token": FB_PAGE_TOKEN
    }

    response = requests.get(url, params=params)
    result = response.json()

    print("Instagram account response:", result)

    if "instagram_business_account" not in result:
        raise RuntimeError(f"No Instagram business account linked: {result}")

    return result["instagram_business_account"]["id"]


def create_media_container(ig_user_id):
    url = f"{GRAPH_URL}/{ig_user_id}/media"

    payload = {
        "image_url": IMAGE_URL,
        "caption": CAPTION,
        "access_token": FB_PAGE_TOKEN
    }

    response = requests.post(url, data=payload)
    result = response.json()

    print("Instagram create media response:", result)

    if "id" not in result:
        raise RuntimeError(f"Instagram media container failed: {result}")

    return result["id"]


def publish_container(ig_user_id, creation_id):
    url = f"{GRAPH_URL}/{ig_user_id}/media_publish"

    payload = {
        "creation_id": creation_id,
        "access_token": FB_PAGE_TOKEN
    }

    response = requests.post(url, data=payload)
    result = response.json()

    print("Instagram publish response:", result)

    if "id" not in result:
        raise RuntimeError(f"Instagram publish failed: {result}")

    return result["id"]


def main():
    ig_user_id = get_instagram_business_id()

    print("Instagram User ID:", ig_user_id)

    creation_id = create_media_container(ig_user_id)

    print("Creation ID:", creation_id)

    time.sleep(10)

    publish_id = publish_container(ig_user_id, creation_id)

    print("Instagram Post Published:", publish_id)


if __name__ == "__main__":
    main()
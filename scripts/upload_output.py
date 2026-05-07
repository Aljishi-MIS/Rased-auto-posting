import os
import base64
import requests

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")

FILE_PATH = "output.png"


def upload_image():
    if not os.path.exists(FILE_PATH):
        raise FileNotFoundError("output.png not found")

    with open(FILE_PATH, "rb") as f:
        content = base64.b64encode(f.read()).decode()

    api_url = (
        f"https://api.github.com/repos/"
        f"{GITHUB_REPOSITORY}/contents/output.png"
    )

    get_response = requests.get(
        api_url,
        headers={
            "Authorization": f"token {GITHUB_TOKEN}"
        },
        timeout=60
    )

    sha = None

    if get_response.status_code == 200:
        sha = get_response.json()["sha"]

    payload = {
        "message": "Update output image",
        "content": content,
        "branch": "main"
    }

    if sha:
        payload["sha"] = sha

    response = requests.put(
        api_url,
        headers={
            "Authorization": f"token {GITHUB_TOKEN}"
        },
        json=payload,
        timeout=60
    )

    print(response.text)

    if response.status_code not in [200, 201]:
        raise RuntimeError("Failed to upload image")

    print("Image uploaded successfully")


if __name__ == "__main__":
    upload_image()
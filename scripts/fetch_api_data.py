import os
import requests
import json

API_URL = os.environ.get("API_URL")
API_KEY = os.environ.get("API_KEY")

headers = {
    "Authorization": f"Bearer {API_KEY}"
}

response = requests.get(API_URL, headers=headers)

data = response.json()

# 👇 اختر أفضل سهم (مؤقت)
stock = data[0]

daily_data = {
    "brand": "مضارب",
    "stock_name": stock["name"],
    "symbol": stock["symbol"],
    "price": str(stock["price"]),
    "entry": str(round(stock["price"] * 1.01, 2)),
    "target1": str(round(stock["price"] * 1.03, 2)),
    "target2": str(round(stock["price"] * 1.06, 2)),
    "stop_loss": str(round(stock["price"] * 0.98, 2)),
    "momentum": "قوي",
    "note": "قراءة فنية تعليمية لسهم قريب من منطقة مقاومة مع متابعة السيولة."
}

with open("data/daily.json", "w", encoding="utf-8") as f:
    json.dump(daily_data, f, ensure_ascii=False, indent=2)

print("API data loaded successfully.")

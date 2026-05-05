import os
import json
import requests
from datetime import datetime


API_URL = os.environ.get("API_URL")
API_KEY = os.environ.get("API_KEY")

SNAPSHOT_FILE = "data/market_snapshot.json"
OUTPUT_FILE = "data/daily.json"


def safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def load_market_data():
    # 1) Try API
    if API_URL:
        try:
            headers = {}
            if API_KEY:
                headers["Authorization"] = f"Bearer {API_KEY}"

            response = requests.get(API_URL, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            if isinstance(data, dict) and "data" in data:
                data = data["data"]

            if isinstance(data, list) and len(data) > 0:
                print("Market data loaded from API")
                return data

        except Exception as e:
            print("API failed, trying local snapshot...")
            print(e)

    # 2) Try local snapshot
    try:
        with open(SNAPSHOT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list) and len(data) > 0:
            print("Market data loaded from local snapshot")
            return data

    except Exception as e:
        print("Local snapshot not found, using fallback data...")
        print(e)

    # 3) Fallback data
    return [
        {
            "name": "أكوا باور",
            "symbol": "2082",
            "price": 235.40,
            "high": 238.00,
            "low": 231.00,
            "volume": 1200000,
            "avg_volume": 600000,
            "change_percent": 2.4,
            "resistance": 238.00,
            "support": 231.00
        }
    ]


def score_stock(stock):
    price = safe_float(stock.get("price"))
    high = safe_float(stock.get("high"), price)
    low = safe_float(stock.get("low"), price)
    volume = safe_float(stock.get("volume"))
    avg_volume = safe_float(stock.get("avg_volume"), 1)
    change_percent = safe_float(stock.get("change_percent"))
    resistance = safe_float(stock.get("resistance"), high)

    score = 0
    reasons = []

    # 1) Positive price action
    if change_percent > 0:
        score += 20
        reasons.append("إغلاق إيجابي")

    if change_percent >= 2:
        score += 15
        reasons.append("زخم سعري قوي")

    # 2) Volume spike
    volume_ratio = volume / avg_volume if avg_volume > 0 else 0

    if volume_ratio >= 2:
        score += 25
        reasons.append("حجم تداول أعلى من المتوسط 2x")

    elif volume_ratio >= 1.5:
        score += 15
        reasons.append("زيادة جيدة في السيولة")

    # 3) Close near high
    daily_range = high - low
    close_near_high = ((price - low) / daily_range) if daily_range > 0 else 0

    if close_near_high >= 0.80:
        score += 20
        reasons.append("إغلاق قريب من أعلى السعر")

    elif close_near_high >= 0.65:
        score += 10
        reasons.append("تمركز سعري جيد")

    # 4) Near resistance / breakout setup
    if resistance > 0:
        distance_to_resistance = abs(resistance - price) / price

        if distance_to_resistance <= 0.02:
            score += 20
            reasons.append("قريب من مقاومة مهمة")

    return score, reasons


def build_daily_json(best_stock, score, reasons):
    price = safe_float(best_stock.get("price"))
    resistance = safe_float(best_stock.get("resistance"), price * 1.01)
    support = safe_float(best_stock.get("support"), price * 0.98)

    entry = round(max(price * 1.005, resistance), 2)
    target1 = round(entry * 1.03, 2)
    target2 = round(entry * 1.06, 2)
    stop_loss = round(min(support, entry * 0.98), 2)

    if score >= 75:
        momentum = "قوي"
    elif score >= 55:
        momentum = "متوسط"
    else:
        momentum = "ضعيف"

    reason_text = " + ".join(reasons[:3]) if reasons else "قراءة فنية تعليمية بناءً على حركة السعر والسيولة."

    return {
        "brand": "مضارب",
        "mode": "morning",
        "stock_name": best_stock.get("name", ""),
        "symbol": str(best_stock.get("symbol", "")),
        "price": f"{price:.2f}",
        "entry": f"{entry:.2f}",
        "target1": f"{target1:.2f}",
        "target2": f"{target2:.2f}",
        "stop_loss": f"{stop_loss:.2f}",
        "momentum": momentum,
        "score": score,
        "note": f"قراءة فنية تعليمية: {reason_text}."
    }


def main():
    stocks = load_market_data()

    ranked = []

    for stock in stocks:
        price = safe_float(stock.get("price"))
        if price <= 0:
            continue

        score, reasons = score_stock(stock)
        ranked.append((score, stock, reasons))

    ranked.sort(key=lambda x: x[0], reverse=True)

    best_score, best_stock, best_reasons = ranked[0]

    daily_data = build_daily_json(best_stock, best_score, best_reasons)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(daily_data, f, ensure_ascii=False, indent=2)

    print("Smart Scanner completed successfully")
    print(f"Selected: {daily_data['stock_name']} - {daily_data['symbol']}")
    print(f"Score: {best_score}")
    print(f"Reasons: {best_reasons}")


if __name__ == "__main__":
    main()

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
    if API_URL:
        try:
            headers = {}
            if API_KEY:
                headers["Authorization"] = f"Bearer {API_KEY}"

            response = requests.get(API_URL, headers=headers, timeout=12)
            response.raise_for_status()
            data = response.json()

            if isinstance(data, dict) and "data" in data:
                data = data["data"]

            if isinstance(data, list) and len(data) > 0:
                print("Loaded from API")
                return data

        except Exception as e:
            print("API failed, using local snapshot")
            print(e)

    with open(SNAPSHOT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    print("Loaded from market_snapshot.json")
    return data


def calculate_score(stock):
    price = safe_float(stock.get("price"))
    high = safe_float(stock.get("high"), price)
    low = safe_float(stock.get("low"), price)
    resistance = safe_float(stock.get("resistance"), high)
    support = safe_float(stock.get("support"), low)
    volume = safe_float(stock.get("volume"))
    avg_volume = safe_float(stock.get("avg_volume"), 1)
    change_percent = safe_float(stock.get("change_percent"))
    rsi = safe_float(stock.get("rsi"), 50)

    score = 0
    reasons = []

    # 1) Breakout / near breakout
    if price >= resistance:
        score += 30
        reasons.append("اختراق مقاومة")
    elif resistance > 0 and ((resistance - price) / price) <= 0.015:
        score += 22
        reasons.append("قريب من اختراق مقاومة")
    elif resistance > 0 and ((resistance - price) / price) <= 0.03:
        score += 12
        reasons.append("قريب من مقاومة مهمة")

    # 2) Volume spike
    volume_ratio = volume / avg_volume if avg_volume > 0 else 0

    if volume_ratio >= 3:
        score += 25
        reasons.append("حجم تداول أعلى من المتوسط 3x")
    elif volume_ratio >= 2:
        score += 20
        reasons.append("حجم تداول أعلى من المتوسط 2x")
    elif volume_ratio >= 1.5:
        score += 10
        reasons.append("زيادة واضحة في السيولة")

    # 3) RSI
    if 45 <= rsi <= 65:
        score += 20
        reasons.append("RSI صحي للزخم")
    elif 35 <= rsi < 45:
        score += 12
        reasons.append("RSI قريب من منطقة ارتداد")
    elif 65 < rsi <= 72:
        score += 8
        reasons.append("RSI قوي مع مراقبة التشبع")
    elif rsi > 75:
        score -= 15
        reasons.append("RSI مرتفع وقد يكون السهم متشبع")

    # 4) Close near high
    daily_range = high - low
    close_position = ((price - low) / daily_range) if daily_range > 0 else 0

    if close_position >= 0.85:
        score += 20
        reasons.append("إغلاق قريب من أعلى السعر")
    elif close_position >= 0.70:
        score += 12
        reasons.append("تمركز سعري إيجابي")

    # 5) Price momentum
    if change_percent >= 3:
        score += 15
        reasons.append("زخم سعري قوي")
    elif change_percent >= 1.5:
        score += 10
        reasons.append("إغلاق إيجابي")
    elif change_percent < 0:
        score -= 20
        reasons.append("تغير سلبي")

    # 6) Risk reward
    entry = max(price, resistance)
    stop_loss = support
    target1 = entry * 1.03

    risk = entry - stop_loss
    reward = target1 - entry
    rr = reward / risk if risk > 0 else 0

    if rr >= 2.5:
        score += 20
        reasons.append("R:R ممتاز")
    elif rr >= 1.8:
        score += 10
        reasons.append("R:R مقبول")
    else:
        score -= 10
        reasons.append("R:R ضعيف")

    return score, reasons, rr, volume_ratio


def build_daily_json(stock, score, reasons, rr, volume_ratio):
    price = safe_float(stock.get("price"))
    resistance = safe_float(stock.get("resistance"), safe_float(stock.get("high"), price))
    support = safe_float(stock.get("support"), safe_float(stock.get("low"), price))

    entry = round(max(price, resistance), 2)

    # أهداف مبنية على المقاومة/الاختراق وليس حساب ثابت فقط
    target1 = round(entry * 1.03, 2)
    target2 = round(entry * 1.06, 2)

    # وقف الخسارة أقرب دعم أو 2% أقل من الدخول
    stop_loss = round(max(support, entry * 0.98), 2)

    if score >= 85:
        momentum = "قوي جداً"
    elif score >= 70:
        momentum = "قوي"
    elif score >= 55:
        momentum = "متوسط"
    else:
        momentum = "ضعيف"

    note_reasons = " + ".join(reasons[:3])

    return {
        "brand": "مضارب",
        "mode": "morning",
        "stock_name": stock.get("name", ""),
        "symbol": str(stock.get("symbol", "")),
        "price": f"{price:.2f}",
        "entry": f"{entry:.2f}",
        "target1": f"{target1:.2f}",
        "target2": f"{target2:.2f}",
        "stop_loss": f"{stop_loss:.2f}",
        "momentum": momentum,
        "score": score,
        "rr": round(rr, 2),
        "volume_ratio": round(volume_ratio, 2),
        "source": "API" if API_URL else "market_snapshot",
        "note": f"قراءة فنية تعليمية: {note_reasons}."
    }


def main():
    stocks = load_market_data()

    ranked = []

    for stock in stocks:
        price = safe_float(stock.get("price"))
        volume = safe_float(stock.get("volume"))

        if price <= 0 or volume <= 0:
            continue

        score, reasons, rr, volume_ratio = calculate_score(stock)

        ranked.append({
            "score": score,
            "stock": stock,
            "reasons": reasons,
            "rr": rr,
            "volume_ratio": volume_ratio
        })

    if not ranked:
        raise Exception("No valid stocks found")

    ranked.sort(key=lambda x: x["score"], reverse=True)

    best = ranked[0]

    daily_data = build_daily_json(
        best["stock"],
        best["score"],
        best["reasons"],
        best["rr"],
        best["volume_ratio"]
    )

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(daily_data, f, ensure_ascii=False, indent=2)

    print("Smart Scanner completed")
    print(f"Selected: {daily_data['stock_name']} - {daily_data['symbol']}")
    print(f"Score: {daily_data['score']}")
    print(f"R:R: {daily_data['rr']}")
    print(f"Volume Ratio: {daily_data['volume_ratio']}")
    print(f"Source: {daily_data['source']}")
    print(f"Note: {daily_data['note']}")


if __name__ == "__main__":
    main()

import os
import json
import requests
from datetime import datetime

API_KEY  = os.environ.get("API_KEY")
API_URL  = os.environ.get("API_URL", "https://app.sahmk.sa/api/v1")

SNAPSHOT_FILE = "data/market_snapshot.json"
OUTPUT_FILE   = "data/daily.json"

HEADERS = {"X-API-Key": API_KEY} if API_KEY else {}


def safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def get(endpoint, params=None):
    try:
        r = requests.get(
            f"{API_URL}{endpoint}",
            headers=HEADERS,
            params=params or {},
            timeout=15
        )
        print(f"  {endpoint} -> HTTP {r.status_code}")
        if r.status_code == 200:
            return r.json()
        else:
            print(f"  Response: {r.text[:200]}")
    except Exception as e:
        print(f"  error {endpoint}: {e}")
    return None


def fetch_gainers():
    data = get("/market/gainers/", {"limit": 25, "index": "TASI"})
    if data:
        stocks = data if isinstance(data, list) else data.get("gainers", data.get("data", []))
        print(f"  gainers -> {len(stocks)}")
        return stocks
    return []


def fetch_volume():
    data = get("/market/volume/", {"limit": 25, "index": "TASI"})
    if data:
        stocks = data if isinstance(data, list) else data.get("stocks", data.get("data", []))
        print(f"  volume -> {len(stocks)}")
        return stocks
    return []


def fetch_market_summary():
    data = get("/market/summary/", {"index": "TASI"})
    if data:
        val = data.get("index_value", "")
        chg = safe_float(data.get("index_change_percent", 0))
        print(f"  TASI -> {val} ({chg:+.2f}%)")
    return data


def normalize(raw):
    price      = safe_float(raw.get("price") or raw.get("close"))
    high       = safe_float(raw.get("high"),   price * 1.01)
    low        = safe_float(raw.get("low"),    price * 0.99)
    volume     = safe_float(raw.get("volume"))
    change_pct = safe_float(raw.get("change_percent") or raw.get("change_pct"))
    avg_volume = safe_float(raw.get("avg_volume"), volume * 0.70)
    resistance = safe_float(raw.get("resistance"), high)
    support    = safe_float(raw.get("support"),    low)
    rsi        = safe_float(raw.get("rsi"), max(20, min(80, 50 + change_pct * 3)))

    return {
        "name":           raw.get("name") or raw.get("name_ar") or str(raw.get("symbol", "")),
        "symbol":         str(raw.get("symbol", "")),
        "price":          price,
        "high":           high,
        "low":            low,
        "volume":         volume,
        "avg_volume":     avg_volume,
        "change_percent": change_pct,
        "resistance":     resistance,
        "support":        support,
        "rsi":            rsi,
    }


def load_market_data():
    stocks = []

    if not API_KEY:
        print("API_KEY missing")
    else:
        print(f"\n fetching from: {API_URL}\n")
        fetch_market_summary()
        gainers = fetch_gainers()
        volume  = fetch_volume()

        seen, all_raw = set(), []
        for s in gainers + volume:
            sym = str(s.get("symbol", ""))
            if sym and sym not in seen:
                seen.add(sym)
                all_raw.append(s)

        if all_raw:
            stocks = [normalize(s) for s in all_raw if safe_float(s.get("price")) > 0]
            print(f"\n total stocks from API: {len(stocks)}")

    if len(stocks) < 3:
        print("\n Fallback -> market_snapshot.json")
        with open(SNAPSHOT_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        stocks = [normalize(s) for s in raw]
        print(f"  loaded {len(stocks)} from snapshot")

    return stocks


def calculate_score(stock):
    price          = safe_float(stock.get("price"))
    high           = safe_float(stock.get("high"), price)
    low            = safe_float(stock.get("low"),  price)
    resistance     = safe_float(stock.get("resistance"), high)
    support        = safe_float(stock.get("support"),    low)
    volume         = safe_float(stock.get("volume"))
    avg_volume     = max(safe_float(stock.get("avg_volume")), 1)
    change_percent = safe_float(stock.get("change_percent"))
    rsi            = safe_float(stock.get("rsi"), 50)

    score, reasons = 0, []

    if change_percent < -1:
        return -999, ["تغير سلبي مستبعد"], 0, 0

    if resistance > 0:
        dist = (resistance - price) / price
        if price >= resistance:
            score += 30; reasons.append("اختراق مقاومة")
        elif dist <= 0.015:
            score += 22; reasons.append("قريب جداً من الاختراق")
        elif dist <= 0.03:
            score += 12; reasons.append("قريب من مقاومة")

    volume_ratio = volume / avg_volume
    if   volume_ratio >= 3:   score += 25; reasons.append(f"حجم {volume_ratio:.1f}x")
    elif volume_ratio >= 2:   score += 20; reasons.append(f"حجم {volume_ratio:.1f}x")
    elif volume_ratio >= 1.5: score += 10; reasons.append("زيادة سيولة")

    if   50 <= rsi <= 65:  score += 20; reasons.append(f"RSI {rsi:.0f} صحي")
    elif 40 <= rsi < 50:   score += 12; reasons.append(f"RSI {rsi:.0f} بداية زخم")
    elif 65 < rsi <= 72:   score +=  8; reasons.append(f"RSI {rsi:.0f} قوي")
    elif rsi > 75:         score -= 15; reasons.append(f"RSI {rsi:.0f} تشبع شرائي")

    daily_range = high - low
    close_pos   = ((price - low) / daily_range) if daily_range > 0 else 0.5
    if   close_pos >= 0.85: score += 20; reasons.append("اغلاق عند القمة")
    elif close_pos >= 0.70: score += 12; reasons.append("تمركز ايجابي")

    if   change_percent >= 3:   score += 15; reasons.append(f"ارتفاع {change_percent:.1f}%")
    elif change_percent >= 1.5: score += 10; reasons.append(f"ارتفاع {change_percent:.1f}%")

    entry     = max(price, resistance * 0.999) if resistance > price * 0.95 else price
    stop_loss = max(support, entry * 0.97)
    target1   = entry * 1.03
    risk      = entry - stop_loss
    reward    = target1 - entry
    rr        = reward / risk if risk > 0 else 0

    if   rr >= 2.5: score += 20; reasons.append(f"R:R {rr:.1f} ممتاز")
    elif rr >= 1.5: score += 10; reasons.append(f"R:R {rr:.1f} جيد")
    else:           score -= 10; reasons.append(f"R:R {rr:.1f} ضعيف")

    return score, reasons, rr, volume_ratio


def build_daily_json(stock, score, reasons, rr, volume_ratio):
    price      = safe_float(stock.get("price"))
    resistance = safe_float(stock.get("resistance"), safe_float(stock.get("high"), price))
    support    = safe_float(stock.get("support"),    safe_float(stock.get("low"),  price))

    entry     = round(price * 1.001, 2)
    target1   = round(entry * 1.03, 2)
    target2   = round(entry * 1.06, 2)
    stop_loss = round(max(support, entry * 0.97), 2)

    momentum = (
        "قوي جداً" if score >= 85 else
        "قوي"      if score >= 70 else
        "متوسط"    if score >= 55 else "ضعيف"
    )

    from_api = bool(API_KEY) and len(reasons) > 0

    return {
        "brand":        "مضارب",
        "mode":         "morning",
        "stock_name":   stock.get("name", ""),
        "symbol":       str(stock.get("symbol", "")),
        "price":        f"{price:.2f}",
        "entry":        f"{entry:.2f}",
        "target1":      f"{target1:.2f}",
        "target2":      f"{target2:.2f}",
        "stop_loss":    f"{stop_loss:.2f}",
        "momentum":     momentum,
        "score":        score,
        "rsi":          round(safe_float(stock.get("rsi")), 1),
        "rr":           round(rr, 2),
        "volume_ratio": round(volume_ratio, 2),
        "source":       "sahmk_api" if from_api else "market_snapshot",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "note":         f"قراءة فنية تعليمية: {' + '.join(reasons[:3])}."
    }


def main():
    stocks = load_market_data()

    ranked = []
    for stock in stocks:
        if safe_float(stock.get("price")) <= 0 or safe_float(stock.get("volume")) <= 0:
            continue
        score, reasons, rr, vol_ratio = calculate_score(stock)
        if score > 0:
            ranked.append({
                "score": score, "stock": stock,
                "reasons": reasons, "rr": rr, "volume_ratio": vol_ratio
            })

    if not ranked:
        for stock in stocks:
            score, reasons, rr, vol_ratio = calculate_score(stock)
            ranked.append({
                "score": score, "stock": stock,
                "reasons": reasons, "rr": rr, "volume_ratio": vol_ratio
            })

    if not ranked:
        raise RuntimeError("no stocks found")

    ranked.sort(key=lambda x: x["score"], reverse=True)

    print(f"\n{'='*55}")
    print("Top 5 Stocks:")
    for i, r in enumerate(ranked[:5], 1):
        s = r["stock"]
        print(f"  {i}. {s.get('name','')[:20]:<20} ({s.get('symbol'):>4}) "
              f"Score:{r['score']:>4} Vol:{r['volume_ratio']:.1f}x")

    best       = ranked[0]
    daily_data = build_daily_json(
        best["stock"], best["score"],
        best["reasons"], best["rr"], best["volume_ratio"]
    )

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(daily_data, f, ensure_ascii=False, indent=2)

    src = daily_data["source"]
    print(f"\n Selected: {daily_data['stock_name']} ({daily_data['symbol']})")
    print(f"  Price: {daily_data['price']} | Entry: {daily_data['entry']}")
    print(f"  Score: {daily_data['score']} | Source: {src}")
    print(f"  Time: {daily_data['generated_at']}")

    if src == "market_snapshot":
        print("\n  WARNING: using local snapshot — check API_KEY and API_URL")
        import sys
        sys.exit(1)  # يوقف الـ workflow — لا نشر من بيانات محلية


if __name__ == "__main__":
    main()

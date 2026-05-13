import os
import json
import re
import requests
from datetime import datetime, timezone, timedelta

API_KEY  = os.environ.get("API_KEY")
API_URL  = os.environ.get("API_URL", "https://app.sahmk.sa/api/v1")

SNAPSHOT_FILE = "data/market_snapshot.json"
OUTPUT_FILE   = "data/daily.json"

HEADERS = {"X-API-Key": API_KEY} if API_KEY else {}

TASI_SYMBOLS = [
    "1010","1020","1030","1050","1060","1080","1120","1150","1180","1210",
    "1211","1212","1213","1214","1301","1302","1303","1304","1320","1321",
    "2010","2020","2030","2040","2050","2060","2070","2080","2082","2083",
    "2090","2100","2110","2120","2130","2140","2150","2160","2170","2180",
    "2190","2200","2210","2220","2222","2223","2230","2240","2250","2290",
    "2310","2320","2330","2340","2350","2360","2370","2380","2381","2382",
    "4001","4002","4003","4004","4005","4006","4007","4008","4009","4010",
    "4011","4012","4013","4014","4015","4016","4017","4018","4019","4020",
    "4021","4030","4031","4040","4050","4051","4061","4100","4110","4130",
    "4140","4141","4142","4143","4144","4150","4160","4161","4162","4163",
    "4164","4170","4180","4190","4191","4192","4193","4200","4210","4220",
    "4230","4240","4250","4261","4270","4280","4281","4290","4291","4300",
    "4310","4320","4321","4322","4323","4324","4330","4331","4332","4333",
    "4334","4335","4336","4337","4338","4339","4340","4341","4342","4344",
    "4345","4346","4347","4348","4349","5010","5020","5110","6001","6002",
    "6010","6013","6014","6015","6020","6040","6050","6060","6070","7010",
    "7020","7030","7040","7203","7204","8010","8020","8030","8040","8050",
    "8060","8070","8100","8120","8150","8160","8170","8180","8190","8200",
    "8210","8230","8240","8250","8260","8270","8280","8300","8310","8311",
    "8320","8330","8340","9516","9526","9527","9528","9529","9536","9543",
    "9544","9545","9546","9547","9548","9549","9553","9554","9555","9556",
    "9557","9558","9559","9560","9561","9562","9563","9564","9565","9566",
    "9567","9568",
]

SECTORS = {
    "البنوك":         ["1010","1020","1030","1050","1060","1080","1120","1150"],
    "البتروكيماويات": ["2010","2020","2060","2090","2100","2150","2160","2170",
                      "2222","2223","2230"],
    "الاتصالات":      ["7010","7020","7030","7040","7203","7204"],
    "الطاقة":         ["5110","2040","2050"],
    "التجزئة":        ["4190","4200","4210","4220","4230","4240","4250","4261"],
    "العقار":         ["4020","4031","4040","4050","4100","4150","4300","4320",
                      "4321","4322","4323","4324"],
    "الصحة":          ["4002","4005","4007","4009","4013","4017","4019","4061"],
    "الصناعة":        ["1211","1212","2030","2080","2082","2083","2110","2120",
                      "2130","2140","2180","2190","2200","2210","2220","2240",
                      "2250","2290","2310","2320","2330","2340","2350","2360",
                      "2370","2380","2381","2382","4030"],
    "التامين":        ["8010","8020","8030","8040","8050","8060","8070","8100",
                      "8120","8150","8160","8170","8180","8190","8200","8210",
                      "8230","8240","8250","8260","8270","8280","8300","8310",
                      "8311","8320","8330","8340"],
    "الاستثمار":      ["1111","4280","4290","4310","4349","4330","4331","4332",
                      "4333","4334","4335","4336","4337","4338","4339","4340",
                      "4341","4342","4344","4345","4346","4347","4348"],
    "التقنية":        ["9516","9526","9527","9528","9529","9536","9543","9544",
                      "9545","9546","9547","9548","9549","9553","9554","9555",
                      "9556","9557","9558","9559","9560","9561","9562","9563",
                      "9564","9565","9566","9567","9568"],
    "الغذاء":         ["2060","2070","6001","6002","6010","6013","6014","6015",
                      "6020","6040","6050","6060","6070"],
    "التعليم":        ["4001","4003","4004","4006","4008","4010","4011","4012",
                      "4014","4015","4016","4018","4021"],
    "الترفيه":        ["4160","4161","4162","4163","4164","4170","4180"],
    "النقل":          ["1301","1302","1303","1304","1320","1321","5010","5020"],
}


def safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def get_sector(symbol):
    for sector_name, symbols in SECTORS.items():
        if str(symbol) in symbols:
            return sector_name
    return "اخرى"


def score_label(score):
    if score >= 90: return "انفجار محتمل"
    if score >= 80: return "زخم قوي"
    if score >= 75: return "مراقبة"
    return "ضعيف"


def is_market_open():
    KSA     = timezone(timedelta(hours=3))
    now     = datetime.now(KSA)
    weekday = now.weekday()
    t       = now.hour * 60 + now.minute
    print(f"  Market check: {now.strftime('%H:%M')} KSA | weekday={weekday} | t={t}")
    market_days  = [6, 0, 1, 2, 3]
    market_open  = 9 * 60 + 30
    market_close = 15 * 60 + 30
    is_open = weekday in market_days and market_open <= t <= market_close
    print(f"  Market open: {is_open}")
    return is_open


def get(endpoint, params=None):
    try:
        r = requests.get(
            f"{API_URL}{endpoint}",
            headers=HEADERS,
            params=params or {},
            timeout=15
        )
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"  error {endpoint}: {e}")
    return None


def fetch_market_summary():
    data = get("/market/summary/", {"index": "TASI"})
    if data:
        val = data.get("index_value", "")
        chg = safe_float(data.get("index_change_percent", 0))
        print(f"  TASI -> {val} ({chg:+.2f}%)")
    return data


def fetch_all_stocks():
    seen = {}
    for endpoint, key in [
        ("/market/gainers/", "gainers"),
        ("/market/volume/",  "stocks"),
    ]:
        data = get(endpoint, {"limit": 50, "index": "TASI"})
        if data:
            items = data if isinstance(data, list) else data.get(key, data.get("data", []))
            for s in items:
                sym = str(s.get("symbol", ""))
                if sym and sym not in seen:
                    seen[sym] = s

    print(f"  gainers+volume -> {len(seen)}")
    remaining = [sym for sym in TASI_SYMBOLS if sym not in seen]
    print(f"  fetching {len(remaining)} remaining stocks...")

    for sym in remaining:
        data = get(f"/quote/{sym}/")
        if data:
            s = data if isinstance(data, dict) else (data[0] if isinstance(data, list) and data else None)
            if s and safe_float(s.get("price") or s.get("close")) > 0:
                seen[sym] = s

    print(f"  total: {len(seen)}")
    return list(seen.values())


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
    sym        = str(raw.get("symbol", ""))

    return {
        "name":           raw.get("name") or raw.get("name_ar") or sym,
        "symbol":         sym,
        "price":          price,
        "high":           high,
        "low":            low,
        "volume":         volume,
        "avg_volume":     avg_volume,
        "change_percent": change_pct,
        "resistance":     resistance,
        "support":        support,
        "rsi":            rsi,
        "rs_rank":        0,
        "rs_vs_tasi":     0,
        "sector":         get_sector(sym),
    }


def load_market_data():
    stocks = []
    if not API_KEY:
        print("API_KEY missing")
    else:
        print(f"\n fetching ALL TASI from: {API_URL}\n")
        fetch_market_summary()
        all_raw = fetch_all_stocks()
        if all_raw:
            stocks = [normalize(s) for s in all_raw
                      if safe_float(s.get("price") or s.get("close")) > 0]
            print(f"\n normalized: {len(stocks)}")

    if len(stocks) < 3:
        print("\n Fallback -> market_snapshot.json")
        with open(SNAPSHOT_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        stocks = [normalize(s) for s in raw]
    return stocks


def calc_targets(price, high, low, resistance, support, change_pct):
    atr = max(high - low, price * 0.01)

    if resistance > price * 1.002:
        entry = round(resistance * 1.005, 2)
    else:
        entry = round(price * 1.005, 2)

    raw_t1 = entry + atr * 1.5
    t1     = round(min(raw_t1, entry * 1.04), 2)

    raw_t2 = t1 + atr * 1.5
    t2     = round(max(entry * 1.05, min(raw_t2, entry * 1.08)), 2)

    raw_sl    = max(support * 0.995, entry - atr * 1.5)
    stop_loss = round(max(raw_sl, entry * 0.97), 2)
    if stop_loss >= entry:
        stop_loss = round(entry * 0.97, 2)

    risk   = entry - stop_loss
    reward = t1 - entry
    rr     = round(reward / risk, 2) if risk > 0 else 0

    return entry, t1, t2, stop_loss, rr


def build_signal_reason(reasons, resistance, vol_ratio, rsi, rs_rank,
                         sector, news_reason="", news_sentiment="neutral"):
    parts = []

    if any("اختراق" in r or "قريب" in r for r in reasons):
        parts.append(f"اختراق {resistance:.2f}")

    if vol_ratio >= 2:
        parts.append(f"سيولة {vol_ratio:.1f}x فوق المتوسط")
    elif vol_ratio >= 1.5:
        parts.append(f"سيولة {vol_ratio:.1f}x")

    if 50 <= rsi <= 65:
        parts.append(f"RSI {rsi:.0f} في المنطقة الذهبية")
    elif 40 <= rsi < 50:
        parts.append(f"RSI {rsi:.0f} بداية زخم")

    if rs_rank >= 80:
        parts.append(f"RS Rank {rs_rank} قائد السوق")

    if sector and sector != "اخرى":
        parts.append(f"قطاع {sector} صاعد")

    if news_sentiment == "positive" and news_reason:
        parts.append(f"اخبار ايجابية: {news_reason}")
    elif news_sentiment == "negative" and news_reason:
        parts.append(f"تحذير: {news_reason}")

    if not parts:
        parts = reasons[:2]

    return " + ".join(parts[:4])


def calculate_score(stock, top_sectors=None, news_delta=0):
    price          = safe_float(stock.get("price"))
    high           = safe_float(stock.get("high"), price)
    low            = safe_float(stock.get("low"),  price)
    resistance     = safe_float(stock.get("resistance"), high)
    support        = safe_float(stock.get("support"),    low)
    volume         = safe_float(stock.get("volume"))
    avg_volume     = max(safe_float(stock.get("avg_volume")), 1)
    change_percent = safe_float(stock.get("change_percent"))
    rsi            = safe_float(stock.get("rsi"), 50)
    rs_rank        = safe_float(stock.get("rs_rank", 0))
    rs_vs_tasi     = safe_float(stock.get("rs_vs_tasi", 0))
    sector         = stock.get("sector", "")

    score, reasons = 0, []

    if change_percent < -1:
        return -999, ["تغير سلبي مستبعد"], 0, 0

    if resistance > 0:
        dist = (resistance - price) / price
        if price >= resistance:
            score += 30; reasons.append("اختراق مقاومة")
        elif dist <= 0.015:
            score += 22; reasons.append(f"قريب من الاختراق ({resistance:.2f})")
        elif dist <= 0.03:
            score += 12; reasons.append(f"قريب من مقاومة ({resistance:.2f})")

    volume_ratio = volume / avg_volume
    if   volume_ratio >= 3:   score += 25; reasons.append(f"سيولة استثنائية {volume_ratio:.1f}x")
    elif volume_ratio >= 2:   score += 20; reasons.append(f"سيولة عالية {volume_ratio:.1f}x")
    elif volume_ratio >= 1.5: score += 10; reasons.append(f"سيولة جيدة {volume_ratio:.1f}x")

    if   50 <= rsi <= 65:  score += 20; reasons.append(f"RSI {rsi:.0f} في المنطقة الذهبية")
    elif 40 <= rsi < 50:   score += 12; reasons.append(f"RSI {rsi:.0f} بداية زخم")
    elif 65 < rsi <= 72:   score +=  8; reasons.append(f"RSI {rsi:.0f} قوي")
    elif rsi > 75:         score -= 15; reasons.append(f"RSI {rsi:.0f} تشبع شرائي")

    daily_range = high - low
    close_pos   = ((price - low) / daily_range) if daily_range > 0 else 0.5
    if   close_pos >= 0.85: score += 20; reasons.append("اغلاق عند القمة")
    elif close_pos >= 0.70: score += 12; reasons.append("تمركز ايجابي")

    if   change_percent >= 3:   score += 15; reasons.append(f"ارتفاع قوي {change_percent:.1f}%")
    elif change_percent >= 1.5: score += 10; reasons.append(f"ارتفاع {change_percent:.1f}%")

    entry, t1, t2, stop_loss, rr = calc_targets(
        price, high, low, resistance, support, change_percent)
    if   rr >= 2.5: score += 15; reasons.append(f"R:​​​​​​​​​​​​​​​​

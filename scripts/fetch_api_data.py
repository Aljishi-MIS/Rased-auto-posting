import os
import json
import re
import requests
from datetime import datetime, timezone, timedelta

API_KEY           = os.environ.get("API_KEY")
API_URL           = os.environ.get("API_URL", "https://app.sahmk.sa/api/v1")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

SNAPSHOT_FILE = "data/market_snapshot.json"
INTEL_FILE    = "data/market_intel.json"
OUTPUT_FILE   = "data/daily.json"

HEADERS = {"X-API-Key": API_KEY} if API_KEY else {}

SECTORS = {
    "البنوك":         ["1010","1020","1030","1050","1060","1080","1120","1150"],
    "البتروكيماويات": ["2010","2020","2060","2090","2100","2150","2160","2170",
                      "2222","2223","2230"],
    "الاتصالات":      ["7010","7020","7030","7040","7203","7204"],
    "الطاقة":         ["5110","2040","2050"],
    "التجزئة":        ["4190","4200","4210","4220","4230","4240","4250","4261"],
    "العقار":         ["4020","4031","4040","4050","4100","4150","4300","4310",
                      "4320","4321","4322","4323","4324","4325","4326","4327","4328"],
    "الصحة":          ["4002","4005","4007","4009","4013","4017","4019","4061"],
    "الصناعة":        ["1211","1212","2030","2080","2082","2083","2110","2120",
                      "2130","2140","2180","2190","2200","2210","2220","2240",
                      "2250","2290","2310","2320","2330","2340","2350","2360",
                      "2370","2380","2381","2382","4030"],
    "التامين":        ["8010","8020","8030","8040","8050","8060","8070","8100",
                      "8120","8150","8160","8170","8180","8190","8200","8210",
                      "8230","8240","8250","8260","8270","8280","8300","8310",
                      "8311","8320","8330","8340"],
    "الاستثمار":      ["1111","4280","4290","4291","4349","4330","4331",
                      "4332","4333","4334","4335","4336","4337","4338","4339",
                      "4340","4341","4342","4344","4345","4346","4347","4348"],
    "التقنية":        ["9516","9526","9527","9528","9529","9536","9543","9544",
                      "9545","9546","9547","9548","9549","9553","9554","9555",
                      "9556","9557","9558","9559","9560","9561","9562","9563",
                      "9564","9565","9566","9567","9568"],
    "الغذاء":         ["2060","2070","6001","6002","6010","6013","6014","6015",
                      "6020","6040","6050","6060","6070"],
    "التعليم":        ["4001","4003","4004","4006","4008","4010","4011","4012",
                      "4014","4015","4016","4018","4021"],
    "الترفيه":        ["4110","4130","4140","4141","4142","4143","4144",
                      "4160","4161","4162","4163","4164","4170","4180"],
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
    market_open  = 10 * 60 + 0
    market_close = 15 * 60 + 0
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


def load_all_stocks_from_intel():
    try:
        with open(INTEL_FILE, "r", encoding="utf-8") as f:
            intel = json.load(f)

        all_stocks  = intel.get("top_stocks", [])
        top_sectors = intel.get("top_sectors", [])

        if not all_stocks:
            print("  market_intel.json فارغ")
            return [], []

        stocks = []
        for s in all_stocks:
            price = safe_float(s.get("price", 0))
            if price <= 0:
                continue
            sym = str(s.get("symbol", ""))
            vol = safe_float(s.get("volume", 0))

            stocks.append({
                "name":           s.get("name", "") or sym,
                "symbol":         sym,
                "price":          price,
                "high":           price * 1.01,
                "low":            price * 0.99,
                "volume":         vol,
                "avg_volume":     vol * 0.7,
                "change_percent": safe_float(s.get("change_pct", 0)),
                "resistance":     price * 1.01,
                "support":        price * 0.99,
                "rsi":            max(20, min(80, 50 + safe_float(s.get("change_pct", 0)) * 3)),
                "rs_rank":        s.get("rs_rank", 0),
                "rs_vs_tasi":     s.get("rs_vs_tasi", 0),
                "sector":         s.get("sector") or get_sector(sym),
            })

        print(f"  قراءة {len(stocks)} سهم من market_intel.json ✅")
        return stocks, top_sectors

    except FileNotFoundError:
        print("  market_intel.json غير موجود — fallback للـ API")
        return [], []
    except Exception as e:
        print(f"  market_intel.json error: {e}")
        return [], []


def enrich_top10_with_live_data(ranked):
    print(f"\n  تحديث أفضل 10 ببيانات حية...")
    updated = 0

    for r in ranked[:10]:
        stock = r["stock"]
        sym   = stock.get("symbol", "")
        data  = get(f"/quote/{sym}/")

        if data:
            s = data if isinstance(data, dict) else (data[0] if isinstance(data, list) and data else None)
            if s:
                price = safe_float(s.get("price") or s.get("close"))
                if price > 0:
                    live_vol            = safe_float(s.get("volume"), stock["volume"])
                    stock["price"]          = price
                    stock["high"]           = safe_float(s.get("high"),   price * 1.01)
                    stock["low"]            = safe_float(s.get("low"),    price * 0.99)
                    stock["volume"]         = live_vol
                    stock["avg_volume"]     = safe_float(s.get("avg_volume")) or live_vol * 0.7
                    stock["change_percent"] = safe_float(s.get("change_percent") or s.get("change_pct"))
                    stock["resistance"]     = safe_float(s.get("resistance"), stock["high"])
                    stock["support"]        = safe_float(s.get("support"),    stock["low"])
                    stock["rsi"]            = safe_float(s.get("rsi"), stock["rsi"])
                    updated += 1

    print(f"  تم تحديث {updated} سهم ✅")
    return ranked


def fallback_from_api():
    print("\n  Fallback: جلب من API مباشرة...")
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

    stocks = []
    for sym, s in seen.items():
        price = safe_float(s.get("price") or s.get("close"))
        if price > 0:
            vol = safe_float(s.get("volume"))
            stocks.append({
                "name":           s.get("name") or s.get("name_ar") or sym,
                "symbol":         sym,
                "price":          price,
                "high":           safe_float(s.get("high"),   price * 1.01),
                "low":            safe_float(s.get("low"),    price * 0.99),
                "volume":         vol,
                "avg_volume":     safe_float(s.get("avg_volume"), vol * 0.7),
                "change_percent": safe_float(s.get("change_percent") or s.get("change_pct")),
                "resistance":     safe_float(s.get("resistance"), safe_float(s.get("high"), price * 1.01)),
                "support":        safe_float(s.get("support"),    safe_float(s.get("low"),  price * 0.99)),
                "rsi":            safe_float(s.get("rsi"), 50),
                "rs_rank":        0,
                "rs_vs_tasi":     0,
                "sector":         get_sector(sym),
            })

    print(f"  API fallback: {len(stocks)} سهم")
    return stocks, []


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

    if rr < 1.0 and risk > 0:
        max_sl_drop = entry * 0.04
        better_sl   = round(entry - reward, 2)
        if entry - better_sl <= max_sl_drop:
            stop_loss = better_sl
            risk      = entry - stop_loss
            rr        = round(reward / risk, 2) if risk > 0 else 0

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
        parts.append(f"RS Rank {rs_rank} قائد السو​​​​​​​​​​​​​​​​

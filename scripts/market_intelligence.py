import os
import json
import requests
from datetime import datetime, timezone, timedelta

API_KEY  = os.environ.get("API_KEY")
API_URL  = os.environ.get("API_URL", "https://app.sahmk.sa/api/v1")
HEADERS  = {"X-API-Key": API_KEY} if API_KEY else {}
OUTPUT   = "data/market_intel.json"

# ✅ كاش 20 دقيقة — يمنع إعادة المسح في كل تشغيل
CACHE_MINUTES = 20

SECTORS = {
    "البنوك":         ["1010","1020","1030","1050","1060","1080","1120","1150"],
    "البتروكيماويات": ["2010","2020","2060","2090","2100","2150","2160","2170","2222","2223","2230"],
    "الاتصالات":      ["7010","7020","7030","7040","7203","7204"],
    "الطاقة":         ["5110","2040","2050"],
    "التجزئة":        ["4190","4200","4210","4220","4230","4240","4250","4261"],
    "العقار":         ["4020","4031","4040","4050","4100","4150","4300","4320","4321","4322","4323","4324"],
    "الصحة":          ["4002","4005","4007","4009","4013","4017","4019","4061"],
    "الصناعة":        ["1211","1212","2030","2080","2082","2083","2110","2120","2130","2140","2180",
                       "2190","2200","2210","2220","2240","2250","2290","2310","2320","2330","2340",
                       "2350","2360","2370","2380","2381","2382"],
    "التامين":        ["8010","8020","8030","8040","8050","8060","8070","8100","8120","8150","8160",
                       "8170","8180","8190","8200","8210","8230","8240","8250","8260","8270","8280",
                       "8300","8310","8311","8320","8330","8340"],
    "الاستثمار":      ["1111","4280","4290","4310","4349","4330","4331","4332","4333","4334","4335",
                       "4336","4337","4338","4339","4340","4341","4342","4344","4345","4346","4347","4348"],
    "التقنية":        ["9516","9526","9527","9528","9529","9536","9543","9544","9545","9546","9547",
                       "9548","9549","9553","9554","9555","9556","9557","9558","9559","9560","9561",
                       "9562","9563","9564","9565","9566","9567","9568"],
    "الغذاء":         ["2060","2070","6001","6002","6010","6013","6014","6015","6020","6040","6050","6060","6070"],
    "التعليم":        ["4001","4003","4004","4006","4008","4010","4011","4012","4014","4015","4016","4018","4021"],
    "الترفيه":        ["4160","4161","4162","4163","4164","4170","4180"],
    "النقل":          ["1301","1302","1303","1304","1320","1321","5010","5020"],
}


def safe_float(v, default=0.0):
    try:
        return float(v)
    except Exception:
        return default


def get_sector(symbol):
    for sector_name, symbols in SECTORS.items():
        if str(symbol) in symbols:
            return sector_name
    return "اخرى"


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


def is_cache_fresh():
    """✅ تحقق من أن market_intel.json أحدث من CACHE_MINUTES دقيقة"""
    try:
        with open(OUTPUT, "r", encoding="utf-8") as f:
            data = json.load(f)
        gen_at = data.get("generated_at", "")
        if not gen_at:
            return False, data
        gen_time = datetime.strptime(gen_at, "%Y-%m-%d %H:%M")
        age = (datetime.now() - gen_time).total_seconds() / 60
        if age < CACHE_MINUTES:
            print(f"  market_intel.json حديث ({age:.0f} دقيقة) — تخطي إعادة المسح ✅")
            return True, data
    except Exception:
        pass
    return False, {}


def get_tasi_performance():
    data = get("/market/summary/", {"index": "TASI"})
    if not data:
        return 0.0, 0.0
    change_pct = safe_float(data.get("index_change_percent", 0))
    tasi_20d   = 0.0
    hist = get("/market/historical/TASI/", {"period": 20})
    if hist:
        history = hist if isinstance(hist, list) else hist.get("history", [])
        history = sorted(history, key=lambda x: x.get("date", ""))
        if len(history) >= 2:
            first = safe_float(history[0].get("close", 0))
            last  = safe_float(history[-1].get("close", 0))
            if first > 0:
                tasi_20d = (last - first) / first * 100
    print(f"  TASI اليوم: {change_pct:+.2f}% | 20 يوم: {tasi_20d:+.2f}%")
    return change_pct, tasi_20d


def fetch_all_stocks():
    """
    ✅ إصلاح: يجلب فقط من gainers وvolume — بدون جلب 200 سهم فردي
    طلبان فقط بدل 200+
    """
    seen = {}

    for endpoint, key in [
        ("/market/gainers/", "gainers"),
        ("/market/volume/",  "stocks"),
        ("/market/movers/",  "movers"),
    ]:
        data = get(endpoint, {"limit": 100, "index": "TASI"})
        if data:
            items = data if isinstance(data, list) else data.get(key, data.get("data", []))
            for s in items:
                sym = str(s.get("symbol", ""))
                if sym and sym not in seen:
                    seen[sym] = s

    print(f"  gainers+volume+movers: {len(seen)} سهم (3 طلبات فقط) ✅")
    return list(seen.values())


def analyze_sector_rotation(all_stocks):
    sector_scores = {}
    sector_counts = {}

    for stock in all_stocks:
        sym    = str(stock.get("symbol", ""))
        chg    = safe_float(stock.get("change_percent") or stock.get("change_pct", 0))
        volume = safe_float(stock.get("volume", 0))
        sector = get_sector(sym)

        if sector not in sector_scores:
            sector_scores[sector] = 0.0
            sector_counts[sector] = 0
        sector_scores[sector] += chg * (1 + min(volume / 1_000_000, 3))
        sector_counts[sector] += 1

    ranked = sorted(
        [(name, score / max(sector_counts.get(name, 1), 1))
         for name, score in sector_scores.items()],
        key=lambda x: x[1],
        reverse=True
    )

    print("\n  Sector Rotation:")
    for name, score in ranked[:5]:
        sign = "+" if score > 0 else ""
        print(f"    {name:<16} {sign}{score:.1f}%")

    return {
        "top_sectors":    [r[0] for r in ranked[:3]],
        "bottom_sectors": [r[0] for r in ranked[-2:]] if len(ranked) > 2 else [],
        "sector_scores":  {name: round(score, 2) for name, score in ranked},
    }


def calc_rs_score(stock, tasi_20d):
    change_pct = safe_float(stock.get("change_percent") or stock.get("change_pct", 0))
    rs_vs_tasi = change_pct - tasi_20d
    return round(change_pct, 2), round(rs_vs_tasi, 2)


def get_rs_rank(all_rs_scores, stock_rs):
    if not all_rs_scores:
        return 50
    below = sum(1 for s in all_rs_scores if s < stock_rs)
    rank  = int((below / len(all_rs_scores)) * 99) + 1
    return min(rank, 99)


def calc_canslim_score(stock, rs_rank, rs_vs_tasi, top_sectors):
    sym       = str(stock.get("symbol", ""))
    sector    = get_sector(sym)
    chg       = safe_float(stock.get("change_percent") or stock.get("change_pct", 0))
    volume    = safe_float(stock.get("volume", 0))
    avg_vol   = safe_float(stock.get("avg_volume", 1))
    vol_ratio = volume / avg_vol if avg_vol > 0 else 0

    score   = 0
    reasons = []

    if chg >= 2 and vol_ratio >= 2:
        score += 20; reasons.append(f"C: زخم {chg:.1f}% + حجم {vol_ratio:.1f}x")
    elif chg >= 1:
        score += 10; reasons.append(f"C: تغير {chg:.1f}%")

    if rs_rank >= 80:
        score += 20; reasons.append(f"L: RS Rank {rs_rank} قائد")
    elif rs_rank >= 60:
        score += 10; reasons.append(f"L: RS Rank {rs_rank}")
    elif rs_rank < 40:
        score -= 15

    if sector in top_sectors:
        score += 15; reasons.append(f"I: قطاع {sector} متصدر")

    if rs_vs_tasi >= 3:
        score += 10; reasons.append(f"M: +{rs_vs_tasi:.1f}% فوق TASI")
    elif rs_vs_tasi >= 0:
        score += 5
    else:
        score -= 10

    if vol_ratio >= 2:
        score += 15; reasons.append(f"S: حجم {vol_ratio:.1f}x")
    elif vol_ratio >= 1.5:
        score += 8

    return score, reasons


def run():
    print("\n" + "="*60)
    print("Market Intelligence — تاسي")
    print("="*60)

    if not API_KEY:
        print("API_KEY missing")
        return {}

    # ✅ تحقق من الكاش أولاً
    fresh, cached_data = is_cache_fresh()
    if fresh:
        return cached_data

    tasi_today, tasi_20d = get_tasi_performance()
    all_stocks = fetch_all_stocks()

    if not all_stocks:
        print("لا توجد بيانات")
        return {}

    rotation    = analyze_sector_rotation(all_stocks)
    top_sectors = rotation["top_sectors"]

    all_rs          = []
    stock_data_list = []

    for stock in all_stocks:
        sym   = str(stock.get("symbol", ""))
        price = safe_float(stock.get("price") or stock.get("close"))
        if price <= 0:
            continue
        rs_comp, rs_vs = calc_rs_score(stock, tasi_20d)
        all_rs.append(rs_comp)
        stock_data_list.append({
            "stock":   stock,
            "rs_comp": rs_comp,
            "rs_vs":   rs_vs,
            "symbol":  sym,
        })

    results = []
    for item in stock_data_list:
        rs_rank = get_rs_rank(all_rs, item["rs_comp"])
        cs_score, cs_reasons = calc_canslim_score(
            item["stock"], rs_rank, item["rs_vs"], top_sectors
        )
        sym    = item["symbol"]
        stock  = item["stock"]
        sector = get_sector(sym)

        results.append({
            "symbol":     sym,
            "name":       stock.get("name") or stock.get("name_ar") or sym,
            "price":      safe_float(stock.get("price") or stock.get("close")),
            "change_pct": safe_float(stock.get("change_percent") or stock.get("change_pct", 0)),
            "volume":     safe_float(stock.get("volume", 0)),
            "avg_volume": safe_float(stock.get("avg_volume", 0)),
            "rs_rank":    rs_rank,
            "rs_comp":    item["rs_comp"],
            "rs_vs_tasi": item["rs_vs"],
            "canslim":    cs_score,
            "reasons":    cs_reasons,
            "sector":     sector,
        })

    results.sort(key=lambda x: x["canslim"], reverse=True)

    print(f"\n  {'السهم':<20} {'RS':>5} {'Rank':>5} {'CANSLIM':>8} {'القطاع'}")
    print(f"  {'='*58}")
    for r in results[:10]:
        print(f"  {r['name'][:20]:<20} {r['rs_comp']:>+5.1f} "
              f"{r['rs_rank']:>5} {r['canslim']:>8} {r['sector']}")

    output = {
        "generated_at":  datetime.now().strftime("%Y-%m-%d %H:%M"),
        "tasi_today":    tasi_today,
        "tasi_20d":      tasi_20d,
        "total_stocks":  len(results),
        "top_sectors":   top_sectors,
        "sector_scores": rotation["sector_scores"],
        "top_stocks":    results,
    }

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n  تم تحليل {len(results)} سهم | طلبات API: 3 فقط ✅")
    if results:
        print(f"  افضل سهم: {results[0]['name']} ({results[0]['symbol']})")
        print(f"  RS Rank: {results[0]['rs_rank']} | CAN SLIM: {results[0]['canslim']}")

    return output


if __name__ == "__main__":
    run()

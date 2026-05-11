"""
market_intelligence.py
=======================
نظام تحليل متقدم يضيف لـ fetch_api_data.py:

1. Relative Strength (RS) — هل السهم أقوى من TASI؟
2. Sector Rotation    — أي قطاع يتصدر السوق؟
3. RS Rank            — ترتيب السهم بين كل الأسهم (0-99)
4. CAN SLIM Score     — تقييم مستوحى من منهجية O'Neil

يُكتب في data/market_intel.json ويُستخدم في fetch_api_data.py
"""

import os, json, requests
from datetime import datetime, timezone, timedelta

API_KEY  = os.environ.get("API_KEY")
API_URL  = os.environ.get("API_URL", "https://app.sahmk.sa/api/v1")
HEADERS  = {"X-API-Key": API_KEY} if API_KEY else {}
OUTPUT   = "data/market_intel.json"

# ═══ القطاعات السعودية ════════════════════════════════════
SECTORS = {
    "البنوك":         ["1010","1020","1030","1050","1060","1080","1120","1150"],
    "البتروكيماويات": ["2010","2020","2060","2090","2100","2150","2160","2170"],
    "الاتصالات":      ["7010","7020","7030","7040","7203","7204"],
    "الطاقة":         ["2222","5110"],
    "التجزئة":        ["4190","4200","4210","4220","4230","4240","4250"],
    "العقار":         ["4020","4031","4040","4050","4100","4150","4300","4320"],
    "الصحة":          ["2150","4002","4005","4007","4009","4013","4017"],
    "الصناعة":        ["1211","2030","2080","2082","2110","2120","2130"],
    "التأمين":        ["8010","8020","8030","8040","8050","8060","8070"],
    "الاستثمار":      ["1111","4280","4290","4310","4321","4349"],
}


def safe_float(v, default=0.0):
    try:
        return float(v)
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
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"  error {endpoint}: {e}")
    return None


# ═══ 1. جلب مؤشر TASI ════════════════════════════════════

def get_tasi_performance():
    """
    أداء TASI في آخر 20 يوم
    للمقارنة مع أداء الأسهم الفردية
    """
    data = get("/market/summary/", {"index": "TASI"})
    if not data:
        return 0.0, 0.0

    change_pct   = safe_float(data.get("index_change_percent", 0))
    index_value  = safe_float(data.get("index_value", 0))

    # جلب التاريخي للمؤشر إذا متوفر
    hist = get("/market/historical/TASI/", {"period": 20})
    tasi_20d_return = 0.0

    if hist:
        history = hist if isinstance(hist, list) else hist.get("history", [])
        history = sorted(history, key=lambda x: x.get("date",""))
        if len(history) >= 2:
            first = safe_float(history[0].get("close", 0))
            last  = safe_float(history[-1].get("close", 0))
            if first > 0:
                tasi_20d_return = (last - first) / first * 100

    print(f"  TASI اليوم: {change_pct:+.2f}% | 20 يوم: {tasi_20d_return:+.2f}%")
    return change_pct, tasi_20d_return


# ═══ 2. Relative Strength ════════════════════════════════

def calc_rs_score(stock_hist, tasi_20d_return):
    """
    RS = أداء السهم 20 يوم - أداء TASI 20 يوم
    RS > 0  → السهم أقوى من السوق ✅
    RS < 0  → السهم أضعف من السوق ❌

    RS Composite (مثل IBD):
    - 40% وزن آخر 3 أشهر
    - 20% وزن آخر شهر
    - 20% وزن آخر أسبوعين
    - 20% وزن آخر أسبوع
    """
    if not stock_hist or len(stock_hist) < 5:
        return 0.0, 0.0

    closes = stock_hist
    price  = closes[-1]

    def ret(n):
        if len(closes) < n + 1:
            return 0.0
        p = closes[-(n+1)]
        return (price - p) / p * 100 if p > 0 else 0.0

    r_week  = ret(5)
    r_2week = ret(10)
    r_month = ret(20)
    r_3m    = ret(min(60, len(closes)-1))

    # RS Composite مرجح
    rs_composite = (r_3m * 0.4) + (r_month * 0.2) + (r_2week * 0.2) + (r_week * 0.2)
    rs_vs_tasi   = r_month - tasi_20d_return

    return round(rs_composite, 2), round(rs_vs_tasi, 2)


def get_rs_rank(all_rs_scores, stock_rs):
    """
    RS Rank: ترتيب السهم من 1 إلى 99
    99 = أقوى 1% في السوق
    80+ = منطقة CAN SLIM المطلوبة
    """
    if not all_rs_scores:
        return 50
    below = sum(1 for s in all_rs_scores if s < stock_rs)
    rank  = int((below / len(all_rs_scores)) * 99) + 1
    return min(rank, 99)


# ═══ 3. Sector Rotation ══════════════════════════════════

def analyze_sector_rotation(gainers, volume_leaders):
    """
    يحدد القطاعات الأقوى أداءً اليوم
    ويحسب نقاط الزخم لكل قطاع

    المبدأ: الدخول في أسهم القطاعات الصاعدة
    يزيد احتمال النجاح بشكل كبير
    """
    sector_scores = {}
    sector_counts = {}

    all_stocks = gainers + volume_leaders
    seen = set()
    unique_stocks = []
    for s in all_stocks:
        sym = str(s.get("symbol",""))
        if sym and sym not in seen:
            seen.add(sym)
            unique_stocks.append(s)

    for stock in unique_stocks:
        sym        = str(stock.get("symbol",""))
        chg        = safe_float(stock.get("change_percent", 0))
        volume     = safe_float(stock.get("volume", 0))

        for sector_name, symbols in SECTORS.items():
            if sym in symbols:
                if sector_name not in sector_scores:
                    sector_scores[sector_name] = 0.0
                    sector_counts[sector_name] = 0
                sector_scores[sector_name] += chg * (1 + min(volume/1_000_000, 3))
                sector_counts[sector_name] += 1
                break

    # ترتيب القطاعات
    ranked = sorted(
        [(name, score/max(sector_counts.get(name,1),1))
         for name, score in sector_scores.items()],
        key=lambda x: x[1],
        reverse=True
    )

    print("\n  📊 Sector Rotation اليوم:")
    for name, score in ranked[:5]:
        bar = "█" * min(int(abs(score)*2), 20)
        sign = "+" if score > 0 else ""
        print(f"    {name:<16} {sign}{score:.1f}% {bar}")

    return {
        "top_sectors":    [r[0] for r in ranked[:3]],
        "bottom_sectors": [r[0] for r in ranked[-2:]] if len(ranked) > 2 else [],
        "sector_scores":  {name: round(score,2) for name, score in ranked},
    }


def get_stock_sector(symbol):
    for sector_name, symbols in SECTORS.items():
        if symbol in symbols:
            return sector_name
    return "أخرى"


# ═══ 4. CAN SLIM Score ═══════════════════════════════════

def calc_canslim_score(stock, rs_composite, rs_rank, rs_vs_tasi,
                       top_sectors, hist_closes):
    """
    CAN SLIM مبسّط — منهجية William O'Neil
    C - Current Earnings  (نستخدم volume spike كبديل)
    A - Annual Earnings   (نستخدم RS طويل المدى)
    N - New High / Product (نستخدم قرب المقاومة)
    S - Supply/Demand     (حجم التداول)
    L - Leader or Laggard (RS Rank >= 80)
    I - Institutional     (Smart Money)
    M - Market Direction  (TASI اتجاه)
    """
    score   = 0
    reasons = []

    price      = safe_float(stock.get("price"))
    change_pct = safe_float(stock.get("change_percent", 0))
    volume     = safe_float(stock.get("volume", 0))
    avg_vol    = safe_float(stock.get("avg_volume", 1))
    symbol     = str(stock.get("symbol",""))
    sector     = get_stock_sector(symbol)

    vol_ratio = volume / avg_vol if avg_vol > 0 else 0

    # C — زخم قوي (نستخدم change + volume)
    if change_pct >= 2 and vol_ratio >= 2:
        score += 20
        reasons.append(f"C: زخم قوي {change_pct:.1f}% مع حجم {vol_ratio:.1f}x")
    elif change_pct >= 1:
        score += 10
        reasons.append(f"C: تغير إيجابي {change_pct:.1f}%")

    # A — RS طويل المدى إيجابي
    if rs_composite >= 10:
        score += 15
        reasons.append(f"A: RS مركّب قوي {rs_composite:.1f}")
    elif rs_composite >= 0:
        score += 8
        reasons.append(f"A: RS مركّب إيجابي {rs_composite:.1f}")

    # N — السهم يتجه لقمم جديدة
    if hist_closes and len(hist_closes) >= 10:
        high_20 = max(hist_closes[-20:]) if len(hist_closes) >= 20 else max(hist_closes)
        if price >= high_20 * 0.97:
            score += 20
            reasons.append("N: السهم قرب قمم 20 يوم")
        elif price >= high_20 * 0.90:
            score += 10
            reasons.append("N: السهم في منطقة قوة")

    # S — سيولة عالية
    if vol_ratio >= 3:
        score += 15
        reasons.append(f"S: سيولة استثنائية {vol_ratio:.1f}x")
    elif vol_ratio >= 1.8:
        score += 8
        reasons.append(f"S: سيولة جيدة {vol_ratio:.1f}x")

    # L — Leader: RS Rank >= 80
    if rs_rank >= 80:
        score += 20
        reasons.append(f"L: قائد السوق RS={rs_rank}")
    elif rs_rank >= 60:
        score += 10
        reasons.append(f"L: أداء فوق المتوسط RS={rs_rank}")
    elif rs_rank < 40:
        score -= 15
        reasons.append(f"L: أداء ضعيف RS={rs_rank} ⚠️")

    # I — في قطاع صاعد (Sector Rotation)
    if sector in top_sectors:
        score += 15
        reasons.append(f"I: قطاع {sector} متصدر اليوم ✅")
    else:
        score -= 5
        reasons.append(f"I: قطاع {sector} ليس متصدراً")

    # M — السهم أقوى من السوق
    if rs_vs_tasi >= 3:
        score += 10
        reasons.append(f"M: يتفوق على TASI بـ {rs_vs_tasi:.1f}%")
    elif rs_vs_tasi >= 0:
        score += 5
        reasons.append(f"M: يضاهي TASI")
    else:
        score -= 10
        reasons.append(f"M: أضعف من TASI بـ {abs(rs_vs_tasi):.1f}% ⚠️")

    return score, reasons


# ═══ Main ════════════════════════════════════════════════

def run():
    print("\n" + "═"*60)
    print("🧠 Market Intelligence — CAN SLIM + Sector Rotation")
    print("═"*60)

    if not API_KEY:
        print("⚠️  API_KEY مفقود")
        return {}

    # TASI أداء
    tasi_today, tasi_20d = get_tasi_performance()

    # جلب الأسهم
    gainers = []
    volume  = []
    data_g  = get("/market/gainers/", {"limit": 30, "index": "TASI"})
    data_v  = get("/market/volume/",  {"limit": 30, "index": "TASI"})

    if data_g:
        gainers = data_g if isinstance(data_g, list) else data_g.get("gainers", data_g.get("data",[]))
    if data_v:
        volume  = data_v if isinstance(data_v, list) else data_v.get("stocks",  data_v.get("data",[]))

    # Sector Rotation
    rotation = analyze_sector_rotation(gainers, volume)
    top_sectors = rotation["top_sectors"]

    # تحليل كل سهم
    print(f"\n  🔍 تحليل CAN SLIM لأفضل {min(20,len(gainers))} سهم...")

    all_rs    = []
    candidates= []

    seen = set()
    all_stocks = []
    for s in gainers + volume:
        sym = str(s.get("symbol",""))
        if sym and sym not in seen:
            seen.add(sym)
            all_stocks.append(s)

    # جلب التاريخي لكل سهم
    for stock in all_stocks[:20]:
        sym = str(stock.get("symbol",""))
        hist = get(f"/historical/{sym}/", {"period": 20})
        closes = []

        if hist:
            history = hist if isinstance(hist, list) else hist.get("history",[])
            history = sorted(history, key=lambda x: x.get("date",""))
            closes  = [safe_float(d.get("close") or d.get("price")) for d in history if d.get("close") or d.get("price")]

        rs_comp, rs_vs = calc_rs_score(closes, tasi_20d)
        all_rs.append(rs_comp)

        candidates.append({
            "stock":   stock,
            "closes":  closes,
            "rs_comp": rs_comp,
            "rs_vs":   rs_vs,
        })

    # حساب RS Rank لكل سهم
    results = []
    for c in candidates:
        rs_rank = get_rs_rank(all_rs, c["rs_comp"])

        avg_vol = safe_float(c["stock"].get("avg_volume",0))
        if avg_vol == 0:
            vol = safe_float(c["stock"].get("volume",0))
            c["stock"]["avg_volume"] = vol * 0.7

        cs_score, cs_reasons = calc_canslim_score(
            c["stock"], c["rs_comp"], rs_rank,
            c["rs_vs"], top_sectors, c["closes"]
        )

        results.append({
            "symbol":     str(c["stock"].get("symbol","")),
            "name":       c["stock"].get("name",""),
            "price":      safe_float(c["stock"].get("price",0)),
            "change_pct": safe_float(c["stock"].get("change_percent",0)),
            "rs_rank":    rs_rank,
            "rs_comp":    c["rs_comp"],
            "rs_vs_tasi": c["rs_vs"],
            "canslim":    cs_score,
            "reasons":    cs_reasons,
            "sector":     get_stock_sector(str(c["stock"].get("symbol",""))),
            "stock_obj":  c["stock"],
            "closes":     c["closes"],
        })

    # ترتيب بـ CAN SLIM Score
    results.sort(key=lambda x: x["canslim"], reverse=True)

    print(f"\n  {'═'*58}")
    print(f"  {'السهم':<20} {'RS':>5} {'Rank':>6} {'CAN SLIM':>9} {'القطاع'}")
    print(f"  {'═'*58}")
    for r in results[:8]:
        print(f"  {r['name'][:20]:<20} {r['rs_comp']:>+5.1f} "
              f"{r['rs_rank']:>6} {r['canslim']:>9} {r['sector']}")

    # حفظ النتائج
    output = {
        "generated_at":   datetime.now(timezone(timedelta(hours=3))).strftime("%Y-%m-%d %H:%M"),
        "tasi_today":     tasi_today,
        "tasi_20d":       tasi_20d,
        "top_sectors":    top_sectors,
        "sector_scores":  rotation["sector_scores"],
        "top_stocks":     [
            {
                "symbol":     r["symbol"],
                "name":       r["name"],
                "price":      r["price"],
                "rs_rank":    r["rs_rank"],
                "rs_comp":    r["rs_comp"],
                "rs_vs_tasi": r["rs_vs_tasi"],
                "canslim":    r["canslim"],
                "sector":     r["sector"],
                "reasons":    r["reasons"],
            }
            for r in results[:10]
        ],
    }

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n  ✅ تم حفظ التحليل في {OUTPUT}")
    print(f"  🏆 أفضل سهم: {results[0]['name']} ({results[0]['symbol']})")
    print(f"     CAN SLIM: {results[0]['canslim']} | RS Rank: {results[0]['rs_rank']}")
    print(f"     القطاع: {results[0]['sector']} | RS vs TASI: {results[0]['rs_vs_tasi']:+.1f}%")

    return output


if __name__ == "__main__":
    run()

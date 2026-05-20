"""
fetch_api_data.py — TASI AI مضارب
جلب بيانات السوق السعودي وتحليلها تلقائياً
الإصدار 3.0 — مع error handling شامل + fallback مضمون
"""

import os
import sys
import json
import re
import time
import requests
from datetime import datetime, timezone, timedelta

# ═══════════════════════════════════════════════════════════════
# الإعدادات
# ═══════════════════════════════════════════════════════════════

API_KEY           = os.environ.get("API_KEY")
API_URL           = os.environ.get("API_URL", "https://app.sahmk.sa/api/v1")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

INTEL_FILE  = "data/market_intel.json"
OUTPUT_FILE = "data/daily.json"
HEADERS     = {"X-API-Key": API_KEY} if API_KEY else {}

# قائمة طوارئ — تُستخدم عند فشل gainers/volume
EMERGENCY_WATCHLIST = [
    "2222","7010","1120","1080","1060","4190",
    "9516","2230","7020","2020","1010","4002",
    "2010","6010","2050","5110","9526","9527",
]

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


# ═══════════════════════════════════════════════════════════════
# دوال مساعدة
# ═══════════════════════════════════════════════════════════════

def safe_float(value, default=0.0):
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def get_sector(symbol):
    for name, symbols in SECTORS.items():
        if str(symbol) in symbols:
            return name
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
    is_open = weekday in [6,0,1,2,3] and 600 <= t <= 900
    print(f"  Market open: {is_open}")
    return is_open


def get(endpoint, params=None, retries=2, timeout=15):
    """GET مع إعادة المحاولة عند الفشل"""
    for attempt in range(retries + 1):
        try:
            r = requests.get(
                f"{API_URL}{endpoint}",
                headers=HEADERS,
                params=params or {},
                timeout=timeout,
            )
            if r.status_code == 200:
                return r.json()
            print(f"  HTTP {r.status_code} {endpoint}")
        except requests.exceptions.Timeout:
            print(f"  Timeout {endpoint} (attempt {attempt+1})")
        except requests.exceptions.ConnectionError:
            print(f"  Connection error {endpoint} (attempt {attempt+1})")
        except Exception as e:
            print(f"  Error {endpoint}: {type(e).__name__}: {e}")
        if attempt < retries:
            time.sleep(1)
    return None


# ═══════════════════════════════════════════════════════════════
# تحميل الأسهم — ثلاث طبقات
# ═══════════════════════════════════════════════════════════════

def load_all_stocks_from_intel():
    """الطبقة الأولى: من market_intel.json (كاش 20 دقيقة)"""
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
            if price <= 0: continue
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
        print("  market_intel.json غير موجود")
        return [], []
    except Exception as e:
        print(f"  market_intel.json error: {type(e).__name__}: {e}")
        return [], []


def fallback_from_api():
    """الطبقة الثانية: gainers + volume + movers من API"""
    print("\n  Fallback: جلب من API مباشرة...")
    seen = {}
    for endpoint, key in [
        ("/market/gainers/", "gainers"),
        ("/market/volume/",  "stocks"),
        ("/market/movers/",  "movers"),
    ]:
        try:
            data = get(endpoint, {"limit": 50, "index": "TASI"}, retries=2)
            if data:
                items = data if isinstance(data, list) else data.get(key, data.get("data", []))
                for s in items:
                    sym = str(s.get("symbol", ""))
                    if sym and sym not in seen:
                        seen[sym] = s
        except Exception as e:
            print(f"  {endpoint} error: {e}")
    stocks = []
    for sym, s in seen.items():
        price = safe_float(s.get("price") or s.get("close"))
        if price <= 0: continue
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
            "rs_rank":        0, "rs_vs_tasi": 0,
            "sector":         get_sector(sym),
        })
    print(f"  API fallback: {len(stocks)} سهم")
    return stocks, []


def emergency_watchlist_fetch():
    """
    الطبقة الثالثة: أسعار حية لأسهم رئيسية بـ /quote/
    بيانات حية — لا قديمة مُثبَّتة
    """
    print("\n  ⚠️ Emergency: جلب أسهم رئيسية بـ /quote/ مباشرة...")
    stocks = []
    for sym in EMERGENCY_WATCHLIST:
        try:
            data = get(f"/quote/{sym}/", retries=1, timeout=8)
            if not data: continue
            s = data if isinstance(data, dict) else (data[0] if isinstance(data, list) and data else None)
            if not s: continue
            price = safe_float(s.get("price") or s.get("close"))
            if price <= 0: continue
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
                "rs_rank":        0, "rs_vs_tasi": 0,
                "sector":         get_sector(sym),
            })
        except Exception as e:
            print(f"    {sym}: {e}")
    print(f"  Emergency watchlist: {len(stocks)} سهم ✅")
    return stocks, []


# ═══════════════════════════════════════════════════════════════
# تحديث البيانات الحية والتحليل العميق
# ═══════════════════════════════════════════════════════════════

def enrich_top10_with_live_data(ranked):
    print(f"\n  تحديث أفضل 10 ببيانات حية...")
    updated = 0
    for r in ranked[:10]:
        stock = r["stock"]
        sym   = stock.get("symbol", "")
        if not sym: continue
        try:
            data = get(f"/quote/{sym}/", retries=1, timeout=8)
            if not data: continue
            s = data if isinstance(data, dict) else (data[0] if isinstance(data, list) and data else None)
            if not s: continue
            price = safe_float(s.get("price") or s.get("close"))
            if price <= 0: continue
            stock["price"]          = price
            stock["high"]           = safe_float(s.get("high"),   price * 1.01)
            stock["low"]            = safe_float(s.get("low"),    price * 0.99)
            stock["volume"]         = safe_float(s.get("volume"),  stock["volume"])
            stock["avg_volume"]     = safe_float(s.get("avg_volume"), stock["volume"] * 0.7)
            stock["change_percent"] = safe_float(s.get("change_percent") or s.get("change_pct"))
            stock["resistance"]     = safe_float(s.get("resistance"), stock["high"])
            stock["support"]        = safe_float(s.get("support"),    stock["low"])
            stock["rsi"]            = safe_float(s.get("rsi"), stock["rsi"])
            updated += 1
        except Exception as e:
            print(f"  quote/{sym} error: {e}")
    print(f"  تم تحديث {updated} سهم ✅")
    return ranked


def _ema(closes, p):
    if len(closes) < p: return closes[-1] if closes else 0
    k = 2/(p+1); e = sum(closes[:p])/p
    for c in closes[p:]: e = c*k + e*(1-k)
    return round(e, 6)

def _obv(closes, vols):
    o = [0.0]
    for i in range(1, len(closes)):
        if closes[i] > closes[i-1]:   o.append(o[-1] + vols[i])
        elif closes[i] < closes[i-1]: o.append(o[-1] - vols[i])
        else:                          o.append(o[-1])
    return o

def _calc_obv_score(closes, vols):
    if len(closes) < 10: return 0, "بيانات غير كافية"
    obv = _obv(closes, vols); lb = min(10, len(closes)-1)
    pc  = (closes[-1]-closes[-lb])/closes[-lb]*100 if closes[-lb] else 0
    oc  = (obv[-1]-obv[-lb])/(abs(obv[-lb])+1)*100 if obv[-lb] else 0
    if pc < -1 and oc > 5:   return 15, f"Divergence ايجابي: سعر {pc:.1f}% OBV +{oc:.1f}% — تراكم خفي"
    elif pc > 1 and oc > 5:  return 10, f"تأكيد صعود: OBV +{oc:.1f}%"
    elif pc > 1 and oc < -5: return -5, f"تحذير ضعف خفي: OBV {oc:.1f}%"
    else:                     return  3, f"OBV محايد"

def _calc_macd_score(closes):
    if len(closes) < 26: return 0, "بيانات غير كافية"
    ef = _ema(closes,12); es = _ema(closes,26); macd = ef-es
    ms = [_ema(closes[:i],12)-_ema(closes[:i],26) for i in range(26,len(closes)+1)]
    sig = _ema(ms,9) if len(ms)>=9 else macd; hist = macd-sig
    cross = False
    if len(closes) >= 29:
        m3  = _ema(closes[:-3],12)-_ema(closes[:-3],26)
        ms3 = [_ema(closes[:-3][:i],12)-_ema(closes[:-3][:i],26) for i in range(26,len(closes)-2)]
        s3  = _ema(ms3,9) if len(ms3)>=9 else m3
        cross = m3 < s3 and macd > sig
    if cross:                   return 15, f"تقاطع صعودي حديث MACD {macd:.3f}"
    elif macd>sig and hist>0:   return 12, f"MACD صاعد + Histogram يتوسع"
    elif macd>sig:              return  8, f"MACD فوق Signal"
    elif hist > -0.01:          return  3, f"MACD يقترب من التقاطع"
    else:                       return  0, f"MACD تحت Signal"

def _calc_week52_score(closes, highs, price):
    lookback = min(252, len(highs))
    high_52w = max(highs[-lookback:]) if lookback > 0 and highs else price
    if high_52w <= 0: return 0, 0, "لا بيانات"
    pct = price / high_52w * 100
    if pct >= 97:   pts = 20; d = f"اختراق قمة 52 أسبوع ({pct:.1f}%)"
    elif pct >= 90: pts = 14; d = f"قريب من قمة 52 أسبوع ({pct:.1f}%)"
    elif pct >= 80: pts =  8; d = f"ضمن نطاق 52 أسبوع ({pct:.1f}%)"
    elif pct >= 60: pts =  3; d = f"بعيد عن القمة ({pct:.1f}%)"
    else:           pts = -5; d = f"في القاع ({pct:.1f}%)"
    return pts, round(pct, 1), d

def fetch_historical_for_daily(symbol, period=60):
    try:
        r = requests.get(f"{API_URL}/historical/{symbol}/",
                         headers=HEADERS, params={"period": period}, timeout=15)
        if r.status_code != 200: return None
        history = r.json().get("data", [])
        if len(history) < 15: return None
        history = sorted(history, key=lambda x: x.get("date",""))
        return {
            "closes":  [safe_float(d.get("close"))  for d in history],
            "highs":   [safe_float(d.get("high"))   for d in history],
            "lows":    [safe_float(d.get("low"))     for d in history],
            "volumes": [safe_float(d.get("volume"))  for d in history],
        }
    except Exception as e:
        print(f"  historical/{symbol} error: {e}")
        return None

def acceleration_score(closes, volumes):
    if len(closes) < 10 or len(volumes) < 10: return 0
    price_accel = (closes[-1]-closes[-6])/closes[-6]*100 if closes[-6] else 0
    price_prev  = (closes[-6]-closes[-11])/closes[-11]*100 if len(closes)>=11 and closes[-11] else 0
    vol_accel   = sum(volumes[-5:])/(sum(volumes[-10:-5]) or 1)
    score = 0
    if price_accel > price_prev: score += 20
    if vol_accel > 1.5:          score += 20
    if price_accel > 3:          score += 10
    return min(score, 50)

def enrich_top10_with_historical(ranked):
    print(f"\n  تحليل عميق (OBV + MACD + 52W) لأفضل {min(10,len(ranked))} أسهم...")
    enriched = 0
    for r in ranked[:10]:
        stock = r["stock"]
        sym   = str(stock.get("symbol",""))
        price = safe_float(stock.get("price"))
        if price <= 0 or not sym: continue
        try:
            hist = fetch_historical_for_daily(sym, period=60)
            if not hist: continue
            closes = hist["closes"]; highs = hist["highs"]; volumes = hist["volumes"]
            obv_pts,  obv_detail  = _calc_obv_score(closes, volumes)
            macd_pts, macd_detail = _calc_macd_score(closes)
            w52_pts,  w52_pct, w52_detail = _calc_week52_score(closes, highs, price)
            if len(volumes) >= 20:
                avg20 = sum(volumes[-20:])/20
                if avg20 > 0:
                    stock["avg_volume"] = avg20
                    r["volume_ratio"] = round(safe_float(stock.get("volume"))/avg20, 2)
            accel = acceleration_score(closes, volumes)
            stock["obv_score"] = obv_pts;  stock["obv_detail"] = obv_detail
            stock["macd_score"]= macd_pts; stock["macd_detail"]= macd_detail
            stock["week52_pct"]= w52_pct;  stock["week52_detail"]= w52_detail
            stock["week52_pts"]= w52_pts;  stock["acceleration"]  = accel
            bonus      = obv_pts + macd_pts + w52_pts
            r["score"] = max(0, min(r.get("score",0)+bonus, 100))
            icon = "↑" if bonus>0 else ("↓" if bonus<0 else "→")
            print(f"    {stock.get('name','')[:18]:<18} OBV:{obv_pts:>3} MACD:{macd_pts:>3} "
                  f"52W:{w52_pts:>3} Accel:{accel:>3} {icon}{bonus:+d} → {r['score']}")
            enriched += 1
        except Exception as e:
            print(f"  enrich {sym} error: {e}")
    ranked.sort(key=lambda x: x["score"], reverse=True)
    print(f"  تم تحليل {enriched} سهم بعمق ✅")
    return ranked


def get_ml_score(symbol):
    try:
        from ml_trainer import predict, fetch_historical as ml_fetch
        hist = ml_fetch(symbol, period=20)
        if hist: return predict(symbol, hist)
    except Exception: pass
    return 50.0


def get_fundamental_score(symbol, sector):
    try:
        from fundamentals_fetcher import get_fundamental_data
        score, detail, _ = get_fundamental_data(str(symbol), sector)
        return score, detail
    except Exception:
        return 0, ""


# ═══════════════════════════════════════════════════════════════
# التحليل والتقييم
# ═══════════════════════════════════════════════════════════════

def calc_targets(price, high, low, resistance, support, change_pct):
    atr = max(high-low, price*0.01)
    entry = round(resistance*1.005 if resistance>price*1.002 else price*1.005, 2)
    t1    = round(entry*1.05, 2)
    t2    = round(entry*1.10, 2)
    sl    = round(max(max(support*0.995, entry-atr*2), entry*0.96), 2)
    if sl >= entry: sl = round(entry*0.97, 2)
    risk  = entry - sl
    rr    = round((t2-entry)/risk, 2) if risk > 0 else 0
    return entry, t1, t2, sl, rr


def build_signal_reason(reasons, resistance, vol_ratio, rsi, rs_rank,
                         sector, news_reason="", news_sentiment="neutral"):
    parts = []
    if any("اختراق" in r or "قريب" in r for r in reasons): parts.append(f"اختراق {resistance:.2f}")
    if vol_ratio >= 2:     parts.append(f"سيولة {vol_ratio:.1f}x فوق المتوسط")
    elif vol_ratio >= 1.5: parts.append(f"سيولة {vol_ratio:.1f}x")
    if 50 <= rsi <= 65:    parts.append(f"RSI {rsi:.0f} في المنطقة الذهبية")
    elif 40 <= rsi < 50:   parts.append(f"RSI {rsi:.0f} بداية زخم")
    if rs_rank >= 80:      parts.append(f"RS Rank {rs_rank} قائد السوق")
    if sector and sector != "اخرى": parts.append(f"قطاع {sector} صاعد")
    if news_sentiment == "positive" and news_reason: parts.append(f"اخبار ايجابية: {news_reason}")
    elif news_sentiment == "negative" and news_reason: parts.append(f"تحذير: {news_reason}")
    if not parts: parts = reasons[:2]
    return " + ".join(parts[:4])


def calculate_score(stock, top_sectors=None, news_delta=0):
    price      = safe_float(stock.get("price"))
    high       = safe_float(stock.get("high"), price)
    low        = safe_float(stock.get("low"),  price)
    resistance = safe_float(stock.get("resistance"), high)
    support    = safe_float(stock.get("support"),    low)
    volume     = safe_float(stock.get("volume"))
    avg_volume = max(safe_float(stock.get("avg_volume")), 1)
    change_pct = safe_float(stock.get("change_percent"))
    rsi        = safe_float(stock.get("rsi"), 50)
    rs_rank    = safe_float(stock.get("rs_rank", 0))
    rs_vs_tasi = safe_float(stock.get("rs_vs_tasi", 0))
    sector     = stock.get("sector", "")
    score, reasons = 0, []

    if change_pct < -1: return -999, ["تغير سلبي مستبعد"], 0, 0

    if resistance > 0:
        dist = (resistance-price)/price
        if price >= resistance:    score += 30; reasons.append("اختراق مقاومة")
        elif dist <= 0.015:        score += 22; reasons.append(f"قريب من الاختراق ({resistance:.2f})")
        elif dist <= 0.03:         score += 12; reasons.append(f"قريب من مقاومة ({resistance:.2f})")

    if avg_volume <= 1 and volume > 0: avg_volume = volume*0.5; vsrc = "estimated"
    else: vsrc = "api"
    volume_ratio = volume/avg_volume if avg_volume > 0 else 0

    if vsrc == "estimated":
        if volume_ratio >= 2: score += 10; reasons.append(f"حجم {volume_ratio:.1f}x (مقدَّر)")
        elif volume_ratio >= 1: score += 5; reasons.append(f"حجم {volume_ratio:.1f}x (مقدَّر)")
    else:
        if   volume_ratio >= 3:   score += 25; reasons.append(f"سيولة استثنائية {volume_ratio:.1f}x")
        elif volume_ratio >= 2:   score += 20; reasons.append(f"سيولة عالية {volume_ratio:.1f}x")
        elif volume_ratio >= 1.5: score += 10; reasons.append(f"سيولة جيدة {volume_ratio:.1f}x")

    if   50<=rsi<=65:  score+=20; reasons.append(f"RSI {rsi:.0f} في المنطقة الذهبية")
    elif 40<=rsi<50:   score+=12; reasons.append(f"RSI {rsi:.0f} بداية زخم")
    elif 65<rsi<=72:   score+= 8; reasons.append(f"RSI {rsi:.0f} قوي")
    elif rsi>75:       score-=15; reasons.append(f"RSI {rsi:.0f} تشبع شرائي")

    daily_range = high-low; close_pos = ((price-low)/daily_range) if daily_range>0 else 0.5
    if   close_pos >= 0.85: score+=20; reasons.append("اغلاق عند القمة")
    elif close_pos >= 0.70: score+=12; reasons.append("تمركز ايجابي")

    if   change_pct >= 3:   score+=15; reasons.append(f"ارتفاع قوي {change_pct:.1f}%")
    elif change_pct >= 1.5: score+=10; reasons.append(f"ارتفاع {change_pct:.1f}%")

    _, _, _, _, rr = calc_targets(price, high, low, resistance, support, change_pct)
    if   rr >= 2.5: score+=15; reasons.append(f"R:R {rr:.1f} ممتاز")
    elif rr >= 2.0: score+=10; reasons.append(f"R:R {rr:.1f} جيد")
    elif rr >= 1.5: score+= 5; reasons.append(f"R:R {rr:.1f} مقبول")
    elif rr < 1:   score-=10; reasons.append(f"R:R {rr:.1f} ضعيف")

    if   rs_rank>=80: score+=15; reasons.append(f"RS Rank {rs_rank:.0f} قائد السوق")
    elif rs_rank>=60: score+= 8; reasons.append(f"RS Rank {rs_rank:.0f} فوق المتوسط")
    elif 0<rs_rank<40: score-=10; reasons.append(f"RS Rank {rs_rank:.0f} ضعيف")

    if   rs_vs_tasi>=3:  score+= 8; reasons.append(f"يتفوق على TASI بـ {rs_vs_tasi:.1f}%")
    elif rs_vs_tasi>=0:  score+= 4
    elif rs_vs_tasi<-3:  score-= 8

    if top_sectors and sector in top_sectors:
        score+=10; reasons.append(f"قطاع {sector} متصدر اليوم")

    try:
        fund_pts, fund_detail = get_fundamental_score(stock.get("symbol",""), sector)
        score += fund_pts
        if fund_pts>=8:   reasons.append(fund_detail)
        elif fund_pts<=-3: reasons.append(f"أساسيات ضعيفة: {fund_detail}")
    except Exception: pass

    try:
        ml = get_ml_score(str(stock.get("symbol","")))
        score += int((ml-50)*0.3)
        if ml>=70: reasons.append(f"ML {ml:.0f}% احتمال نجاح")
        elif ml<=30: reasons.append(f"ML {ml:.0f}% احتمال ضعيف")
    except Exception: pass

    score += news_delta
    return min(score,100), reasons, rr, volume_ratio


def build_daily_json(stock, score, reasons, rr, volume_ratio, news_analysis=None):
    price      = safe_float(stock.get("price"))
    high       = safe_float(stock.get("high"), price)
    low        = safe_float(stock.get("low"),  price)
    resistance = safe_float(stock.get("resistance"), high)
    support    = safe_float(stock.get("support"),    low)
    change_pct = safe_float(stock.get("change_percent"))
    rsi        = safe_float(stock.get("rsi"), 50)
    rs_rank    = stock.get("rs_rank", 0)
    sector     = stock.get("sector", "")
    accel      = stock.get("acceleration", 0)

    entry, target1, target2, stop_loss, rr_calc = calc_targets(
        price, high, low, resistance, support, change_pct)

    news_sentiment = news_analysis.get("sentiment","neutral") if news_analysis else "neutral"
    news_reason    = news_analysis.get("reason","")           if news_analysis else ""
    news_summary   = news_analysis.get("summary","")          if news_analysis else ""

    signal_reason = build_signal_reason(
        reasons, resistance, volume_ratio, rsi,
        rs_rank, sector, news_reason, news_sentiment)

    obv_pts  = stock.get("obv_score", 0)
    macd_pts = stock.get("macd_score", 0)
    w52_pts  = stock.get("week52_pts", 0)
    extra    = []
    if obv_pts  >= 10: extra.append(stock.get("obv_detail", ""))
    if macd_pts >= 12: extra.append(stock.get("macd_detail", ""))
    if w52_pts  >= 14: extra.append(stock.get("week52_detail", ""))
    if extra: signal_reason = signal_reason + " + " + " + ".join(extra[:2])

    return {
        "brand":          "مضارب", "mode": "morning",
        "stock_name":     stock.get("name", ""),
        "symbol":         str(stock.get("symbol", "")),
        "price":          f"{price:.2f}",
        "entry":          f"{entry:.2f}",
        "target1":        f"{target1:.2f}",
        "target2":        f"{target2:.2f}",
        "stop_loss":      f"{stop_loss:.2f}",
        "momentum":       score_label(score),
        "score":          score,
        "rsi":            round(rsi,1),
        "rr":             round(rr_calc,2),
        "volume_ratio":   round(volume_ratio,2),
        "rs_rank":        rs_rank,
        "rs_vs_tasi":     stock.get("rs_vs_tasi", 0),
        "sector":         sector,
        "signal_reason":  signal_reason,
        "news_sentiment": news_sentiment,
        "news_summary":   news_summary,
        "obv_score":      obv_pts,
        "macd_score":     macd_pts,
        "week52_pct":     stock.get("week52_pct", 0),
        "acceleration":   accel,
        "source":         "sahmk_api" if API_KEY and len(reasons)>0 else "market_snapshot",
        "generated_at":   datetime.now().strftime("%Y-%m-%d %H:%M"),
        "target2_pct":    10.0,
        "expected_days":  7,
        "max_days":       10,
        "note":           f"قراءة فنية تعليمية: {signal_reason}. هدف 10% خلال 7-10 أيام.",
    }


# ═══════════════════════════════════════════════════════════════
# Claude Review
# ═══════════════════════════════════════════════════════════════

def claude_review(candidates, top_sectors):
    if not candidates: return None, {}
    if not ANTHROPIC_API_KEY:
        print("  ANTHROPIC_API_KEY missing — skipping")
        return candidates[0], {}

    summaries = []
    for i, c in enumerate(candidates[:3], 1):
        s    = c["stock"]; news = c.get("news", {})
        summaries.append(
            f"{i}. {s.get('name','')} ({s.get('symbol','')})\n"
            f"   Score: {c['score']} | RS Rank: {s.get('rs_rank',0)}\n"
            f"   RSI: {s.get('rsi',50):.0f} | Volume: {c['volume_ratio']:.1f}x\n"
            f"   OBV: {s.get('obv_score','─')} | MACD: {s.get('macd_score','─')} | 52W: {s.get('week52_pct',0):.1f}%\n"
            f"   Acceleration: {s.get('acceleration',0)} | القطاع: {s.get('sector','')}\n"
            f"   الأسباب: {' + '.join(c['reasons'][:4])}\n"
            f"   R:R: {c['rr']} (T2=10%) | أخبار: {news.get('sentiment','neutral')}\n"
            f"   {news.get('summary','لا يوجد')}"
        )

    prompt = f"""
انت محلل مضاربة محترف في تاسي. لديك صلاحية كاملة في قبول أو رفض النشر.
الهدف: إشارات تصل +10% خلال 7-10 أيام.
القطاعات المتصدرة: {', '.join(top_sectors) if top_sectors else 'غير محدد'}

{chr(10).join(summaries)}

أجب بـ JSON فقط:
{{"selected_index":1أو2أو3أو0,"decision":"publish"أو"reject","symbol":"","reason":"","confidence":"عالية"أو"متوسطة"أو"منخفضة","warning":"","note":""}}
ارفض إذا: Score<70 | RSI>75 | R:R<1.5 | OBV سلبي
"""

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"Content-Type":"application/json","anthropic-version":"2023-06-01","x-api-key":ANTHROPIC_API_KEY},
            json={"model":"claude-sonnet-4-20250514","max_tokens":500,"messages":[{"role":"user","content":prompt}]},
            timeout=30,
        )
        if resp.status_code == 200:
            content = resp.json()["content"][0]["text"].strip()
            match   = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                result   = json.loads(match.group())
                decision = result.get("decision","publish")
                idx      = int(result.get("selected_index",1))
                print(f"\n  Claude: {decision.upper()} | {result.get('reason','')} | ثقة: {result.get('confidence','')}")
                if result.get("warning"): print(f"  تحذير: {result.get('warning')}")
                if decision=="reject" or idx==0:
                    print("  Claude رفض — لا توجد فرصة جيدة")
                    return None, result
                return candidates[max(0,min(idx-1,len(candidates)-1))], result
        print(f"  Claude status: {resp.status_code}")
    except Exception as e:
        print(f"  Claude error: {type(e).__name__}: {e}")

    return candidates[0], {}


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════

def main():
    print("="*65)
    print("📊 TASI AI مضارب — Fetch & Analyze Market Data v3.0")
    print("="*65)

    if not is_market_open():
        print("السوق مغلق الآن — لا يتم النشر")
        sys.exit(0)

    # ── خطوة 1: market_intelligence ──
    top_sectors = []
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from market_intelligence import run as run_intel
        intel       = run_intel() or {}
        top_sectors = intel.get("top_sectors", [])
        count       = len(intel.get("top_stocks", []))
        print(f"\n Market Intelligence: {count} سهم | Sectors: {', '.join(top_sectors)}")
    except Exception as e:
        print(f"\n Market Intelligence error: {type(e).__name__}: {e}")
        try:
            with open(INTEL_FILE,"r",encoding="utf-8") as f:
                cache       = json.load(f)
                top_sectors = cache.get("top_sectors",[])
                print(f"  كاش: {', '.join(top_sectors)}")
        except Exception: pass

    # ── خطوة 2: تحميل الأسهم (3 طبقات) ──
    print("\n" + "-"*65)
    stocks, intel_sectors = load_all_stocks_from_intel()
    if intel_sectors: top_sectors = intel_sectors

    if len(stocks) < 5:
        print("  ⚠️ عدد قليل — محاولة gainers/volume...")
        stocks, _ = fallback_from_api()

    if not stocks:
        print("  ⚠️ API فارغ — emergency watchlist...")
        stocks, _ = emergency_watchlist_fetch()

    if not stocks:
        print("\n  ❌ فشلت جميع مصادر البيانات — لا يتم النشر")
        sys.exit(1)

    # ── خطوة 3: التقييم ──
    print("\n" + "-"*65)
    ranked = []
    for stock in stocks:
        if safe_float(stock.get("price")) <= 0: continue
        score, reasons, rr, vol_ratio = calculate_score(stock, top_sectors, 0)
        if score > 0:
            ranked.append({"score":score,"stock":stock,"reasons":reasons,"rr":rr,"volume_ratio":vol_ratio})

    if not ranked:
        for stock in stocks:
            score, reasons, rr, vol_ratio = calculate_score(stock, top_sectors, 0)
            ranked.append({"score":score,"stock":stock,"reasons":reasons,"rr":rr,"volume_ratio":vol_ratio})

    if not ranked:
        print("  ❌ لا أسهم بعد التقييم")
        sys.exit(1)

    ranked.sort(key=lambda x: x["score"], reverse=True)
    ranked = enrich_top10_with_live_data(ranked)
    ranked = enrich_top10_with_historical(ranked)

    print(f"\n{'='*65}\n🏆 Top 5 TASI:")
    for i,r in enumerate(ranked[:5],1):
        s = r["stock"]
        print(f"  {i}. {s.get('name','')[:16]:<16} ({s.get('symbol'):>4}) "
              f"Score:{r['score']:>4} OBV:{s.get('obv_score','─'):>3} "
              f"MACD:{s.get('macd_score','─'):>3} Accel:{s.get('acceleration',0):>3}")

    # ── خطوة 4: أخبار ──
    print(f"\n{'='*65}\n📰 الأخبار...")
    try:
        from news_analyzer import get_news_analysis
    except ImportError:
        def get_news_analysis(sym, name):
            return {"sentiment":"neutral","score_delta":0,"reason":"","summary":""}

    final_candidates = []
    for r in ranked[:3]:
        s = r["stock"]; sym = str(s.get("symbol","")); name = s.get("name","")
        try:
            news = get_news_analysis(sym, name)
        except Exception:
            news = {"sentiment":"neutral","score_delta":0,"reason":"","summary":""}
        delta     = news.get("score_delta",0)
        new_score = min(r["score"]+delta, 100)
        final_candidates.append({"score":new_score,"stock":s,"reasons":r["reasons"],
                                  "rr":r["rr"],"volume_ratio":r["volume_ratio"],"news":news})
        print(f"  {name[:20]:<20} {r['score']} -> {new_score} (أخبار: {delta:+d})")

    final_candidates.sort(key=lambda x: x["score"], reverse=True)

    # ── خطوة 5: Claude يقرر (قرار نهائي ملزم) ──
    print(f"\n{'='*65}\n🤖 Claude يقرر...")
    best, claude_result = claude_review(final_candidates, top_sectors)

    if best is None:  # Claude رفض — نحترم قراره
        reason = claude_result.get("reason","لا توجد فرصة") if claude_result else "لا توجد فرصة"
        print(f"\n  لا يتم النشر: {reason}")
        sys.exit(1)

    # ── خطوة 6: حفظ الإشارة ──
    daily_data = build_daily_json(best["stock"], best["score"],
                                  best["reasons"], best["rr"],
                                  best["volume_ratio"], best.get("news"))

    if claude_result:
        if claude_result.get("reason"):  daily_data["note"]             = f"قراءة فنية: {claude_result['reason']}."
        if claude_result.get("note"):    daily_data["claude_note"]      = claude_result["note"]
        if claude_result.get("warning"): daily_data["claude_warning"]   = claude_result["warning"]
        daily_data["claude_confidence"] = claude_result.get("confidence","متوسطة")

    try:
        with open(OUTPUT_FILE,"w",encoding="utf-8") as f:
            json.dump(daily_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"  ❌ خطأ في الحفظ: {e}"); sys.exit(1)

    print(f"\n{'='*65}")
    print(f"✅ {daily_data['stock_name']} ({daily_data['symbol']}) | Score:{daily_data['score']}")
    print(f"   Entry:{daily_data['entry']} T1:{daily_data['target1']} T2:{daily_data['target2']} SL:{daily_data['stop_loss']}")
    print(f"   R:R:{daily_data['rr']} | Accel:{daily_data.get('acceleration',0)} | {daily_data['sector']}")
    print(f"{'='*65}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted"); sys.exit(0)
    except SystemExit:
        raise
    except Exception as e:
        print(f"\n❌ Fatal: {type(e).__name__}: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)

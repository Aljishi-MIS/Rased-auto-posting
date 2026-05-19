"""
historical_analyzer.py  ─ مُحدَّث
==================================
معايير الإشارات الجديدة:
  ✅ هدف ثانٍ ≥ 10% من نقطة الدخول
  ✅ يُتوقع الوصول إليه خلال 7 أيام (أقصاه 10)
  ✅ وقف خسارة ≤ -4% (نسبة مخاطرة/مكافأة ≥ 2.5)
  ✅ إشارة ذهبية: Score ≥ 88 + شروط إضافية
"""

import os, json, csv, requests
from datetime import datetime, timedelta

API_KEY  = os.environ.get("API_KEY")
API_URL  = os.environ.get("API_URL", "https://app.sahmk.sa/api/v1")
HEADERS  = {"X-API-Key": API_KEY} if API_KEY else {}

OUTPUT_FILE = "data/daily.json"
GOLDEN_FILE = "data/golden_signal.json"

# ═══════════════════════════════════════════
# ▌ معايير الإشارة اليومية
# ═══════════════════════════════════════════
TARGET1_PCT        = 0.05   # هدف أول  +5%
TARGET2_PCT        = 0.10   # هدف ثانٍ +10%
STOP_LOSS_PCT      = 0.04   # وقف خسارة -4%
MIN_RR             = 2.5    # مكافأة/مخاطرة ≥ 2.5
MAX_DAYS_TO_TARGET = 10     # أقصى أيام للهدف الثاني
EXPECTED_DAYS      = 7      # الإطار المتوقع

MIN_SCORE          = 78
MIN_RSI            = 42
MAX_RSI            = 68
MIN_VOLUME_RATIO   = 2.0    # حجم ≥ 2× المعدل
MIN_PRICE          = 10.0
MAX_ATR_PCT        = 4.0
MIN_AVG_VOLUME_SAR = 500_000

# ═══════════════════════════════════════════
# ▌ معايير الإشارة الذهبية ⭐
# ═══════════════════════════════════════════
GOLDEN_SCORE_MIN    = 88
GOLDEN_RSI_MIN      = 45
GOLDEN_RSI_MAX      = 62
GOLDEN_VOLUME_RATIO = 2.5
GOLDEN_MIN_HISTORY  = 15
GOLDEN_MAX_ATR_PCT  = 3.0
GOLDEN_TARGET2_PCT  = 0.12  # هدف ثانٍ +12%
GOLDEN_MIN_RR       = 3.0
BB_SQUEEZE_RATIO    = 0.7
MIN_HISTORY_DAYS    = 10


def safe_float(v, default=0.0):
    try:    return float(v)
    except: return default


def get(endpoint, params=None):
    try:
        r = requests.get(f"{API_URL}{endpoint}", headers=HEADERS,
                         params=params or {}, timeout=15)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"  ❌ {endpoint}: {e}")
    return None


# ═══════════════════════════════════════════
# المؤشرات الفنية
# ═══════════════════════════════════════════
def calc_rsi(closes, period=14):
    if len(closes) < period + 1: return 50.0
    gains = losses = 0.0
    for i in range(1, period + 1):
        d = closes[-i] - closes[-i-1]
        if d > 0: gains += d
        else:     losses -= d
    avg_gain = gains / period
    avg_loss = losses / period
    if avg_loss == 0: return 100.0
    return round(100 - 100 / (1 + avg_gain / avg_loss), 2)


def calc_ema(values, period):
    if len(values) < period: return values[-1] if values else 0
    k = 2 / (period + 1)
    ema = sum(values[:period]) / period
    for v in values[period:]:
        ema = v * k + ema * (1 - k)
    return round(ema, 4)


def calc_atr(highs, lows, closes, period=14):
    if len(closes) < 2: return 0
    trs = [max(highs[i]-lows[i], abs(highs[i]-closes[i-1]),
               abs(lows[i]-closes[i-1])) for i in range(1, len(closes))]
    return sum(trs[-period:]) / min(period, len(trs))


def calc_bollinger(closes, period=20):
    if len(closes) < period: return None, None, None
    window = closes[-period:]
    mid = sum(window) / period
    std = (sum((x-mid)**2 for x in window) / period) ** 0.5
    return round(mid-2*std, 4), round(mid, 4), round(mid+2*std, 4)


def resistance_level(highs, lookback=20):
    window = highs[-lookback:] if len(highs) >= lookback else highs
    return round(max(window) * 0.995, 4)


def avg_volume(volumes, period=10):
    window = volumes[-period:] if len(volumes) >= period else volumes
    return sum(window) / len(window) if window else 0


def volume_ratio(volumes):
    avg10 = avg_volume(volumes, 10)
    return round(volumes[-1] / avg10, 2) if avg10 else 0


def obv_trend(closes, volumes):
    if len(closes) < 12: return False
    obv = 0; obvs = []
    for i in range(1, len(closes)):
        obv += volumes[i] if closes[i] > closes[i-1] else -volumes[i]
        obvs.append(obv)
    return sum(obvs[-5:]) > sum(obvs[-10:-5])


def acceleration_score(closes, volumes):
    """تسارع السعر+الحجم = مؤشر الوصول للهدف في ≤ 10 أيام"""
    if len(closes) < 10 or len(volumes) < 10: return 0
    price_accel = (closes[-1] - closes[-6]) / closes[-6] * 100
    price_prev  = (closes[-6] - closes[-11]) / closes[-11] * 100 if len(closes) >= 11 else 0
    vol_accel   = sum(volumes[-5:]) / (sum(volumes[-10:-5]) or 1)
    score = 0
    if price_accel > price_prev: score += 20
    if vol_accel > 1.5:          score += 20
    if price_accel > 3:          score += 10
    return min(score, 50)


# ═══════════════════════════════════════════
# بناء بيانات الإشارة
# ═══════════════════════════════════════════
def build_signal(stock, score, reasons, rr, vol_ratio, is_golden=False):
    entry   = round(safe_float(stock.get("price")), 2)
    t2_pct  = GOLDEN_TARGET2_PCT if is_golden else TARGET2_PCT
    t1_pct  = t2_pct / 2

    return {
        "symbol":        stock.get("symbol", ""),
        "stock_name":    stock.get("name", ""),
        "entry":         entry,
        "target1":       round(entry * (1 + t1_pct),  2),
        "target2":       round(entry * (1 + t2_pct),  2),
        "stop_loss":     round(entry * (1 - STOP_LOSS_PCT), 2),
        "target1_pct":   round(t1_pct * 100, 1),
        "target2_pct":   round(t2_pct * 100, 1),
        "stop_loss_pct": round(STOP_LOSS_PCT * 100, 1),
        "rr":            rr,
        "score":         score,
        "volume_ratio":  vol_ratio,
        "rsi":           safe_float(stock.get("rsi")),
        "sector":        stock.get("sector", ""),
        "reasons":       reasons,
        "is_golden":     is_golden,
        "expected_days": EXPECTED_DAYS,
        "max_days":      MAX_DAYS_TO_TARGET,
        "date":          datetime.now().strftime("%Y-%m-%d"),
        "time":          datetime.now().strftime("%H:%M"),
        "note": (
            f"إشارة ذهبية ⭐ — هدف {round(t2_pct*100)}% خلال {EXPECTED_DAYS}-{MAX_DAYS_TO_TARGET} يوم"
            if is_golden else
            f"هدف ثانٍ {round(t2_pct*100)}% — متوقع خلال {EXPECTED_DAYS}-{MAX_DAYS_TO_TARGET} يوم"
        ),
        "data_quality": "live",
        "source":       "sahmk_api",
    }


# ═══════════════════════════════════════════
# تقييم سهم واحد
# ═══════════════════════════════════════════
def evaluate_stock(stock):
    symbol = stock.get("symbol", "")
    price  = safe_float(stock.get("price"))
    if price < MIN_PRICE: return None

    data = get(f"/historical/{symbol}/", {"period": 25})
    if not data: return None
    history = data if isinstance(data, list) else data.get("history", [])
    if len(history) < MIN_HISTORY_DAYS: return None
    history = sorted(history, key=lambda x: x.get("date", ""))

    closes = [safe_float(d.get("close") or d.get("price")) for d in history]
    highs  = [safe_float(d.get("high"),  0) for d in history]
    lows   = [safe_float(d.get("low"),   0) for d in history]
    vols   = [safe_float(d.get("volume"),0) for d in history]

    rsi     = calc_rsi(closes)
    ema20   = calc_ema(closes, 20)
    ema50   = calc_ema(closes, 50)
    atr     = calc_atr(highs, lows, closes)
    atr_pct = atr / price * 100 if price else 999
    bb_low, bb_mid, bb_high = calc_bollinger(closes)
    res     = resistance_level(highs)
    avg_vol = avg_volume(vols)
    vol_r   = volume_ratio(vols)
    obv_bull= obv_trend(closes, vols)
    accel   = acceleration_score(closes, vols)

    if (avg_vol * price) < MIN_AVG_VOLUME_SAR: return None
    if atr_pct > MAX_ATR_PCT:                  return None
    if not (MIN_RSI <= rsi <= MAX_RSI):         return None
    if vol_r < MIN_VOLUME_RATIO:                return None

    rr = round(TARGET2_PCT / STOP_LOSS_PCT, 2)  # = 2.5

    score = 0; reasons = []

    if MIN_RSI <= rsi <= MAX_RSI:
        score += 20; reasons.append(f"RSI مثالي {rsi}")
    if price > ema20:
        score += 10; reasons.append("السعر فوق EMA20")
    if price > ema50:
        score += 10; reasons.append("السعر فوق EMA50")
    if vol_r >= MIN_VOLUME_RATIO:
        score += 20; reasons.append(f"حجم ×{vol_r} المعدل")
    if obv_bull:
        score += 10; reasons.append("OBV صاعد")

    score += accel
    if accel >= 30: reasons.append("تسارع سعر+حجم قوي")

    if bb_high and bb_low and bb_mid:
        band_width = (bb_high - bb_low) / (bb_mid or 1)
        if band_width < BB_SQUEEZE_RATIO * 0.05:
            score += 10; reasons.append("BB Squeeze — انفجار وشيك")

    dist_to_res = (res - price) / price * 100
    if 0 < dist_to_res < 3:
        score += 10; reasons.append(f"على بُعد {round(dist_to_res,1)}% من المقاومة")

    if score < MIN_SCORE: return None

    is_golden = (
        score    >= GOLDEN_SCORE_MIN             and
        GOLDEN_RSI_MIN <= rsi <= GOLDEN_RSI_MAX  and
        vol_r    >= GOLDEN_VOLUME_RATIO          and
        atr_pct  <= GOLDEN_MAX_ATR_PCT           and
        obv_bull                                 and
        accel    >= 30                           and
        len(closes) >= GOLDEN_MIN_HISTORY
    )
    if is_golden:
        rr = round(GOLDEN_TARGET2_PCT / STOP_LOSS_PCT, 2)
        if rr < GOLDEN_MIN_RR: is_golden = False

    stock["rsi"] = rsi; stock["ema20"] = ema20; stock["ema50"] = ema50
    return {"stock": stock, "score": score, "reasons": reasons,
            "rr": rr, "vol_ratio": vol_r, "is_golden": is_golden, "accel": accel}


# ═══════════════════════════════════════════
# جلب جميع أسهم تاسي
# ═══════════════════════════════════════════
def fetch_all_stocks():
    stocks = []
    for endpoint in ["/gainers/", "/volume/", "/stocks/"]:
        data = get(endpoint)
        if isinstance(data, list): stocks.extend(data)
        elif isinstance(data, dict):
            for key in ("data", "stocks", "results"):
                if key in data and isinstance(data[key], list):
                    stocks.extend(data[key]); break
    seen = set(); unique = []
    for s in stocks:
        sym = s.get("symbol", "")
        if sym and sym not in seen:
            seen.add(sym); unique.append(s)
    return unique


# ═══════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════
def main():
    print("=" * 65)
    print("  مُحلّل الإشارات — هدف ثانٍ 10%+ خلال 7-10 أيام")
    print("=" * 65)

    stocks = fetch_all_stocks()
    print(f"\n  تم جلب {len(stocks)} سهم")

    results = []; golden_list = []
    for stock in stocks:
        ev = evaluate_stock(stock)
        if ev:
            results.append(ev)
            if ev["is_golden"]: golden_list.append(ev)

    if not results:
        print("  ⚠️  لا أسهم تجتاز المعايير اليوم"); return

    results.sort(key=lambda x: (x["is_golden"], x["score"]), reverse=True)
    print(f"\n  ✅ اجتاز الفلتر : {len(results)} سهم")
    print(f"  ⭐ ذهبية        : {len(golden_list)} سهم\n")

    for i, r in enumerate(results[:10], 1):
        s = r["stock"]
        tag = "⭐ ذهبية" if r["is_golden"] else "📈 يومية"
        print(f"  {i:>2}. {s.get('name','')[:20]:<20} ({s.get('symbol'):>4})  "
              f"Score:{r['score']:>4}  RSI:{s.get('rsi',0):.0f}  "
              f"Vol:{r['vol_ratio']:.1f}x  {tag}")

    os.makedirs("data", exist_ok=True)

    best = results[0]
    sig  = build_signal(best["stock"], best["score"], best["reasons"],
                        best["rr"], best["vol_ratio"], best["is_golden"])
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(sig, f, ensure_ascii=False, indent=2)

    print(f"\n{'═'*65}")
    print(f"  ✅ {sig['stock_name']} ({sig['symbol']})")
    print(f"     دخول  : {sig['entry']} ريال")
    print(f"     هدف 1 : {sig['target1']} (+{sig['target1_pct']}%)")
    print(f"     هدف 2 : {sig['target2']} (+{sig['target2_pct']}%) ← {sig['expected_days']}-{sig['max_days']} يوم")
    print(f"     وقف   : {sig['stop_loss']} (-{sig['stop_loss_pct']}%)")
    print(f"     Score : {sig['score']}  |  R:R: {sig['rr']}")

    if golden_list:
        g   = golden_list[0]
        gsig = build_signal(g["stock"], g["score"], g["reasons"],
                            g["rr"], g["vol_ratio"], is_golden=True)
        with open(GOLDEN_FILE, "w", encoding="utf-8") as f:
            json.dump(gsig, f, ensure_ascii=False, indent=2)
        print(f"\n  ⭐ ذهبية: {gsig['stock_name']}  هدف: +{gsig['target2_pct']}%  R:R: {gsig['rr']}")
    else:
        print("\n  ℹ️  لا إشارة ذهبية اليوم")

    print(f"{'═'*65}")


if __name__ == "__main__":
    main()

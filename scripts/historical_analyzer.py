import os
import json
import requests
from datetime import datetime, timezone, timedelta

API_KEY  = os.environ.get("API_KEY")
API_URL  = os.environ.get("API_URL", "https://app.sahmk.sa/api/v1")
HEADERS  = {"X-API-Key": API_KEY} if API_KEY else {}

OUTPUT_FILE  = "data/daily.json"
GOLDEN_FILE  = "data/golden_signal.json"
INTEL_FILE   = "data/market_intel.json"

GOLDEN_SCORE_MIN = 75
MIN_HISTORY_DAYS = 10

KSA = timezone(timedelta(hours=3))

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
                      "2370","2380","2381","2382"],
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


def get_rs_rank_from_intel(symbol):
    try:
        with open(INTEL_FILE, "r", encoding="utf-8") as f:
            intel = json.load(f)
        for s in intel.get("top_stocks", []):
            if str(s.get("symbol","")) == str(symbol):
                return s.get("rs_rank", 0)
    except Exception:
        pass
    return 0


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


def fetch_historical(symbol, period=20):
    data = get(f"/historical/{symbol}/", {"period": period})
    if not data:
        return None
    history = data.get("data", [])
    if len(history) < MIN_HISTORY_DAYS:
        return None
    history = sorted(history, key=lambda x: x.get("date",""))
    return {
        "opens":   [safe_float(d.get("open"))   for d in history],
        "closes":  [safe_float(d.get("close"))  for d in history],
        "highs":   [safe_float(d.get("high"))   for d in history],
        "lows":    [safe_float(d.get("low"))    for d in history],
        "volumes": [safe_float(d.get("volume")) for d in history],
        "dates":   [d.get("date","")            for d in history],
        "count":   len(history),
    }


def fetch_candidates():
    gainers = []
    volume  = []
    data_g  = get("/market/gainers/", {"limit": 50, "index": "TASI"})
    data_v  = get("/market/volume/",  {"limit": 50, "index": "TASI"})
    if data_g:
        gainers = data_g if isinstance(data_g, list) else data_g.get("gainers", data_g.get("data",[]))
    if data_v:
        volume  = data_v if isinstance(data_v, list) else data_v.get("stocks",  data_v.get("data",[]))
    seen, stocks = set(), []
    for s in gainers + volume:
        sym = str(s.get("symbol",""))
        if sym and sym not in seen:
            seen.add(sym)
            stocks.append(s)
    return stocks


def calc_rsi(closes, period=14):
    if len(closes) < period + 1:
        return 50.0
    gains, losses = [], []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i-1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period-1) + gains[i]) / period
        avg_loss = (avg_loss * (period-1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


def calc_ema(closes, period):
    if len(closes) < period:
        return closes[-1] if closes else 0
    k   = 2 / (period + 1)
    ema = sum(closes[:period]) / period
    for price in closes[period:]:
        ema = price * k + ema * (1 - k)
    return round(ema, 4)


def calc_atr(highs, lows, closes, period=14):
    trs = []
    for i in range(1, len(closes)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i]  - closes[i-1]),
            abs(lows[i]   - closes[i-1])
        )
        trs.append(tr)
    if not trs:
        return 0
    atr = sum(trs[:period]) / min(period, len(trs))
    for tr in trs[period:]:
        atr = (atr * (period-1) + tr) / period
    return round(atr, 4)


def calc_bollinger(closes, period=20, mult=2):
    if len(closes) < period:
        period = len(closes)
    recent = closes[-period:]
    mid    = sum(recent) / period
    std    = (sum((c - mid)**2 for c in recent) / period) ** 0.5
    upper  = mid + mult * std
    lower  = mid - mult * std
    width  = (upper - lower) / mid if mid > 0 else 0
    return round(upper,4), round(mid,4), round(lower,4), round(width,4)


def find_support_resistance(highs, lows, closes, lookback=20):
    if len(highs) < 5:
        return closes[-1] * 1.03, closes[-1] * 0.97
    recent_highs = highs[-lookback:]
    recent_lows  = lows[-lookback:]
    price        = closes[-1]
    resistances  = []
    for i in range(1, len(recent_highs)-1):
        if recent_highs[i] >= recent_highs[i-1] and recent_highs[i] >= recent_highs[i+1]:
            resistances.append(recent_highs[i])
    supports = []
    for i in range(1, len(recent_lows)-1):
        if recent_lows[i] <= recent_lows[i-1] and recent_lows[i] <= recent_lows[i+1]:
            supports.append(recent_lows[i])
    above      = [r for r in resistances if r > price * 1.002]
    resistance = min(above) if above else max(recent_highs)
    below      = [s for s in supports if s < price * 0.998]
    support    = max(below) if below else min(recent_lows)
    return round(resistance, 4), round(support, 4)


def calc_volume_trend(volumes, days=5):
    if len(volumes) < days * 2:
        return 1.0, False
    recent     = volumes[-days:]
    baseline   = volumes[-(days*2):-days]
    avg_r      = sum(recent)   / len(recent)
    avg_b      = sum(baseline) / len(baseline) if baseline else 1
    ratio      = avg_r / avg_b if avg_b > 0 else 1
    is_gradual = all(recent[i] >= recent[i-1] * 0.8 for i in range(1, len(recent)))
    return round(ratio, 2), is_gradual


def calc_rsi_divergence(closes, period=14, lookback=10):
    if len(closes) < lookback + period:
        return False
    mid          = lookback // 2
    recent       = closes[-lookback:]
    price_first  = min(recent[:mid])
    price_second = min(recent[mid:])
    if price_second >= price_first:
        return False
    rsi_first  = calc_rsi(closes[:-lookback+mid])
    rsi_second = calc_rsi(closes[-period:])
    return rsi_second > rsi_first


def calc_bb_squeeze(closes, period=20):
    if len(closes) < period * 2:
        return False, 1.0
    current_widths = []
    for i in range(period, len(closes)+1):
        _, _, _, w = calc_bollinger(closes[:i], period)
        current_widths.append(w)
    if len(current_widths) < 2:
        return False, 1.0
    avg_width  = sum(current_widths) / len(current_widths)
    curr_width = current_widths[-1]
    ratio      = curr_width / avg_width if avg_width > 0 else 1
    return ratio <= 0.7, round(ratio, 3)


def calc_golden_score(stock, hist):
    closes  = hist["closes"]
    highs   = hist["highs"]
    lows    = hist["lows"]
    volumes = hist["volumes"]
    price   = safe_float(stock.get("price") or stock.get("close"))

    score   = 0
    signals = []

    rsi = calc_rsi(closes)
    if 45 <= rsi <= 65:
        score += 20; signals.append(f"RSI {rsi:.0f} في المنطقة الذهبية")
    elif 40 <= rsi < 45:
        score += 10; signals.append(f"RSI {rsi:.0f} يقترب")
    elif rsi > 75:
        score -= 20; signals.append(f"RSI {rsi:.0f} تشبع شرائي")

    ema20 = calc_ema(closes, 20)
    ema50 = calc_ema(closes, min(50, len(closes)))
    if price > ema20 > ema50:
        score += 15; signals.append("السعر فوق EMA20 و EMA50")
    elif price > ema20:
        score +=  8; signals.append("السعر فوق EMA20")
    elif price < ema20:
        score -= 10

    is_squeeze, squeeze_ratio = calc_bb_squeeze(closes)
    if is_squeeze:
        score += 20; signals.append(f"ضغط بولينجر ({squeeze_ratio:.2f}) انفجار وشيك")
    elif squeeze_ratio <= 0.85:
        score += 10; signals.append("بداية ضغط بولينجر")

    atr     = calc_atr(highs, lows, closes)
    atr_pct = (atr / price * 100) if price > 0 else 999
    if atr_pct < 2:
        score += 15; signals.append(f"تذبذب منخفض ATR {atr_pct:.1f}%")
    elif atr_pct < 3:
        score +=  8; signals.append(f"تذبذب معتدل ATR {atr_pct:.1f}%")
    elif atr_pct > 5:
        score -= 10; signals.append(f"تذبذب عالٍ ATR {atr_pct:.1f}%")

    resistance, support = find_support_resistance(highs, lows, closes)
    if resistance > 0:
        dist = (resistance - price) / price * 100
        if price >= resistance:
            score += 25; signals.append("اختراق مقاومة حقيقية")
        elif dist <= 1.5:
            score += 18; signals.append(f"على بعد {dist:.1f}% من الاختراق")
        elif dist <= 3:
            score += 10; signals.append(f"قريب من مقاومة ({dist:.1f}%)")

    vol_ratio, is_gradual = calc_volume_trend(volumes)
    if vol_ratio >= 2 and is_gradual:
        score += 20; signals.append(f"تراكم حجم تدريجي {vol_ratio:.1f}x")
    elif vol_ratio >= 1.5:
        score += 10; signals.append(f"زيادة حجم {vol_ratio:.1f}x")

    if calc_rsi_divergence(closes):
        score += 15; signals.append("Divergence ايجابي — قوة خفية")

    if closes and highs and lows:
        rng       = highs[-1] - lows[-1]
        close_pos = (closes[-1] - lows[-1]) / rng if rng > 0 else 0.5
        if close_pos >= 0.85:
            score += 10; signals.append("اغلاق عند القمة")

    score = min(score, 100)
    return score, signals, rsi, resistance, support, atr, vol_ratio


def build_signal(stock, hist, score, signals, rsi,
                 resistance, support, atr, vol_ratio):
    price  = safe_float(stock.get("price") or stock.get("close"))
    sym    = str(stock.get("symbol",""))
    name   = stock.get("name") or stock.get("name_ar") or sym
    sector = get_sector(sym)

    # RS Rank من market_intel.json
    rs_rank = get_rs_rank_from_intel(sym)

    entry = round(price * 1.001, 2)

    # الهدف الاول — اقرب مقاومة (حد اقصى 4%)
    if resistance > entry * 1.005:
        raw_t1 = resistance
    else:
        raw_t1 = entry + atr * 1.5
    t1 = round(min(raw_t1, entry * 1.04), 2)

    # الهدف الثاني — بين 5% و 8%
    raw_t2 = t1 + atr * 1.5
    t2     = round(max(entry * 1.05, min(raw_t2, entry * 1.08)), 2)

    # وقف الخسارة — حد اقصى 3%
    raw_sl    = max(support * 0.995, entry - atr * 1.5)
    stop_loss = round(max(raw_sl, entry * 0.97), 2)
    if stop_loss >= entry:
        stop_loss = round(entry * 0.97, 2)

    risk   = entry - stop_loss
    reward = t1 - entry
    rr     = round(reward / risk, 2) if risk > 0 else 0

    momentum = (
        "قوي جداً" if score >= 85 else
        "قوي"      if score >= 70 else
        "متوسط"    if score >= 55 else "ضعيف"
    )

    now = datetime.now(KSA)

    return {
        "brand":        "مضارب",
        "mode":         "golden",
        "type":         "اشارة ذهبية",
        "stock_name":   name,
        "symbol":       sym,
        "price":        f"{price:.2f}",
        "entry":        f"{entry:.2f}",
        "target1":      f"{t1:.2f}",
        "target2":      f"{t2:.2f}",
        "stop_loss":    f"{stop_loss:.2f}",
        "momentum":     momentum,
        "score":        score,
        "rsi":          round(rsi, 1),
        "rr":           rr,
        "volume_ratio": vol_ratio,
        "resistance":   round(resistance, 2),
        "support":      round(support, 2),
        "atr":          round(atr, 4),
        "rs_rank":      rs_rank,
        "sector":       sector,
        "source":       "historical_analysis",
        "generated_at": now.strftime("%Y-%m-%d %H:%M"),
        "signals":      signals,
        "note":         f"قراءة فنية تعليمية: {' + '.join(signals[:3])}.",
    }


def main():
    import sys

    print("\n" + "="*60)
    print("Historical Analyzer -- تحليل 20 يوم تاريخي")
    print("="*60)

    if not API_KEY:
        print("API_KEY missing")
        sys.exit(1)

    now = datetime.now(KSA)
    print(f"  الوقت: {now.strftime('%H:%M')} KSA")

    # تشغيل market_intelligence اولاً لتوفير RS Rank
    print("\n  تشغيل Market Intelligence...")
    try:
        import sys as _sys, os as _os
        _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
        from market_intelligence import run as run_intel
        run_intel()
        print("  Market Intelligence جاهز")
    except Exception as e:
        print(f"  Market Intelligence error: {e}")

    candidates = fetch_candidates()
    if not candidates:
        print("لا توجد اسهم مرشحة")
        sys.exit(1)

    print(f"\n  مرشحون: {len(candidates)} سهم\n")

    golden_candidates = []

    for i, stock in enumerate(candidates[:30]):
        sym   = str(stock.get("symbol",""))
        name  = (stock.get("name") or stock.get("name_ar") or sym)[:18]
        price = safe_float(stock.get("price") or stock.get("close"))

        if price < 5:
            continue

        hist = fetch_historical(sym, period=20)
        if not hist:
            print(f"  [{i+1:02d}] {name:<18} ({sym}) -- لا يوجد تاريخي")
            continue

        score, signals, rsi, resistance, support, atr, vol_ratio = \
            calc_golden_score(stock, hist)

        atr_pct = atr / price * 100 if price > 0 else 0
        status  = "🥇" if score >= GOLDEN_SCORE_MIN else "  "
        print(f"  [{i+1:02d}] {name:<18} ({sym}) "
              f"Score:{score:>4} RSI:{rsi:>5.1f} "
              f"ATR:{atr_pct:.1f}% {status}")

        if score >= GOLDEN_SCORE_MIN:
            golden_candidates.append({
                "score":      score,
                "stock":      stock,
                "hist":       hist,
                "signals":    signals,
                "rsi":        rsi,
                "resistance": resistance,
                "support":    support,
                "atr":        atr,
                "vol_ratio":  vol_ratio,
            })

    print(f"\n{'='*60}")

    if not golden_candidates:
        print("لا توجد اشارات ذهبية — تخطي")
        sys.exit(1)

    golden_candidates.sort(key=lambda x: x["score"], reverse=True)
    best   = golden_candidates[0]
    signal = build_signal(
        best["stock"], best["hist"], best["score"],
        best["signals"], best["rsi"], best["resistance"],
        best["support"], best["atr"], best["vol_ratio"]
    )

    with open(GOLDEN_FILE, "w", encoding="utf-8") as f:
        json.dump(signal, f, ensure_ascii=False, indent=2)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(signal, f, ensure_ascii=False, indent=2)

    print(f"الاشارة الذهبية:")
    print(f"  السهم   : {signal['stock_name']} ({signal['symbol']})")
    print(f"  القطاع  : {signal['sector']}")
    print(f"  RS Rank : {signal['rs_rank']}")
    print(f"  دخول    : {signal['entry']}")
    print(f"  هدف1    : {signal['target1']} ({round((float(signal['target1'])-float(signal['entry']))/float(signal['entry'])*100,1)}%)")
    print(f"  هدف2    : {signal['target2']} ({round((float(signal['target2'])-float(signal['entry']))/float(signal['entry'])*100,1)}%)")
    print(f"  وقف     : {signal['stop_loss']} ({round((float(signal['stop_loss'])-float(signal['entry']))/float(signal['entry'])*100,1)}%)")
    print(f"  R:R     : {signal['rr']} | Score: {signal['score']}")


if __name__ == "__main__":
    main()

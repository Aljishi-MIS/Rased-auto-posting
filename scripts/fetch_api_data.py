import os
import json
import re
import requests
from datetime import datetime, timezone, timedelta

API_KEY           = os.environ.get(“API_KEY”)
API_URL           = os.environ.get(“API_URL”, “https://app.sahmk.sa/api/v1”)
ANTHROPIC_API_KEY = os.environ.get(“ANTHROPIC_API_KEY”, “”)

SNAPSHOT_FILE = “data/market_snapshot.json”
INTEL_FILE    = “data/market_intel.json”
OUTPUT_FILE   = “data/daily.json”

HEADERS = {“X-API-Key”: API_KEY} if API_KEY else {}

SECTORS = {
“البنوك”:         [“1010”,“1020”,“1030”,“1050”,“1060”,“1080”,“1120”,“1150”],
“البتروكيماويات”: [“2010”,“2020”,“2060”,“2090”,“2100”,“2150”,“2160”,“2170”,
“2222”,“2223”,“2230”],
“الاتصالات”:      [“7010”,“7020”,“7030”,“7040”,“7203”,“7204”],
“الطاقة”:         [“5110”,“2040”,“2050”],
“التجزئة”:        [“4190”,“4200”,“4210”,“4220”,“4230”,“4240”,“4250”,“4261”],
“العقار”:         [“4020”,“4031”,“4040”,“4050”,“4100”,“4150”,“4300”,“4310”,
“4320”,“4321”,“4322”,“4323”,“4324”,“4325”,“4326”,“4327”,“4328”],
“الصحة”:          [“4002”,“4005”,“4007”,“4009”,“4013”,“4017”,“4019”,“4061”],
“الصناعة”:        [“1211”,“1212”,“2030”,“2080”,“2082”,“2083”,“2110”,“2120”,
“2130”,“2140”,“2180”,“2190”,“2200”,“2210”,“2220”,“2240”,
“2250”,“2290”,“2310”,“2320”,“2330”,“2340”,“2350”,“2360”,
“2370”,“2380”,“2381”,“2382”,“4030”],
“التامين”:        [“8010”,“8020”,“8030”,“8040”,“8050”,“8060”,“8070”,“8100”,
“8120”,“8150”,“8160”,“8170”,“8180”,“8190”,“8200”,“8210”,
“8230”,“8240”,“8250”,“8260”,“8270”,“8280”,“8300”,“8310”,
“8311”,“8320”,“8330”,“8340”],
“الاستثمار”:      [“1111”,“4280”,“4290”,“4291”,“4349”,“4330”,“4331”,
“4332”,“4333”,“4334”,“4335”,“4336”,“4337”,“4338”,“4339”,
“4340”,“4341”,“4342”,“4344”,“4345”,“4346”,“4347”,“4348”],
“التقنية”:        [“9516”,“9526”,“9527”,“9528”,“9529”,“9536”,“9543”,“9544”,
“9545”,“9546”,“9547”,“9548”,“9549”,“9553”,“9554”,“9555”,
“9556”,“9557”,“9558”,“9559”,“9560”,“9561”,“9562”,“9563”,
“9564”,“9565”,“9566”,“9567”,“9568”],
“الغذاء”:         [“2060”,“2070”,“6001”,“6002”,“6010”,“6013”,“6014”,“6015”,
“6020”,“6040”,“6050”,“6060”,“6070”],
“التعليم”:        [“4001”,“4003”,“4004”,“4006”,“4008”,“4010”,“4011”,“4012”,
“4014”,“4015”,“4016”,“4018”,“4021”],
“الترفيه”:        [“4110”,“4130”,“4140”,“4141”,“4142”,“4143”,“4144”,
“4160”,“4161”,“4162”,“4163”,“4164”,“4170”,“4180”],
“النقل”:          [“1301”,“1302”,“1303”,“1304”,“1320”,“1321”,“5010”,“5020”],
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
return “اخرى”

def score_label(score):
if score >= 90: return “انفجار محتمل”
if score >= 80: return “زخم قوي”
if score >= 75: return “مراقبة”
return “ضعيف”

def is_market_open():
KSA     = timezone(timedelta(hours=3))
now     = datetime.now(KSA)
weekday = now.weekday()
t       = now.hour * 60 + now.minute
print(f”  Market check: {now.strftime(’%H:%M’)} KSA | weekday={weekday} | t={t}”)
market_days  = [6, 0, 1, 2, 3]
market_open  = 10 * 60 + 0
market_close = 15 * 60 + 0
is_open = weekday in market_days and market_open <= t <= market_close
print(f”  Market open: {is_open}”)
return is_open

def get(endpoint, params=None):
try:
r = requests.get(
f”{API_URL}{endpoint}”,
headers=HEADERS,
params=params or {},
timeout=15
)
if r.status_code == 200:
return r.json()
except Exception as e:
print(f”  error {endpoint}: {e}”)
return None

def load_all_stocks_from_intel():
try:
with open(INTEL_FILE, “r”, encoding=“utf-8”) as f:
intel = json.load(f)

```
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
```

def enrich_top10_with_live_data(ranked):
print(f”\n  تحديث أفضل 10 ببيانات حية…”)
updated = 0

```
for r in ranked[:10]:
    stock = r["stock"]
    sym   = stock.get("symbol", "")
    data  = get(f"/quote/{sym}/")

    if data:
        s = data if isinstance(data, dict) else (data[0] if isinstance(data, list) and data else None)
        if s:
            price = safe_float(s.get("price") or s.get("close"))
            if price > 0:
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

print(f"  تم تحديث {updated} سهم ✅")
return ranked
```

def fallback_from_api():
print(”\n  Fallback: جلب من API مباشرة…”)
seen = {}

```
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
```

def calc_targets(price, high, low, resistance, support, change_pct):
atr = max(high - low, price * 0.01)

```
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
```

def build_signal_reason(reasons, resistance, vol_ratio, rsi, rs_rank,
sector, news_reason=””, news_sentiment=“neutral”):
parts = []

```
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
```

def get_ml_score(symbol):
“””
يستخدم نموذج ML للتنبؤ باحتمال نجاح الإشارة
“””
try:
import sys, os as _os
sys.path.insert(0, _os.path.dirname(_os.path.abspath(**file**)))
from ml_trainer import predict, fetch_historical as ml_fetch

```
    hist = ml_fetch(symbol, period=20)
    if hist:
        return predict(symbol, hist)
except Exception:
    pass
return 50.0
```

def calculate_score(stock, top_sectors=None, news_delta=0):
price          = safe_float(stock.get(“price”))
high           = safe_float(stock.get(“high”), price)
low            = safe_float(stock.get(“low”),  price)
resistance     = safe_float(stock.get(“resistance”), high)
support        = safe_float(stock.get(“support”),    low)
volume         = safe_float(stock.get(“volume”))
avg_volume     = max(safe_float(stock.get(“avg_volume”)), 1)
change_percent = safe_float(stock.get(“change_percent”))
rsi            = safe_float(stock.get(“rsi”), 50)
rs_rank        = safe_float(stock.get(“rs_rank”, 0))
rs_vs_tasi     = safe_float(stock.get(“rs_vs_tasi”, 0))
sector         = stock.get(“sector”, “”)

```
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
if   rr >= 2.5: score += 15; reasons.append(f"R:R {rr:.1f} ممتاز")
elif rr >= 1.5: score +=  8; reasons.append(f"R:R {rr:.1f} جيد")
elif rr < 1:    score -= 10; reasons.append(f"R:R {rr:.1f} ضعيف")

if rs_rank >= 80:
    score += 15; reasons.append(f"RS Rank {rs_rank:.0f} قائد السوق")
elif rs_rank >= 60:
    score +=  8; reasons.append(f"RS Rank {rs_rank:.0f} فوق المتوسط")
elif 0 < rs_rank < 40:
    score -= 10; reasons.append(f"RS Rank {rs_rank:.0f} ضعيف")

if rs_vs_tasi >= 3:
    score += 8; reasons.append(f"يتفوق على TASI بـ {rs_vs_tasi:.1f}%")
elif rs_vs_tasi >= 0:
    score += 4
elif rs_vs_tasi < -3:
    score -= 8

if top_sectors and sector in top_sectors:
    score += 10; reasons.append(f"قطاع {sector} متصدر اليوم")

# ML Score
ml_score = get_ml_score(str(stock.get("symbol", "")))
ml_delta = int((ml_score - 50) * 0.3)
score   += ml_delta
if ml_score >= 70:
    reasons.append(f"ML {ml_score:.0f}% احتمال نجاح")
elif ml_score <= 30:
    reasons.append(f"ML {ml_score:.0f}% احتمال ضعيف")

score += news_delta
score  = min(score, 100)
return score, reasons, rr, volume_ratio
```

def build_daily_json(stock, score, reasons, rr, volume_ratio, news_analysis=None):
price      = safe_float(stock.get(“price”))
high       = safe_float(stock.get(“high”), price)
low        = safe_float(stock.get(“low”),  price)
resistance = safe_float(stock.get(“resistance”), high)
support    = safe_float(stock.get(“support”),    low)
change_pct = safe_float(stock.get(“change_percent”))
rsi        = safe_float(stock.get(“rsi”), 50)
rs_rank    = stock.get(“rs_rank”, 0)
sector     = stock.get(“sector”, “”)

```
entry, target1, target2, stop_loss, rr_calc = calc_targets(
    price, high, low, resistance, support, change_pct)

news_sentiment = news_analysis.get("sentiment", "neutral") if news_analysis else "neutral"
news_reason    = news_analysis.get("reason",    "")        if news_analysis else ""
news_summary   = news_analysis.get("summary",   "")        if news_analysis else ""

signal_reason = build_signal_reason(
    reasons, resistance, volume_ratio, rsi,
    rs_rank, sector, news_reason, news_sentiment
)

momentum = score_label(score)
from_api = bool(API_KEY) and len(reasons) > 0

return {
    "brand":          "مضارب",
    "mode":           "morning",
    "stock_name":     stock.get("name", ""),
    "symbol":         str(stock.get("symbol", "")),
    "price":          f"{price:.2f}",
    "entry":          f"{entry:.2f}",
    "target1":        f"{target1:.2f}",
    "target2":        f"{target2:.2f}",
    "stop_loss":      f"{stop_loss:.2f}",
    "momentum":       momentum,
    "score":          score,
    "rsi":            round(rsi, 1),
    "rr":             round(rr_calc, 2),
    "volume_ratio":   round(volume_ratio, 2),
    "rs_rank":        rs_rank,
    "rs_vs_tasi":     stock.get("rs_vs_tasi", 0),
    "sector":         sector,
    "signal_reason":  signal_reason,
    "news_sentiment": news_sentiment,
    "news_summary":   news_summary,
    "source":         "sahmk_api" if from_api else "market_snapshot",
    "generated_at":   datetime.now().strftime("%Y-%m-%d %H:%M"),
    "note":           f"قراءة فنية تعليمية: {signal_reason}.",
}
```

def claude_review(candidates, top_sectors):
if not candidates:
return None, {}
if len(candidates) == 1:
return candidates[0], {}
if not ANTHROPIC_API_KEY:
print(”  ANTHROPIC_API_KEY missing - skipping Claude review”)
return candidates[0], {}

```
summaries = []
for i, c in enumerate(candidates[:3], 1):
    s = c["stock"]
    summaries.append(
        f"{i}. {s.get('name','')} ({s.get('symbol','')})\n"
        f"   Score: {c['score']} | RS Rank: {s.get('rs_rank',0)}\n"
        f"   RSI: {s.get('rsi',50):.0f} | Volume: {c['volume_ratio']:.1f}x\n"
        f"   القطاع: {s.get('sector','')}\n"
        f"   الاسباب: {' + '.join(c['reasons'][:3])}\n"
        f"   R:R: {c['rr']}"
    )

prompt = f"""
```

انت محلل مضاربة محترف متخصص في سوق الاسهم السعودي تاسي.

القطاعات المتصدرة اليوم: {’, ’.join(top_sectors)}

هذه افضل 3 اسهم وجدها النظام:

{chr(10).join(summaries)}

مهمتك:

1. اختر السهم الافضل للمضاربة اليوم
1. اشرح لماذا بجملة واحدة احترافية بالعربي
1. حدد مستوى الثقة
1. نبه اذا كان هناك مخاطر

اجب بـ JSON فقط:
{{
“selected_index”: 1 او 2 او 3,
“symbol”: “رمز السهم”,
“reason”: “جملة واحدة سبب الاختيار بالعربي”,
“confidence”: “عالية” او “متوسطة” او “منخفضة”,
“warning”: “تحذير ان وجد او اتركه فارغ”,
“note”: “ملاحظة تحليلية قصيرة للمشتركين”
}}
“””

```
try:
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "Content-Type":      "application/json",
            "anthropic-version": "2023-06-01",
            "x-api-key":         ANTHROPIC_API_KEY,
        },
        json={
            "model":      "claude-sonnet-4-20250514",
            "max_tokens": 400,
            "messages":   [{"role": "user", "content": prompt}]
        },
        timeout=30
    )

    if response.status_code == 200:
        data    = response.json()
        content = data["content"][0]["text"].strip()
        match   = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            result = json.loads(match.group())
            idx    = int(result.get("selected_index", 1)) - 1
            idx    = max(0, min(idx, len(candidates)-1))
            print(f"\n  Claude اختار : {result.get('symbol','')}")
            print(f"  السبب         : {result.get('reason','')}")
            print(f"  الثقة         : {result.get('confidence','')}")
            if result.get("warning"):
                print(f"  تحذير         : {result.get('warning','')}")
            return candidates[idx], result
    else:
        print(f"  Claude API status: {response.status_code}")

except Exception as e:
    print(f"  Claude review error: {e}")

return candidates[0], {}
```

def main():
import sys

```
if not is_market_open():
    print("السوق مغلق الان - لا يتم النشر")
    sys.exit(1)

# الخطوة 1 — market_intelligence يحلل 220+ سهم
top_sectors = []
try:
    import os as _os
    sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
    from market_intelligence import run as run_intel
    intel       = run_intel() or {}
    top_sectors = intel.get("top_sectors", [])
    count       = len(intel.get("top_stocks", []))
    print(f"\n Market Intelligence: {count} سهم | Sectors: {', '.join(top_sectors)}")
except Exception as e:
    print(f"\n Market Intelligence error: {e}")

# الخطوة 2 — قراءة جميع الأسهم من market_intel.json
stocks, intel_sectors = load_all_stocks_from_intel()
if intel_sectors:
    top_sectors = intel_sectors

if len(stocks) < 5:
    stocks, _ = fallback_from_api()

if not stocks:
    raise RuntimeError("no stocks found")

# الخطوة 3 — تقييم جميع الأسهم
ranked = []
for stock in stocks:
    if safe_float(stock.get("price")) <= 0:
        continue
    score, reasons, rr, vol_ratio = calculate_score(stock, top_sectors, 0)
    if score > 0:
        ranked.append({
            "score":        score,
            "stock":        stock,
            "reasons":      reasons,
            "rr":           rr,
            "volume_ratio": vol_ratio,
        })

if not ranked:
    for stock in stocks:
        score, reasons, rr, vol_ratio = calculate_score(stock, top_sectors, 0)
        ranked.append({
            "score":        score,
            "stock":        stock,
            "reasons":      reasons,
            "rr":           rr,
            "volume_ratio": vol_ratio,
        })

if not ranked:
    raise RuntimeError("no stocks after scoring")

ranked.sort(key=lambda x: x["score"], reverse=True)

# الخطوة 4 — تحديث أفضل 10 ببيانات حية
ranked = enrich_top10_with_live_data(ranked)

print(f"\n{'='*60}")
print("Top 5 TASI:")
for i, r in enumerate(ranked[:5], 1):
    s = r["stock"]
    print(f"  {i}. {s.get('name','')[:20]:<20} ({s.get('symbol'):>4}) "
          f"Score:{r['score']:>4} RS:{s.get('rs_rank',0):>3} "
          f"Vol:{r['volume_ratio']:.1f}x Sec:{s.get('sector','')}")

# الخطوة 5 — أخبار + Claude
print(f"\n{'='*60}")
print("اخبار + Claude...")

try:
    from news_analyzer import get_news_analysis
except ImportError:
    def get_news_analysis(sym, name):
        return {"sentiment": "neutral", "score_delta": 0, "reason": "", "summary": ""}

final_candidates = []
for r in ranked[:3]:
    s         = r["stock"]
    sym       = str(s.get("symbol",""))
    name      = s.get("name","")
    news      = get_news_analysis(sym, name)
    delta     = news.get("score_delta", 0)
    new_score = min(r["score"] + delta, 100)

    final_candidates.append({
        "score":        new_score,
        "stock":        s,
        "reasons":      r["reasons"],
        "rr":           r["rr"],
        "volume_ratio": r["volume_ratio"],
        "news":         news,
    })
    print(f"  {name[:20]:<20} {r['score']} -> {new_score} (اخبار: {delta:+d})")

final_candidates.sort(key=lambda x: x["score"], reverse=True)

best, claude_result = claude_review(final_candidates, top_sectors)

claude_reason  = claude_result.get("reason",    "") if claude_result else ""
claude_note    = claude_result.get("note",       "") if claude_result else ""
claude_warning = claude_result.get("warning",    "") if claude_result else ""
claude_conf    = claude_result.get("confidence", "متوسطة") if claude_result else "متوسطة"

daily_data = build_daily_json(
    best["stock"], best["score"],
    best["reasons"], best["rr"],
    best["volume_ratio"], best.get("news")
)

if claude_reason:
    daily_data["note"]           = f"قراءة فنية تعليمية: {claude_reason}."
if claude_note:
    daily_data["claude_note"]    = claude_note
if claude_warning:
    daily_data["claude_warning"] = claude_warning
daily_data["claude_confidence"]  = claude_conf

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(daily_data, f, ensure_ascii=False, indent=2)

print(f"\n{'='*60}")
print(f" Selected   : {daily_data['stock_name']} ({daily_data['symbol']})")
print(f"  Score     : {daily_data['score']} | Momentum: {daily_data['momentum']}")
print(f"  Entry     : {daily_data['entry']} | T1: {daily_data['target1']} | SL: {daily_data['stop_loss']}")
print(f"  Claude    : {claude_reason}")
print(f"  Sector    : {daily_data['sector']} | Source: {daily_data['source']}")

if daily_data.get("source") == "market_snapshot":
    print("\n  WARNING: using local snapshot")
    sys.exit(1)
```

if **name** == “**main**”:
main()
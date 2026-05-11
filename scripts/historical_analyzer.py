# “””
historical_analyzer.py

يحلل 20 يوم من البيانات التاريخية لكل سهم
ويكتشف الأسهم قبل الانفجار السعري بدقة عالية.

معايير الأسهم الأقل خطورة:

- ATR% < 3% (تذبذب يومي منخفض)
- السعر > 10 ريال (أسهم مستقرة)
- حجم تداول يومي > 500,000 ريال (سيولة كافية)
- beta منخفض (حركة هادئة)
  “””

import os
import json
import csv
import requests
from datetime import datetime, timezone, timedelta

API_KEY  = os.environ.get(“API_KEY”)
API_URL  = os.environ.get(“API_URL”, “https://app.sahmk.sa/api/v1”)
HEADERS  = {“X-API-Key”: API_KEY} if API_KEY else {}

OUTPUT_FILE  = “data/daily.json”
GOLDEN_FILE  = “data/golden_signal.json”
LOG_FILE     = “data/signals_log.csv”

# ══════════════════════════════════════════════════════════

# معايير الأمان — أسهم أقل خطورة

# ══════════════════════════════════════════════════════════

MAX_ATR_PCT      = 3.0    # أقصى تذبذب يومي 3%
MIN_PRICE        = 10.0   # أدنى سعر 10 ريال
MIN_AVG_VOLUME   = 500_000 # أدنى حجم تداول يومي
MIN_HISTORY_DAYS = 10     # أدنى أيام تاريخية للتحليل

# معايير الإشارة الذهبية

GOLDEN_SCORE_MIN    = 80
VOLUME_ACCUM_DAYS   = 5   # أيام تراكم الحجم
BB_SQUEEZE_RATIO    = 0.7 # نسبة ضغط البولينجر
RSI_GOLDEN_MIN      = 45
RSI_GOLDEN_MAX      = 65
MIN_RESISTANCE_TESTS= 2   # عدد مرات اختبار المقاومة

def safe_float(v, default=0.0):
try:
return float(v)
except Exception:
return default

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
print(f”  ❌ {endpoint}: {e}”)
return None

# ══════════════════════════════════════════════════════════

# جلب البيانات التاريخية

# ══════════════════════════════════════════════════════════

def fetch_historical(symbol, days=20):
data = get(f”/historical/{symbol}/”, {“period”: days})
if not data:
return None

```
history = data if isinstance(data, list) else data.get("history", [])
if len(history) < MIN_HISTORY_DAYS:
    return None

history = sorted(history, key=lambda x: x.get("date", ""))

return {
    "closes":  [safe_float(d.get("close") or d.get("price")) for d in history],
    "highs":   [safe_float(d.get("high"),  0) for d in history],
    "lows":    [safe_float(d.get("low"),   0) for d in history],
    "volumes": [safe_float(d.get("volume"),0) for d in history],
    "dates":   [d.get("date","") for d in history],
}
```

def fetch_candidates():
“”“يجلب الأسهم المرشحة من gainers و volume”””
gainers = get(”/market/gainers/”, {“limit”: 30, “index”: “TASI”})
volume  = get(”/market/volume/”,  {“limit”: 30, “index”: “TASI”})

```
stocks, seen = [], set()
for s in (gainers or []) + (volume or []):
    if isinstance(gainers, list):
        items = gainers
    else:
        items = (gainers or {}).get("gainers", []) + \
                (volume  or {}).get("stocks",  [])

# تجميع كل الأسهم
all_items = []
if gainers:
    all_items += gainers if isinstance(gainers, list) else gainers.get("gainers", gainers.get("data", []))
if volume:
    all_items += volume  if isinstance(volume,  list) else volume.get("stocks",  volume.get("data",  []))

for s in all_items:
    sym = str(s.get("symbol",""))
    if sym and sym not in seen:
        seen.add(sym)
        stocks.append(s)

return stocks
```

# ══════════════════════════════════════════════════════════

# المؤشرات الفنية

# ══════════════════════════════════════════════════════════

def calc_atr(highs, lows, closes, period=14):
“”“Average True Range — مقياس التذبذب”””
trs = []
for i in range(1, len(closes)):
tr = max(
highs[i]  - lows[i],
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

def calc_bollinger(closes, period=20, std_mult=2):
“”“Bollinger Bands — للكشف عن الضغط”””
if len(closes) < period:
period = len(closes)
recent = closes[-period:]
mid    = sum(recent) / period
variance = sum((c - mid)**2 for c in recent) / period
std    = variance ** 0.5
upper  = mid + std_mult * std
lower  = mid - std_mult * std
width  = (upper - lower) / mid if mid > 0 else 0
return round(upper, 2), round(mid, 2), round(lower, 2), round(width, 4)

def calc_rsi(closes, period=14):
“”“RSI حقيقي”””
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

def calc_volume_accumulation(volumes, days=5):
“””
تراكم الحجم التدريجي:
هل الحجم يرتفع تدريجياً على مدى N أيام؟
“””
if len(volumes) < days + 1:
return 0, False

```
recent   = volumes[-days:]
baseline = volumes[-(days*2):-days]

avg_recent   = sum(recent)   / len(recent)   if recent   else 0
avg_baseline = sum(baseline) / len(baseline) if baseline else 1

accumulation_ratio = avg_recent / avg_baseline if avg_baseline > 0 else 0

# هل الحجم يرتفع تدريجياً (ليس spike واحد)؟
is_gradual = all(
    recent[i] >= recent[i-1] * 0.8
    for i in range(1, len(recent))
)

return round(accumulation_ratio, 2), is_gradual
```

def calc_resistance_tests(highs, closes, lookback=20):
“””
كم مرة اختبر السهم نفس مستوى المقاومة؟
“””
if len(highs) < 5:
return 0, 0

```
resistance = max(highs[-lookback:]) if len(highs) >= lookback else max(highs)
tolerance  = resistance * 0.02  # 2% tolerance

tests = sum(
    1 for h in highs[-lookback:]
    if abs(h - resistance) <= tolerance
)

return tests, round(resistance, 2)
```

def calc_smart_money(closes, volumes, days=10):
“””
Smart Money Detection:
أيام إغلاق قوية مع حجم مرتفع = مؤسسات تشتري
“””
if len(closes) < days + 1:
return 0

```
avg_vol = sum(volumes[-days:]) / days if volumes else 0
score   = 0

for i in range(-days, 0):
    if len(closes) + i < 1:
        continue
    daily_change = (closes[i] - closes[i-1]) / closes[i-1] * 100 if closes[i-1] > 0 else 0
    vol_ratio    = volumes[i] / avg_vol if avg_vol > 0 else 0

    # يوم إغلاق إيجابي مع حجم فوق المتوسط
    if daily_change > 0.5 and vol_ratio > 1.2:
        score += 1
    # يوم إغلاق قوي جداً مع حجم عالٍ جداً
    if daily_change > 1.5 and vol_ratio > 2:
        score += 2

return min(score, 10)
```

def calc_rsi_divergence(closes, rsi_period=14, lookback=10):
“””
Divergence إيجابي:
السعر ينخفض لكن RSI يرتفع = قوة خفية
“””
if len(closes) < lookback + rsi_period:
return False

```
# آخر نقطتين منخفضتين
recent_closes = closes[-lookback:]
mid           = len(recent_closes) // 2

price_first  = min(recent_closes[:mid])
price_second = min(recent_closes[mid:])

if price_second >= price_first:
    return False  # لا divergence — السعر يرتفع

# RSI عند نفس النقاط
rsi_first  = calc_rsi(closes[:-lookback+mid])
rsi_second = calc_rsi(closes[-rsi_period:])

return rsi_second > rsi_first  # RSI يرتفع بينما السعر ينخفض
```

# ══════════════════════════════════════════════════════════

# فلتر الأمان

# ══════════════════════════════════════════════════════════

def is_safe_stock(stock, hist):
“”“يتحقق أن السهم منخفض المخاطر”””
price      = safe_float(stock.get(“price”))
avg_volume = sum(hist[“volumes”][-10:]) / 10 if hist[“volumes”] else 0
atr        = calc_atr(hist[“highs”], hist[“lows”], hist[“closes”])
atr_pct    = (atr / price * 100) if price > 0 else 999

```
checks = {
    f"السعر > {MIN_PRICE} ريال":       price >= MIN_PRICE,
    f"ATR% < {MAX_ATR_PCT}%":          atr_pct <= MAX_ATR_PCT,
    f"حجم > {MIN_AVG_VOLUME:,}":       avg_volume >= MIN_AVG_VOLUME,
}

passed = all(checks.values())
return passed, checks, round(atr_pct, 2)
```

# ══════════════════════════════════════════════════════════

# حساب الـ Golden Score

# ══════════════════════════════════════════════════════════

def calc_golden_score(stock, hist):
closes  = hist[“closes”]
highs   = hist[“highs”]
lows    = hist[“lows”]
volumes = hist[“volumes”]
price   = safe_float(stock.get(“price”))

```
score   = 0
signals = []

# ── 1. تراكم الحجم التدريجي (وزن 25) ──────────────────
accum_ratio, is_gradual = calc_volume_accumulation(volumes, VOLUME_ACCUM_DAYS)
if accum_ratio >= 2.0 and is_gradual:
    score += 25
    signals.append(f"تراكم حجم تدريجي {accum_ratio:.1f}x ✨")
elif accum_ratio >= 1.5:
    score += 15
    signals.append(f"زيادة حجم {accum_ratio:.1f}x")
elif accum_ratio >= 1.2:
    score += 8
    signals.append(f"حجم فوق المتوسط {accum_ratio:.1f}x")

# ── 2. ضغط البولينجر باندز (وزن 20) ───────────────────
bb_upper, bb_mid, bb_lower, bb_width = calc_bollinger(closes)
# مقارنة بمتوسط العرض التاريخي
if len(closes) >= 20:
    widths = []
    for i in range(10, len(closes)):
        _, _, _, w = calc_bollinger(closes[:i])
        widths.append(w)
    avg_width = sum(widths) / len(widths) if widths else bb_width
    squeeze_ratio = bb_width / avg_width if avg_width > 0 else 1

    if squeeze_ratio <= 0.5:
        score += 20
        signals.append("ضغط بولينجر شديد 🔥 — انفجار وشيك")
    elif squeeze_ratio <= 0.7:
        score += 12
        signals.append("ضغط بولينجر — طاقة مكتنزة")
    elif squeeze_ratio <= 0.85:
        score += 6
        signals.append("بداية ضغط بولينجر")

# ── 3. اختبار المقاومة المتكرر (وزن 20) ───────────────
resistance_tests, resistance_level = calc_resistance_tests(highs, closes)
if resistance_tests >= 3:
    score += 20
    signals.append(f"اختبر المقاومة {resistance_tests} مرات 🎯")
elif resistance_tests >= 2:
    score += 12
    signals.append(f"اختبر المقاومة {resistance_tests} مرات")

# ── 4. Smart Money (وزن 20) ────────────────────────────
sm_score = calc_smart_money(closes, volumes)
if sm_score >= 6:
    score += 20
    signals.append(f"تراكم Smart Money قوي ({sm_score}/10) 💰")
elif sm_score >= 4:
    score += 12
    signals.append(f"مؤشر Smart Money ({sm_score}/10)")
elif sm_score >= 2:
    score += 6
    signals.append(f"بداية تراكم ({sm_score}/10)")

# ── 5. RSI في المنطقة الذهبية (وزن 15) ────────────────
rsi = calc_rsi(closes)
if RSI_GOLDEN_MIN <= rsi <= RSI_GOLDEN_MAX:
    score += 15
    signals.append(f"RSI {rsi:.0f} في المنطقة الذهبية ✅")
elif 40 <= rsi < RSI_GOLDEN_MIN:
    score += 8
    signals.append(f"RSI {rsi:.0f} يقترب من المنطقة الذهبية")
elif rsi > 70:
    score -= 15
    signals.append(f"RSI {rsi:.0f} تشبع شرائي ⚠️")

# ── 6. Divergence إيجابي (وزن 15) ─────────────────────
has_divergence = calc_rsi_divergence(closes)
if has_divergence:
    score += 15
    signals.append("Divergence إيجابي — قوة خفية 🔍")

# ── 7. قرب الاختراق (وزن 10) ──────────────────────────
if resistance_level > 0:
    dist_to_resistance = (resistance_level - price) / price * 100
    if 0 < dist_to_resistance <= 1:
        score += 10
        signals.append(f"على بُعد {dist_to_resistance:.1f}% من الاختراق 🚀")
    elif 1 < dist_to_resistance <= 2.5:
        score += 6
        signals.append(f"قريب من الاختراق ({dist_to_resistance:.1f}%)")

return score, signals, rsi, resistance_level, accum_ratio
```

# ══════════════════════════════════════════════════════════

# بناء الإشارة الذهبية

# ══════════════════════════════════════════════════════════

def build_golden_signal(stock, hist, score, signals, rsi, resistance, accum_ratio):
closes  = hist[“closes”]
lows    = hist[“lows”]
price   = safe_float(stock.get(“price”))

```
support    = min(lows[-10:]) if lows else price * 0.95
entry      = round(price * 1.001, 2)
target1    = round(resistance * 1.005, 2) if resistance > price else round(entry * 1.04, 2)
target2    = round(entry * 1.08, 2)
stop_loss  = round(max(support * 0.99, entry * 0.96), 2)

risk   = entry - stop_loss
reward = target1 - entry
rr     = round(reward / risk, 2) if risk > 0 else 0

KSA      = timezone(timedelta(hours=3))
now      = datetime.now(KSA)

return {
    "type":         "🥇 إشارة ذهبية",
    "brand":        "مضارب",
    "stock_name":   stock.get("name",""),
    "symbol":       str(stock.get("symbol","")),
    "price":        f"{price:.2f}",
    "entry":        f"{entry:.2f}",
    "target1":      f"{target1:.2f}",
    "target2":      f"{target2:.2f}",
    "stop_loss":    f"{stop_loss:.2f}",
    "rsi":          round(rsi, 1),
    "rr":           rr,
    "score":        score,
    "volume_accum": accum_ratio,
    "resistance":   round(resistance, 2),
    "momentum":     "ذهبي 🥇" if score >= 90 else "قوي جداً 🔥",
    "signals":      signals,
    "note":         f"إشارة ذهبية: {' + '.join(signals[:2])}",
    "generated_at": now.strftime("%Y-%m-%d %H:%M"),
    "source":       "historical_analysis_20d",
    "risk_level":   "منخفض ✅",
}
```

# ══════════════════════════════════════════════════════════

# Main

# ══════════════════════════════════════════════════════════

def main():
print(”\n” + “═”*60)
print(“🥇 محلل الإشارات الذهبية — أسهم منخفضة المخاطر”)
print(“═”*60)

```
candidates = fetch_candidates()
if not candidates:
    print("❌ لم يتم جلب أسهم مرشحة")
    return

print(f"\n📦 {len(candidates)} سهم مرشح — جارٍ التحليل التاريخي...\n")

golden_candidates = []

for i, stock in enumerate(candidates[:25]):  # أفضل 25 سهم
    sym   = str(stock.get("symbol",""))
    name  = stock.get("name","")[:18]
    price = safe_float(stock.get("price"))

    if price < MIN_PRICE:
        continue

    # جلب التاريخي
    hist = fetch_historical(sym, days=20)
    if not hist:
        print(f"  [{i+1:02d}] {name:<18} ({sym}) — ❌ لا يوجد تاريخي")
        continue

    # فلتر الأمان
    is_safe, safety_checks, atr_pct = is_safe_stock(stock, hist)
    if not is_safe:
        failed = [k for k, v in safety_checks.items() if not v]
        print(f"  [{i+1:02d}] {name:<18} ({sym}) — ⚠️ مستبعد: {', '.join(failed)}")
        continue

    # حساب الـ Golden Score
    g_score, signals, rsi, resistance, accum = calc_golden_score(stock, hist)

    status = "🥇" if g_score >= GOLDEN_SCORE_MIN else "📊"
    print(f"  [{i+1:02d}] {name:<18} ({sym}) Score:{g_score:>4} "
          f"RSI:{rsi:.0f} ATR:{atr_pct:.1f}% Vol:{accum:.1f}x {status}")

    if g_score >= GOLDEN_SCORE_MIN:
        golden_candidates.append({
            "score":      g_score,
            "stock":      stock,
            "hist":       hist,
            "signals":    signals,
            "rsi":        rsi,
            "resistance": resistance,
            "accum":      accum,
        })

print(f"\n{'═'*60}")

if not golden_candidates:
    print("⏳ لا توجد إشارات ذهبية اليوم — السوق لا يعطي فرصة مثالية")
    print("   سيعيد المحلل الفحص في الجلسة القادمة")
    return

# أفضل إشارة ذهبية
golden_candidates.sort(key=lambda x: x["score"], reverse=True)
best = golden_candidates[0]

signal = build_golden_signal(
    best["stock"], best["hist"], best["score"],
    best["signals"], best["rsi"], best["resistance"], best["accum"]
)

# حفظ الإشارة الذهبية
with open(GOLDEN_FILE, "w", encoding="utf-8") as f:
    json.dump(signal, f, ensure_ascii=False, indent=2)

# حفظ أيضاً في daily.json للنشر
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(signal, f, ensure_ascii=False, indent=2)

print(f"\n🥇 الإشارة الذهبية:")
print(f"   السهم  : {signal['stock_name']} ({signal['symbol']})")
print(f"   السعر  : {signal['price']} ريال")
print(f"   دخول   : {signal['entry']} | هدف1: {signal['target1']} | هدف2: {signal['target2']}")
print(f"   وقف    : {signal['stop_loss']} | R:R: {signal['rr']}")
print(f"   Score  : {signal['score']}/100 | RSI: {signal['rsi']}")
print(f"   المخاطر: {signal['risk_level']}")
print(f"\n   الإشارات:")
for s in signal["signals"]:
    print(f"   • {s}")
```

if **name** == “**main**”:
main()
